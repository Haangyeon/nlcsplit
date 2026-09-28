"""nlcsplit —— 非局域关联能（VV10 / rVV10）的片段-成对分解。

不含任何 GAMESS 代码；依赖 PySCF（Apache-2.0）。
"""
from . import partition, nlc, geomlib  # noqa: F401

__version__ = "0.1.0"
