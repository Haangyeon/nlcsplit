#!/usr/bin/env bash
# 验收第 2 条的一条命令：从导出树出货 → 装进一次性 --target 目录 → 树外跑 pytest → 三份 QA 归档。
#
# 为什么默认**不**执行出货：`make_public_repo.js` 在交接件第 65 行"只有他能做"那一栏
# （PAT → 出货 → push_manual → 转 public）。所以这个脚本没带 `--yes` 时只打印计划并退出，
# 不碰 dist/、不触网。带了 `--yes` 表示作者已明确授权本次出货——就这一次，不扩到 push/public。
#
# 为什么值得先写出来：这三步的顺序不能错（先建 wheel 才能装、装了才能树外跑、
# 跑完才有 census/member-diff/pytest 三份档），而顺序错在本仓是有先例的代价。
set -u
cd /mnt/e/Project/GAMESS || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
QA=evidence/release_qa
mkdir -p "$QA"
RUNNER="${QA}/${STAMP}_ship_qa_plan.out"
TARGET=$(mktemp -d /tmp/nlcsplit_shipqa_XXXXXX)
PLAN_ONLY=1
[ "${1:-}" = "--yes" ] && PLAN_ONLY=0

say() { echo "$@" | tee -a "$RUNNER"; }

say "# 验收第 2 条：出货件 QA 流水线"
say "# 生成 $(date -u +%FT%TZ)   临时安装目录 $TARGET"
if [ "$PLAN_ONLY" = "1" ]; then
  say
  say "PLAN ONLY（未执行任何东西）—— 要真跑请显式加 --yes，且这仅代表授权**出货**这一步："
  say "  1) node tools/make_public_repo.js            # 从导出树出货；工作树直建会把 6 个 INTERNAL_ONLY 模块装进去"
  say "  2) python3 evidence/release_qa/wheel_census.py + wheel_member_diff.py   # 数成员：certificate.py 在不在、测试模块数"
  say "  3) python3 -m pip install --no-deps --target $TARGET dist/nlcsplit-*.whl"
  say "  4) cd /tmp && python3 -m pytest $TARGET/nlcsplit/tests -m 'not slow' -q   # 树外 cwd，验 import 不靠仓内文件"
  say "  5) python3 evidence/release_qa/test_count_census.py + wheel_member_diff.py 三份归档"
  say "  6) bash tools/run_w4_closeout.sh             # 最后一步才重生成清单（顺序纪律）"
  say "  仍然**不**做：PAT / push_manual / 转 public / ORCID / Zenodo / ScholarOne"
  say
  say "# exit=0 at $(date -u +%FT%TZ)"
  echo 0 > "$RUNNER.rc"          # 与本仓归档纪律一致：有 `# exit=` 就得有同名 .rc，别只写一半
  rm -rf "$TARGET"
  exit 0
fi

fail() { say "!! $1"; echo 1 > "$RUNNER.rc"; say "# exit=1 at $(date -u +%FT%TZ)"; rm -rf "$TARGET"; exit 1; }

say
say "## 步 1：从导出树出货"
node tools/make_public_repo.js >> "$RUNNER" 2>&1 || fail "make_public_repo.js 非零（它自带 15 道闸门，先读它的判语再重试）"
WHL=$(ls -t dist/nlcsplit-*.whl 2>/dev/null | head -1)
[ -n "$WHL" ] || fail "出货后找不到 dist/nlcsplit-*.whl"
say "   wheel = $WHL"

say "## 步 2：成员清点（census + member-diff）"
python3 evidence/release_qa/wheel_census.py >> "$RUNNER" 2>&1
say "   wheel_census rc=$?"
python3 evidence/release_qa/wheel_member_diff.py >> "$RUNNER" 2>&1 || true
say "   member-diff 见上（若 VERDICT REFUSED 说明读的是工作树件，必须查）"

say "## 步 3：装进一次性 --target 目录"
python3 -m pip install --no-deps --no-index --target "$TARGET" "$WHL" >> "$RUNNER" 2>&1 \
  || fail "pip install --target 失败"
[ -f "$TARGET/nlcsplit/certificate.py" ] || fail "装的件里没有 nlcsplit/certificate.py（白名单没带上？）"
NTEST=$(find "$TARGET/nlcsplit/tests" -maxdepth 1 -name 'test_*.py' 2>/dev/null | wc -l)
say "   装的件里 test_*.py = $NTEST（预飞说 10；不一致就是名单与实装分叉了）"

say "## 步 4：树外 cwd 跑 pytest（不靠仓内文件）"
( cd /tmp && python3 -m pytest "$TARGET/nlcsplit/tests" -m "not slow" -q ) >> "$RUNNER" 2>&1
RCP=$?
say "   pytest rc=$RCP"

rm -rf "$TARGET"
say
if [ "$RCP" -eq 0 ] && [ "$NTEST" = "10" ]; then
  say "VERDICT DONE —— 出货件自带证书入口与 10 个测试模块，树外安装可全绿"
  echo 0 > "$RUNNER.rc"; say "# exit=0 at $(date -u +%FT%TZ)"
  exit 0
fi
say "VERDICT NOTCLEAN —— pytest rc=$RCP，装的测试模块数=$NTEST（应为 10）"
echo 1 > "$RUNNER.rc"; say "# exit=1 at $(date -u +%FT%TZ)"
exit 1
