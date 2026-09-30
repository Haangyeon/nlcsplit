"""注册 slow 标记。

放在包内而不是只写仓库的 pyproject.toml：用户按文档跑
`pytest --pyargs nlcsplit` 时 rootdir 不在本仓库，读不到 pyproject 里的
`[tool.pytest.ini_options]`，就会对每个 @pytest.mark.slow 报
PytestUnknownMarkWarning。这文件跟着包一起装，标记在哪儿都是已登记的。
"""

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: 需要完整 SCF/多网格档位，默认由 addopts 排除")
