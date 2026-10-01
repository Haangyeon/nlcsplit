#!/usr/bin/env bash
# 转 public + 换描述。token 只在本进程里从文件读入，绝不落进命令行字面量；
# 所有回显过 redact（node/git 曾把整条命令行印进异常，那是唯一的泄漏路径）。
set -u
TOK=$(tr -d '\r\n' < /mnt/e/tmp/nlcsplit_pat.tmp)
redact() { sed -E 's/ghp_[A-Za-z0-9]+/<TOKEN>/g'; }
BODY=$(cat <<'EOF'
{"private":false,
 "description":"nlcsplit — fragment and pair decomposition of the VV10 nonlocal-correlation energy (PySCF backend). 213-file release tree, 15 export gates, raw evidence archived.",
 "homepage":"https://github.com/Haangyeon/nlcsplit#readme"}
EOF
)
TMPB=$(mktemp); printf '%s' "$BODY" > "$TMPB"

echo "== before =="
curl -sS --max-time 60 -H "Authorization: Bearer $TOK" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/Haangyeon/nlcsplit \
  | grep -Eo '"(private|visibility)":[^,]*' | redact

echo "== PATCH =="
code=$(curl -sS --max-time 60 -o /tmp/patch_out.json -w '%{http_code}' \
  -X PATCH https://api.github.com/repos/Haangyeon/nlcsplit \
  -H "Authorization: Bearer $TOK" -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" -H "Content-Type: application/json" \
  --data-binary "@$TMPB")
echo "http=$code"
grep -Eo '"(private|visibility)":[^,]*' /tmp/patch_out.json | redact
rm -f "$TMPB" /tmp/patch_out.json

echo "== 匿名验证（不带任何凭据）=="
for u in https://api.github.com/repos/Haangyeon/nlcsplit \
         https://raw.githubusercontent.com/Haangyeon/nlcsplit/main/README.md \
         https://github.com/Haangyeon/nlcsplit; do
  printf "%s -> %s\n" "$u" "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 60 "$u")"
done
