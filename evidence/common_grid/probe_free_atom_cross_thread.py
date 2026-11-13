"""跨进程、不同线程数下，自由原子 UHF 给的是不是同一个解。

为什么单独跑这一条：`probe_free_atom_uhf_stability.py` 测的是**同一进程内**重复 5 次
⇒ 当然全同（线程数没变）。而 `probe_tail_underflow_hypothesis.py` 发现换线程后
**58448 个点里有 38119 个（65%）的权重差 >1e-3**，且抖的点并不集中在远尾
⇒ "尾部下溢"解释不了这么大范围的差。剩下最可能的解释是：
**BLAS 线程数会改变 UHF 的迭代轨迹，于是收敛到不同的解**——那是在自由原子这一层就发生的，
不是归一化那一步放大的。这条一测就知道，代价几秒。
"""
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from nlcsplit import partition            # noqa: E402
from pyscf import gto, scf, dft           # noqa: E402

BASIS = "6-31g*"


def fingerprint(sym):
    atm = gto.M(atom="%s 0 0 0" % sym, basis=BASIS, unit="Angstrom",
                spin=partition.FREE_ATOM_MULT[sym] - 1, verbose=0)
    atm.build()
    mf = scf.UHF(atm).run()
    dm = np.asarray(mf.make_rdm1(), dtype=float)
    # 只比 1-RDM 本身（哈希 + 一个尺度无关的差值基准），不再去网格上取 ρ：
    # eval_rho 的入参形状我连着踩两次，而"是不是同一个解"这个问句根本不需要它。
    return {"e": float(mf.e_tot), "s2": float(mf.spin_square()[0]),
            "dm_hash": hashlib.sha256(dm.tobytes()).hexdigest()[:16],
            "dm_absmax": float(np.abs(dm).max())}


def main():
    out = {"threads": [os.environ.get(k) for k in
                       ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")],
           "atoms": {s: fingerprint(s) for s in ("H", "C", "N")}}
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
