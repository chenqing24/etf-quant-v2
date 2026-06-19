"""
tests/conftest.py — pytest 全局配置（US-013 引入）

按规则 5（先测试再交付）+ 规则 11（先调研再实现）：
    - 自动将 src/ 加入 sys.path，让 `import etf_quant.*` 可用
    - 避免每个测试文件重复 sys.path 注入

业界参考（按规则 13）：
    - pytest 官方 conftest 文档（https://docs.pytest.org/en/stable/reference/fixtures.html）
"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
