#!/usr/bin/env bash
# 抓公开页 HTML，判断 README 里的公式是**被渲染**还是原样露出 $ 符号。
set -u
export https_proxy="${https_proxy:-http://127.0.0.1:7890}"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
out=$(mktemp)
curl -sSL --max-time 90 -A "$UA" -o "$out" https://github.com/Haangyeon/nlcsplit
echo "bytes=$(wc -c < "$out")"
echo "mathml_tags=$(grep -o '<math' "$out" | wc -l)"
echo "katex_or_tex_spans=$(grep -o 'js-preview-math\|math-block\|markdown-body' "$out" | sort | uniq -c | tr '\n' ' ')"
# 未渲染的 LaTeX 会在页面文本里留下这些字面量
for pat in 'E_{\\mathrm{NL}}' '\\iint' 'rho(' ; do
  printf 'literal %-16s = %s\n' "$pat" "$(grep -c -F "$pat" "$out")"
done
echo "--- 抽取渲染后的公式图/文本片段 ---"
grep -o 'aria-label="[^"]\{0,120\}' "$out" | head -3
rm -f "$out"
