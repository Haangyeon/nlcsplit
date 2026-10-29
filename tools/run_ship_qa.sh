#!/usr/bin/env bash
# 验收第 2 条的一条命令：从导出树出货 → 装进一次性 --target 目录 → 树外跑 pytest → 三份 QA 归档。
#
# 为什么默认**不**执行出货：`make_public_repo.js` 在交接件第 65 行"只有他能做"那一栏
# （PAT → 出货 → push_manual → 转 public）。所以这个脚本没带 `--yes` 时只打印计划并退出，
# 不碰 dist/、不触网。带了 `--yes` 表示作者已明确授权本次出货——就这一次，不扩到 push/public。
#
# 为什么值得先写出来：这三步的顺序不能错（先建 wheel 才能装、装了才能树外跑、
# 跑完才有 census/member-diff/pytest 三份档），而顺序错在本仓是有先例的代价。
#
# 2026-10-23：日志先落 /tmp，收口完冻成 evidence/release_qa/<stamp>_ship_qa_plan.out，
# 最后才重生成清单——否则这份日志自己在清单目录里、又还没登记，下一次导出的 C2 闸门必抓它。
set -u
# 2026-10-29：这里原来写死 `cd /mnt/e/Project/GAMESS`。在 WSL 里那是 E: 的挂载点，但对
# Windows 侧 Git Bash 而言 `/mnt/e` 是 Git 安装目录下的一条无关路径——脚本会安静地 cd 进一个
# 空目录、`mkdir -p evidence/release_qa` 造出假树，最后 freeze() 里的
# `bash tools/make_evidence_manifest.sh` 报"No such file"。那次运行除了打印计划什么也没做，
# 但计划里写着"清单已登记"是假的。改成按脚本自身位置定位，两种 shell 下都对。
cd "$(dirname "$0")/.." || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
QA=evidence/release_qa
mkdir -p "$QA"
FINAL="${QA}/${STAMP}_ship_qa_plan.out"
RUNNER=$(mktemp /tmp/nlcsplit_shipqa_log_XXXXXX)
TMPRC="${RUNNER}.rc"
TARGET=$(mktemp -d /tmp/nlcsplit_shipqa_XXXXXX)
PLAN_ONLY=1
[ "${1:-}" = "--yes" ] && PLAN_ONLY=0

say() { echo "$@" | tee -a "$RUNNER"; }

# 冻档：日志与 rc 一起搬进清单目录，然后**最后**重生成清单（硬规矩 2）。
# 重生成之后不再往这份日志里写任何一行，否则哈希立刻陈旧。
freeze() {
  local rc=$1
  echo "$rc" > "$TMPRC"
  mv "$RUNNER" "$FINAL"
  mv "$TMPRC" "$FINAL.rc"
  if bash tools/make_evidence_manifest.sh > /tmp/nlcsplit_shipqa_manifest.log 2>&1; then
    echo "   清单已重生成（本次日志与 rc 已登记）：$FINAL"
  else
    echo "!! 清单重生成失败，见 /tmp/nlcsplit_shipqa_manifest.log —— 这份日志可能未登记"
  fi
}

say "# 验收第 2 条：出货件 QA 流水线"
say "# 生成 $(date -u +%FT%TZ)   临时安装目录 $TARGET"
if [ "$PLAN_ONLY" = "1" ]; then
  say
  say "PLAN ONLY（未执行出货；只把这份计划日志登记进清单）—— 要真跑请显式加 --yes，且这仅代表授权**出货**这一步："
  say "  1) node tools/make_public_repo.js            # 从导出树出货；工作树直建会把 6 个 INTERNAL_ONLY 模块装进去"
  say "  2) python3 evidence/release_qa/wheel_census.py + wheel_member_diff.py   # 数成员：certificate.py 在不在、测试模块数"
  say "  3) python3 -m pip install --no-deps --target $TARGET dist/nlcsplit-*.whl"
  say "  4) cd /tmp && python3 -m pytest $TARGET/nlcsplit/tests -m 'not slow' -q   # 树外 cwd，验 import 不靠仓内文件"
  say "  5) python3 evidence/release_qa/test_count_census.py + wheel_member_diff.py 三份归档"
  say "  6) bash tools/run_w4_closeout.sh             # 正文全表收口（rc 单独记录，不否决 wheel）；清单在冻档后再生成一次"
  say "  仍然**不**做：PAT / push_manual / 转 public / ORCID / Zenodo / ScholarOne"
  say
  say "# exit=0 at $(date -u +%FT%TZ)"
  rm -rf "$TARGET"
  freeze 0
  exit 0
fi

fail() { say "!! $1"; say "# exit=1 at $(date -u +%FT%TZ)"; rm -rf "$TARGET"; freeze 1; exit 1; }

say
say "## 步 1：从导出树出货"
node tools/make_public_repo.js >> "$RUNNER" 2>&1 || fail "make_public_repo.js 非零（它自带 15 道闸门，先读它的判语再重试）"
WHL=$(ls -t dist/nlcsplit-*.whl 2>/dev/null | head -1)
[ -n "$WHL" ] || fail "出货后找不到 dist/nlcsplit-*.whl"
say "   wheel = $WHL"

say "## 步 2：成员清点（census + member-diff）"
python3 evidence/release_qa/wheel_census.py "$WHL" >> "$RUNNER" 2>&1
RC2=$?
say "   wheel_census rc=$RC2"
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

say "## 步 5：测试计数与安装后成员比对"
python3 evidence/release_qa/test_count_census.py >> "$RUNNER" 2>&1
RC5=$?
say "   test_count_census rc=$RC5"
python3 evidence/release_qa/wheel_member_diff.py >> "$RUNNER" 2>&1 || true

rm -rf "$TARGET"

if [ "$RC2" -ne 0 ] || [ "$RCP" -ne 0 ] || [ "$NTEST" != "10" ] || [ "$RC5" -ne 0 ]; then
  say "VERDICT NOTCLEAN —— wheel_census rc=$RC2，pytest rc=$RCP，装的测试模块数=$NTEST（应为 10），test_count_census rc=$RC5"
  say "# exit=1 at $(date -u +%FT%TZ)"
  freeze 1
  exit 1
fi

say "## 步 6：W4 收口（正文全表项，单独记录；清单在冻档后再生成一次）"
bash tools/run_w4_closeout.sh >> "$RUNNER" 2>&1
RC6=$?
if [ "$RC6" -eq 0 ]; then
  say "   w4_closeout rc=0"
else
  say "   w4_closeout rc=$RC6 —— 这是**正文全表**的验收项，不是 wheel 的；见 evidence/common_grid/*_w4_closeout.out"
fi

say "VERDICT DONE —— 出货件自带证书入口与 10 个测试模块，树外安装可全绿；W4 收口 rc=$RC6（正文表项另案）"
say "# exit=0 at $(date -u +%FT%TZ)"
freeze 0
exit 0
