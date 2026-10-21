#!/usr/bin/env bash
# 重生成 evidence/<目录>/MANIFEST.sha256。
#
# 为什么要脚本化：这份清单已经被手跑 one-liner 漏过两轮（10-11、10-12 各抓到 8 条陈旧），
# 而手跑的最大差异来源是 glob 把已删的旧档留着、或把子目录里的原件当成没登记。
#
# 三个自己踩过的坑：
#   1) 排除式只能排掉 MANIFEST.sha256 自己。evidence 下真有叫 MANIFEST.txt 的**原件**
#      （centos/、l2cp/、retrieval_calibration/ 各一份），按前缀 MANIFEST* 一把排掉就等于悄悄删登记。
#   2) 排序要 LC_ALL=C，否则本机排序把 `...levels0-9.out` 与 `.json` 的相对位置和已入库清单不同，
#      产出一个纯噪音的 diff。
#   3) 本脚本只覆盖目录**第一层**（与 lib.js 的 staleManifests() 同口径），但
#      evidence/attribution_referee/MANIFEST.sha256 是**手工登记过 outputs/ 子目录**的（16 条）。
#
# 2026-10-13 改：子目录条目**结转并逐条验活**，不再整目录拒绝。
#   原因（是实测出来的，不是推测）：`attribution_referee` 清单 23 条里 16 条是子目录路径，
#   而第一层只有 7 个文件 ⇒ 旧版"旧清单有条目新清单没有就拒绝"对**这个目录永远成立**，
#   于是 `make_evidence_manifest.sh`（不带参数=全部目录）**每天都 rc=1**。
#   收口脚本的第 2 步因此永远过不去，"staleManifests()=0" 与"一条登记都不许丢"
#   这两条验收按旧实现是互斥的。
#   新语义严格更强，不是放松：
#     - 子目录条目：必须还在磁盘上，且按原路径重算哈希后仍进清单；不见了 ⇒ 拒绝。
#     - 第一层条目：旧清单登记过而磁盘上没了 ⇒ 拒绝（那是真丢了，不是格式问题）。
#   两种拒绝都把条目名列出来。要往子目录上锁的正当做法仍是在子目录内各放一份
#   MANIFEST.sha256（rvv10_referee/orca_run/ 就是），本脚本不会代你做这件事。
#
# 用法：bash tools/make_evidence_manifest.sh [evidence 下的目录名 ...]
#       不传参数 = 全部目录。
set -eu
cd /mnt/e/Project/GAMESS
DIRS=("$@")
if [ ${#DIRS[@]} -eq 0 ]; then
  mapfile -t DIRS < <(find evidence -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | LC_ALL=C sort)
fi
SKIPPED=()
for d in "${DIRS[@]}"; do
  dir="evidence/$d"
  [ -d "$dir" ] || { echo "跳过（不是目录）：$dir"; continue; }
  mf="$dir/MANIFEST.sha256"

  # 旧清单里的子目录条目与第一层条目分开处理
  SUB=()
  if [ -f "$mf" ]; then
    while IFS= read -r s; do [ -n "$s" ] && SUB+=("$s"); done \
      < <(awk 'NF >= 2 {print $2}' "$mf" | sed 's/^\*//' | grep '/' || true)
  fi

  # (a) 子目录条目必须还在，且在 evidence/<目录> 之下（挡住 ../ 这种越界写法）
  gone=(); escape=()
  for s in ${SUB[@]+"${SUB[@]}"}; do
    case "$s" in ../*|/*) escape+=("$s"); continue;; esac
    [ -f "$dir/$s" ] || gone+=("$s")
  done
  if [ ${#escape[@]} -gt 0 ]; then
    echo "!! $dir 拒绝替换：子目录条目里有越界路径 ${escape[*]}（只接受目录内的相对路径）"
    SKIPPED+=("$d"); continue
  fi
  if [ ${#gone[@]} -gt 0 ]; then
    echo "!! $dir 拒绝替换：旧清单登记过、现在磁盘上没有的子目录原件 ${#gone[@]} 条"
    printf '       %s\n' "${gone[@]}"
    SKIPPED+=("$d"); continue
  fi

  # (b) 第一层：旧清单有、现在没了 ⇒ 真丢了，拒绝（这条是旧版那道闸的本意）
  lost=""
  if [ -f "$mf" ]; then
    lost=$(comm -23 \
      <(awk 'NF >= 2 {print $2}' "$mf" | sed 's/^\*//' | grep -v '/' | LC_ALL=C sort) \
      <(cd "$dir" && for f in *; do [ -f "$f" ] || continue; [ "$f" = "MANIFEST.sha256" ] && continue; printf '%s\n' "$f"; done | LC_ALL=C sort))
  fi
  if [ -n "$lost" ]; then
    echo "!! $dir 拒绝替换：旧清单里有 $(printf '%s\n' "$lost" | wc -l) 条第一层登记已不在磁盘上"
    printf '       %s\n' $lost
    SKIPPED+=("$d"); continue
  fi

  # (c) 生成：第一层文件 + 结转的子目录条目，一起按名字排序后逐条哈希
  # ⚠ `${SUB[@]+"${SUB[@]}"}` 在**空数组**时会退化成 `printf '%s\n'`（零参数），
  #    而 printf 会把格式串循环一次、输出一个**空行**；那个空行喂进 `sha256sum -- ""`
  #    就是 `set -e` 下整条子 shell 非零退出——2026-10-18 实测：清单**没被替换**（mv 没跑到，
  #    旧清单原样留着，这点是安全的），但收口第 2 步对这些目录**从来没成功过**，
  #    并在目录里留下一个 0 字节的 `.MANIFEST.tmp`。`recompute` 与 `release_qa` 的清单
  #    都不含子目录条目（`grep -c '/'` = 0），所以正好全命中这条。
  #    修法：空数组就一行都不印。
  ( cd "$dir"
    : > .MANIFEST.tmp
    { for f in *; do
        [ -f "$f" ] || continue
        [ "$f" = "MANIFEST.sha256" ] && continue
        printf '%s\n' "$f"
      done
      [ ${#SUB[@]} -gt 0 ] && printf '%s\n' "${SUB[@]}"
    } | LC_ALL=C sort -u | while read -r f; do
        [ -n "$f" ] || continue
        sha256sum -b -- "$f" >> .MANIFEST.tmp
      done )
  mv "$dir/.MANIFEST.tmp" "$mf"
  echo "$mf  $(wc -l < "$mf") 条（含结转的子目录条目 ${#SUB[@]} 条）"
done
if [ ${#SKIPPED[@]} -gt 0 ]; then
  echo "有 ${#SKIPPED[@]} 个目录没重生成：${SKIPPED[*]}（上面列了每个目录为什么被拒）"
  exit 1
fi
