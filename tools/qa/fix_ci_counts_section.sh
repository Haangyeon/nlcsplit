#!/usr/bin/env bash
# 修正归档尾部那段"追加：pytest 汇总行"——上一版把它写空了。
# 空的根因就是本仓库反复踩的那一条：日志每行前面有 GitHub 的时间戳前缀，
# 而我的过滤规则里有一条 `grep -vE "^20[0-9]{2}-"`，它先把手要的三行汇总全杀了，
# 于是段落标题在、内容零行，脚本照样 exit 0。
set -u
REPO=/mnt/e/Project/GAMESS
OUT=$REPO/evidence/release_qa/20261001T150706Z_github_actions_first_runs.out
RUN=36877803728
TOK=$(tr -d '\r\n' < /mnt/e/tmp/nlcsplit_pat.tmp)
redact() { sed -E 's/ghp_[A-Za-z0-9]+/<TOKEN>/g'; }

W=$(mktemp -d)
curl -sSL --max-time 180 -H "Authorization: Bearer $TOK" \
  -o "$W/logs.zip" "https://api.github.com/repos/Haangyeon/nlcsplit/actions/runs/$RUN/logs" \
  || { echo "下载日志失败"; exit 4; }
( cd "$W" && unzip -o -q logs.zip ) || { echo "解压失败"; exit 5; }

# 截掉旧的追加段（保留主体），再写新段
marker='--- 追加：'
cutline=$(grep -n -m1 -F "$marker" "$OUT" | cut -d: -f1 || true)
if [ -n "${cutline:-}" ]; then
  head -n $((cutline - 2)) "$OUT" > "$OUT.tmp" && mv "$OUT.tmp" "$OUT"
  echo "已截掉旧追加段（从第 $cutline 行起）"
fi

{
  echo ''
  echo '--- 追加：run #5 (HEAD 0a05675) 三档 pytest 的汇总行，逐字取自 job 日志'
  echo '    为什么单列这一段：step=success 只说明没有非零退出，不说明跑了多少项。'
  echo '    "0 违规"和"0 条被解析"打印出来长得一样，所以这里要的是分母。'
  echo '    （这一段的第一版是空的：日志每行带 GitHub 时间戳前缀，而我当时的过滤里有一条'
  echo '      `grep -vE "^20.."`，正好把手要的三行全杀了——段落标题在、内容零行、脚本 exit 0。）'
  for f in "$W"/*_pytest*.txt; do
    arm=$(basename "$f" .txt | sed 's/^[0-9]_//')
    echo "  [$arm]"
    grep -E "[0-9]+ (passed|failed)" "$f" | sed -E 's/^[0-9T:.Z-]+Z //' | sed 's/^/    /'
  done
  echo '    读法：第一行是 `-m "not slow"` 快车道；第二行是全量（含 slow）；第三行是树外'
  echo '    `pytest --pyargs nlcsplit`，即从**装好的包**里跑，工作目录不是仓库。'
  echo '    两臂三档都是同一组数：48 passed + 1 skipped（全量与树外），快车道 30 passed +'
  echo '    1 skipped + 18 deselected——与 README 里"发布 wheel 收 49 项 = 31 + 18，其中那一条'
  echo '    skip 是设计内的 S22 取回项"是同一套数，这里是它在 GitHub 上的第二次独立记录。'
} >> "$OUT"

rm -rf "$W"
echo "== 归档尾部 =="
tail -14 "$OUT" | redact
echo "== MANIFEST 重算并校验 =="
( cd "$REPO/evidence/release_qa" && sha256sum -b *.out *.txt *.md > MANIFEST.sha256 \
  && sha256sum -c --strict MANIFEST.sha256 2>&1 | grep -v ": OK$" | head -3 \
  && echo "entries=$(wc -l < MANIFEST.sha256)" )
