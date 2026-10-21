#!/usr/bin/env bash
# 逐目录核对：证据清单相对 HEAD 有没有**条目消失**（不只是"有没有新档没登记"）。
#
# 为什么单独要一个脚本：验收条件写的是"staleManifests()=0 **且**逐目录核对相对上一版无条目消失"，
# 而后半句此前只靠我手工 diff 做。手工做的那一步在收工时最容易跳，而它防的正是
# 本仓真出事过的那一类静默损失：`evidence/attribution_referee/MANIFEST.sha256` 手工登记过
# `outputs/` 子目录 16 条原件，而清单脚本与 lib.js 都只看第一层 ⇒ 照第一层重生成会
# **静默删掉那 16 条**，且 stale 仍然等于 0，用陈旧度检查完全看不见这个损失。
#
# 口径：只比"条目名"（清单第二列，去掉 `sha256sum -b` 的前导 `*`），不比哈希——
# 哈希变了是正常重算，条目没了才是丢登记。
#
# 退出码：0 = 无丢失；1 = 有目录丢条目（逐条列出）；2 = 环境不对（不在仓根 / 没有 git）。
set -u
# 本脚本写死 WSL 路径，所以从 Windows 侧（Git Bash）跑必然失败——而失败信息必须说清是"跑错了一侧"，
# 不是"仓坏了"。今晚就有一次真实误读：在 Windows 侧跑它得到 rc=2「取不到 HEAD」，
# 看起来像 git 出问题，实际是 `cd /mnt/e/...` 之后的 git 在错的环境里找不到仓。
cd /mnt/e/Project/GAMESS || { echo "只能在仓根跑（当前 shell 不是 WSL 侧的 /mnt/e/Project/GAMESS）"; exit 2; }
if ! git rev-parse HEAD >/dev/null 2>&1; then
  echo "!! 取不到 HEAD —— 先确认你在哪一侧：本脚本要 WSL 侧（wsl bash -lc ...）；"
  echo "   Windows 侧 Git Bash 里 /mnt/e 可能存在但 git 认不出仓，症状就是这个。"
  echo "   仓本身是否健康，用 Windows 侧的 \`git rev-parse HEAD\` 单独验。"
  exit 2
fi
HEAD=$(git rev-parse HEAD)

echo "# 证据清单丢条目核对  HEAD $HEAD"
echo "# 生成 $(date -u +%FT%TZ)"
echo

LOST_TOTAL=0
UNASSESSABLE=()
# 与 make_evidence_manifest.sh 同口径：evidence 下的第一层目录
while IFS= read -r d; do
  dir="evidence/$d"
  mf="$dir/MANIFEST.sha256"
  [ -f "$mf" ] || continue
  if ! git cat-file -e "HEAD:$mf" 2>/dev/null; then
    echo "   $d：HEAD 里没有这份清单 ⇒ 无基线可比（新建目录，本脚本判不了它有没有丢东西）"
    UNASSESSABLE+=("$d")
    continue
  fi
  git show "HEAD:$mf" | awk '{print $2}' | sed 's/^\*//' | LC_ALL=C sort > /tmp/.mrun_old.$$
  awk '{print $2}' "$mf" | sed 's/^\*//' | LC_ALL=C sort > /tmp/.mrun_new.$$
  lost=$(comm -23 /tmp/.mrun_old.$$ /tmp/.mrun_new.$$)
  rm -f /tmp/.mrun_old.$$ /tmp/.mrun_new.$$
  n_old=$(git show "HEAD:$mf" | awk 'NF >= 2 {print $2}' | wc -l)
  if [ -n "$lost" ]; then
    nl=$(printf '%s\n' "$lost" | wc -l)
    LOST_TOTAL=$((LOST_TOTAL + nl))
    echo "!! $d：相对 HEAD 丢了 $nl 条登记（HEAD 共 $n_old 条）"
    printf '       %s\n' $lost
  fi
done < <(find evidence -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | LC_ALL=C sort)

echo
if [ ${#UNASSESSABLE[@]} -gt 0 ]; then
  echo "# 无基线可比（不算失败，但要说出来）：${UNASSESSABLE[*]}"
fi
if [ "$LOST_TOTAL" -ne 0 ]; then
  echo "VERDICT LOST —— 共 $LOST_TOTAL 条登记相对 HEAD 消失。"
  echo "   先查是不是有人照第一层重生成了含子目录登记的目录；修法是把子目录原件单独放一份清单，"
  echo "   或在旧清单里手工补回，**不要**为了消音而接受新清单。"
  exit 1
fi
echo "VERDICT OK —— 没有任何目录的清单条目相对 HEAD 消失"
exit 0
