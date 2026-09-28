#!/bin/bash
# 在 CentOS(10.8.51.23:24522) 上准备 nlcsplit 的计算环境。
# 只新增：python3-venv/python3-pip 包、/root/gamess_work/ 下的 venv 与代码副本。
# 明确不碰 /root/GAMESS_BLW（另一条线的活跃目录）。
set -o pipefail
export DEBIAN_FRONTEND=noninteractive
echo "== host =="; hostname; nproc; free -g | sed -n 2p

if ! command -v pip3 >/dev/null; then
  echo "== apt: python3-venv python3-pip =="
  apt-get install -y -qq python3-venv python3-pip 2>&1 | tail -3
fi

W=/root/gamess_work/nlcsplit
mkdir -p "$W"
if [ ! -d "$W/venv" ]; then
  echo "== venv =="; python3 -m venv "$W/venv" 2>&1 | tail -2
fi
echo "== pip install pyscf =="
"$W/venv/bin/pip" install -q --disable-pip-version-check pyscf numpy scipy 2>&1 | tail -4
"$W/venv/bin/python" -c "import pyscf, numpy; print('pyscf', pyscf.__version__, 'numpy', numpy.__version__)"
echo "== dirs =="; ls -d "$W"/venv >/dev/null && echo "workdir ready: $W"
