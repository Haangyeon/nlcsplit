"""nlcsplit —— 非局域关联能（VV10 / rVV10）的片段-成对分解。

不含任何 GAMESS 代码；依赖 PySCF（Apache-2.0）。

`fastpair` 在这里显式导出：它是可证屏蔽那条线（配套算法文）的唯一入口，
只依赖 numpy，不拉 matplotlib；`figures` 故意不在这里，它要 matplotlib。

`certify` 是归属证书的入口（模块名是 `certificate`，函数名才是 `certify`，
这样 `nlcsplit.certify(...)` 直接可调用，同时 `import nlcsplit.certificate` 不被同名属性遮蔽）。
"""
from . import partition, nlc, geomlib, fastpair  # noqa: F401
from .certificate import certify                 # noqa: F401

__all__ = ["partition", "nlc", "geomlib", "fastpair", "certify"]
__version__ = "0.1.0"
