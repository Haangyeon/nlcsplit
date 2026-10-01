#!/usr/bin/env bash
# 把导出树以**一个普通提交**更新到已存在的远端仓（publish_github.js 按设计只推空仓、
# 且绝不 force，所以这里自己走 git）。安全约束：
#   · 不 --force、不改写历史：在 origin/main 之上加一个 commit。
#   · token 只从文件读进变量，不写进命令行字面量之外；所有输出统一过 redact，
#     因为 9-30 那次实测 node 会把整条 git 命令行印进异常，那一行里 token 是明文。
#   · 凭据文件在仓库外（E:\tmp），用完即删。
set -u
REPO_DIR=/mnt/e/tmp/pubwork
SRC=/mnt/e/Project/GAMESS/.publish/nlcsplit
TOKF=/mnt/e/tmp/nlcsplit_pat.tmp
LOG=/mnt/e/Project/GAMESS/scratch/push_manual.log
redact() { sed -E 's/ghp_[A-Za-z0-9]+/<TOKEN>/g'; }

TOK=$(tr -d '\r\n' < "$TOKF")
if ! echo "$TOK" | grep -q '^ghp_[A-Za-z0-9]\{30,\}$'; then
  echo "凭据文件不像一枚 classic PAT（长度 $(printf %s "$TOK" | wc -c)），中止" | redact > "$LOG"
  exit 2
fi
URL="https://x-access-token:${TOK}@github.com/Haangyeon/nlcsplit.git"

: > "$LOG"
rm -rf "$REPO_DIR"
{
  echo "== clone =="
  GIT_TERMINAL_PROMPT=0 git clone --quiet "$URL" "$REPO_DIR" 2>&1 | redact
  echo "clone_rc=${PIPESTATUS[0]}"
  cd "$REPO_DIR" || exit 3
  echo "远端 HEAD: $(git rev-parse --short HEAD)  文件数: $(git ls-files | wc -l)"

  echo "== 用导出树替换工作区（保留 .git）=="
  git rm -r -q --ignore-unmatch . 2>&1 | redact
  cp -r "$SRC/." "$REPO_DIR/" 2>&1 | redact
  git add -A 2>&1 | redact
  echo "暂存后文件数: $(git ls-files | wc -l)  导出树文件数: $(find "$SRC" -type f | wc -l)"
  echo "== diff 摘要 =="
  git diff --cached --shortstat 2>&1 | redact

  echo "== commit =="
  # 消息走文件，不走 -m 内联：上一版把整段消息塞进双引号，而消息里有一个英文撇号
  # （manuscript's），bash 当场把字符串截断，git 报 "pathspec did not match"，
  # **提交根本没产生**；可脚本照旧往下走，push 回显 "Everything up-to-date" 看着像成功。
  # 两处一起修：(1) -F 读文件，任何引号都不参与 shell 解析；(2) rc 取 ${PIPESTATUS[0]}，
  # 因为管道尾是 redact，$? 量的是 sed 不是 git——那正是假 commit_rc=0 的来源。
  git -c user.name='Haangyeon' -c user.email='haangyeon@snnu.edu.cn' \
      commit -q -F /mnt/e/Project/GAMESS/tools/qa/push_msg.txt 2>&1 | redact
  crc=${PIPESTATUS[0]}
  echo "commit_rc=$crc"
  if [ "$crc" -ne 0 ]; then echo "COMMIT_FAILED：不 push" >> "$LOG"; exit 4; fi
  git log --oneline -2 2>&1 | redact

  echo "== push（不 force）=="
  git push origin HEAD:main 2>&1 | redact
  prc=${PIPESTATUS[0]}
  echo "push_rc=$prc"
  if [ "$prc" -ne 0 ]; then echo "PUSH_FAILED" >> "$LOG"; exit 5; fi
  git rev-parse HEAD 2>&1 | redact
} >> "$LOG" 2>&1
echo "done rc=$?" >> "$LOG"
