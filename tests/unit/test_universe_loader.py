"""
test_universe_loader.py — ETFListLoader 单元测试（L321 教训 P0-2 修复）

按 v2 设计：ETFListLoader 不接受 db_path（与 db 解耦，从 configs/etf_list.json 读）。
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestETFListLoaderSignature:
    """L321 教训 P0-2：ETFListLoader 签名与 db 解耦。"""

    def test_init_takes_no_args(self):
        from etf_quant.universe import ETFListLoader
        sig = inspect.signature(ETFListLoader.__init__)
        # __init__ 应该只接受 self
        params = [p for p in sig.parameters.keys() if p != "self"]
        assert params == [], \
            f"ETFListLoader.__init__ 不应接受参数（L321），实际: {params}"

    def test_init_does_not_accept_db_path(self):
        """L321 教训 P0-2 核心：传 db_path 应抛 TypeError"""
        from etf_quant.universe import ETFListLoader
        with pytest.raises(TypeError) as exc_info:
            ETFListLoader(db_path="/tmp/fake.db")
        assert "db_path" in str(exc_info.value) or "argument" in str(exc_info.value).lower()

    def test_get_core_pool_returns_list(self):
        from etf_quant.universe import ETFListLoader
        loader = ETFListLoader()
        pool = loader.get_core_pool()
        assert isinstance(pool, list)
        assert len(pool) >= 1, "core 池应至少包含 1 只 ETF"


class TestRunRealBacktestGetCoreCodes:
    """L321 教训 P0-2：run_real_backtest.all 不依赖 db_path 传参。"""

    def test_get_core_codes_runs_without_db_path(self):
        """get_core_codes() 应不报错（修复前会 TypeError）"""
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
        from scripts.run_real_backtest import get_core_codes
        codes = get_core_codes()
        assert isinstance(codes, list)
        assert len(codes) >= 14, f"core 池应 ≥14 只，实际: {len(codes)}"
        # core 池必须是字符串
        for c in codes:
            assert isinstance(c, str)
            assert c.isdigit(), f"ETF 代码应是数字字符串: {c}"
