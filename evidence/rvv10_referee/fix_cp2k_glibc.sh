#!/usr/bin/env bash
# 让 CP2K 在这台 WSL（Ubuntu 22.04 / glibc 2.35）上真能跑起来。
#
# 2026-10-12 实测：conda-forge 现役 cp2k 2026.2 起来就死，报
#   /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.38' not found
#     (required by .../lib/libxs.so.1  与  .../lib/libxsmm.so.2)
# ⇒ 不是我的输入语法问题，是**包本身要 glibc 2.38**，而本机是 2.35。
#     我第一版把它当成"输入被拒"去查 job.inp，白绕了一圈——记进坑表。
#
# 两级尝试，先便宜的：
#   1) 把现有 env 里的 libxsmm 降到 glibc 2.35 时代能用的构建，再试 `-V`
#   2) 不行就装旧版 cp2k=2024.2（conda-forge 那个时期的包还是 2.17/2.35 target）
# 每级都跑一次 `-V` 并把结果原样打出来，判据只有一条：**能不能打印出版本号**。
# 包缓存与 env 全放 E:（本机规矩：C 盘只放小文件）。
set -u
CONDA=/home/haangyeon/miniconda3/bin/conda
export CONDA_PKGS_DIRS=/mnt/e/conda_pkgs

echo "### 本机 glibc"
ldd --version | head -1

echo ""
echo "### 尝试 1：降 libxsmm（现有 2026.2 env）"
$CONDA install -y -p /mnt/e/conda_envs/cp2kprobe -c conda-forge "libxsmm=1.17" 2>&1 | tail -4
echo "--- 试跑 -V ---"
LD_LIBRARY_PATH=/mnt/e/conda_envs/cp2kprobe/lib /mnt/e/conda_envs/cp2kprobe/bin/cp2k.popt -V 2>&1 | head -5
# 成功判据：横幅里有 "CP2K ... 20xx"，且**没有** "not found" 那行
#   （注意：加载器报错里也含 "version" 一词，所以不能拿 version 当成功标志）
if LD_LIBRARY_PATH=/mnt/e/conda_envs/cp2kprobe/lib /mnt/e/conda_envs/cp2kprobe/bin/cp2k.popt -V 2>&1 | grep -qE "CP2K.{0,40}20[0-9][0-9]"; then
    echo "### 尝试 1 成功：用 2026.2 env"
    exit 0
fi

echo ""
echo "### 尝试 2：装旧版 cp2k=2024.2 到新 prefix"
$CONDA create -y -p /mnt/e/conda_envs/cp2k24 -c conda-forge "cp2k=2024.2" 2>&1 | tail -6
echo "--- 试跑 -V ---"
LD_LIBRARY_PATH=/mnt/e/conda_envs/cp2k24/lib /mnt/e/conda_envs/cp2k24/bin/cp2k.popt -V 2>&1 | head -5
if LD_LIBRARY_PATH=/mnt/e/conda_envs/cp2k24/lib /mnt/e/conda_envs/cp2k24/bin/cp2k.popt -V 2>&1 | grep -qE "CP2K.{0,40}20[0-9][0-9]"; then
    echo "### 尝试 2 成功：用 /mnt/e/conda_envs/cp2k24"
    exit 0
fi

echo "### 两级都失败 —— 本机 WSL 用不了 conda 版 CP2K，裁判只能换 VASP（集群，配额另议）或 Q-Chem（要授权）"
exit 1
