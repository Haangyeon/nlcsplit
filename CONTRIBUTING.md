# 参与

- 开发在 WSL/Linux 与 PySCF>=2.12 上进行；CI 会同时跑 2.12.1 与更新的版本。
- 提交前本地跑 `python -m pytest -q`（8 项，约 90 s）。
- 任何新的能量口径必须同时给两条独立取数路径并在不一致时抛错，参照 `nlcsplit/step_f_dispersion.py` 的三条校验。
- 不要往仓库或脚本里写任何口令、私钥、凭据。
