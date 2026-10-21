#!/usr/bin/env bash
# 独立复核刚重生成的证据清单：用 coreutils 的 sha256sum -c，而不是只信我自己的生成器。
# 同时把"清单里有没有登记不存在的档"与"目录里有没有没登记的散档"两件事分开数——
# 前者是 sha256sum -c 能抓的，后者要反向比一次。
set -u
cd /mnt/e/Project/GAMESS || exit 2
# 不传参数就自己遍历全部目录。**不要把 `$(ls ...)` 拼进 `bash -lc` 的字符串里**——
# 命令替换产生的换行会留在脚本正文里，从第二行起每一行都被当命令执行（本轮实测）。
if [ "$#" -eq 0 ]; then
  set -- $(find evidence -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | LC_ALL=C sort)
fi
for d in "$@"; do
  dir="evidence/$d"
  mf="$dir/MANIFEST.sha256"
  [ -f "$mf" ] || { echo "$d: 没有清单"; continue; }
  out=$(cd "$dir" && sha256sum -c --quiet MANIFEST.sha256 2>&1)
  rc=$?
  nreg=$(wc -l < "$mf")
  # 反向：第一层里没被登记的散档（排除清单本身与临时文件）
  unreg=$(cd "$dir" && for f in *; do [ -f "$f" ] || continue
            [ "$f" = "MANIFEST.sha256" ] && continue
            grep -q -- "\*$f\$" MANIFEST.sha256 || printf '%s\n' "$f"; done)
  echo "== $d：登记 $nreg 条；sha256sum -c rc=$rc"
  [ -n "$out" ] && echo "   校验输出：$out"
  if [ -n "$unreg" ]; then
    echo "   !! 未登记的散档：$(printf '%s ' $unreg)"
  else
    echo "   未登记散档：0"
  fi
done
