#!/usr/bin/env bash
# 把 run #5 两个臂的 pytest 汇总行原样取回来，追加到归档尾部。
# 只追加，不重写已有内容；MANIFEST 之后重算。
set -u
cd /mnt/e/Project/GAMESS || exit 3
RUN=36877803728
OUT=/mnt/e/Project/GAMESS/evidence/release_qa/20261001T150706Z_github_actions_first_runs.out
TOK=$(tr -d '\r\n' < /mnt/e/tmp/nlcsplit_pat.tmp)
redact() { sed -E 's/ghp_[A-Za-z0-9]+/<TOKEN>/g'; }
W=$(mktemp -d)
curl -sSL --max-time 180 -H "Authorization: Bearer $TOK" \
  -o "$W/logs.zip" "https://api.github.com/repos/Haangyeon/nlcsplit/actions/runs/$RUN/logs"
cd "$W" && unzip -o -q logs.zip || { echo "unzip 失败"; exit 4; }
{
  echo ''
  echo '--- 追加：run #5 (HEAD 0a05675) 两臂的 pytest 汇总行，逐字取自 job 日志'
  echo '    为什么单列这一段：step=success 只说明没有非零退出，不说明跑了多少项。'
  echo '    "0 违规"和"0 条被解析"打印出来长得一样，所以这里要的是分母。'
  for f in $(find . -name "1_pytest*.txt" -o -name "0_pytest*.txt" | sort); do
    arm=$(basename "$f" .txt | sed 's/^[0-9]_//')
    echo "  [$arm]"
    grep -E "^[0-9]+ (passed|failed)|passed|failed|error" "$f" \
      | grep -vE "^ *$|##\[|^20[0-9]{2}-" | tail -3 | sed 's/^/    /'
  done
} >> "$OUT"
cd /mnt/e/Project/GAMESS || exit 5
( cd evidence/release_qa && sha256sum -b *.out *.txt *.md > MANIFEST.sha256 && sha256sum -c --strict MANIFEST.sha256 2>&1 | grep -vc ": OK$" )
rm -rf "$W"
echo "tail of archive:"
tail -12 "$OUT" | redact
