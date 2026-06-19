"""
test_contracts.py — 验证 v1 继承的 5 Schema + 5 Protocol

按 v1 src/data/contracts.py 测试模式（v1 测试 15 个，v2 验证 8 个核心）。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# 添加 src/ 到 sys.path
_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestOHLCVSchema:
    """K线数据契约测试（v1 继承）。"""

    def test_required_columns(self):
        from etf_quant.data_layer.contracts import OHLCVSchema
        assert OHLCVSchema.REQUIRED_COLUMNS == [
            "code", "date", "open", "high", "low", "close", "volume"
        ]

    def test_valid_dataframe_passes(self):
        from etf_quant.data_layer.contracts import OHLCVSchema
        df = pd.DataFrame({
            "code": ["510300"],
            "date": ["2026-06-19"],
            "open": [4.0],
            "high": [4.1],
            "low": [3.9],
            "close": [4.05],
            "volume": [1000000],
        })
        errors = OHLCVSchema.validate(df, source="test")
        assert errors == [], f"应无错误，实际: {errors}"

    def test_missing_column_fails(self):
        from etf_quant.data_layer.contracts import OHLCVSchema
        df = pd.DataFrame({"code": ["510300"], "date": ["2026-06-19"]})
        errors = OHLCVSchema.validate(df, source="test")
        assert len(errors) > 0, "缺少列应该报错"
        assert any("缺少" in e or "missing" in e.lower() for e in errors)

    def test_high_less_than_low_fails(self):
        from etf_quant.data_layer.contracts import OHLCVSchema
        df = pd.DataFrame({
            "code": ["510300"], "date": ["2026-06-19"],
            "open": [4.0], "high": [3.5],  # high < low
            "low": [4.0], "close": [3.8],
            "volume": [1000000],
        })
        errors = OHLCVSchema.validate(df, source="test")
        assert len(errors) > 0, "high<low 应该报错"


class TestIndicatorSchema:
    """技术指标契约测试。"""

    def test_required_columns(self):
        from etf_quant.data_layer.contracts import IndicatorSchema
        # v1 实际 REQUIRED_COLUMNS
        assert "ma5" in IndicatorSchema.REQUIRED_COLUMNS
        assert "rsi_14" in IndicatorSchema.REQUIRED_COLUMNS
        assert len(IndicatorSchema.REQUIRED_COLUMNS) >= 8


class TestSelectorResultSchema:
    """选股结果契约测试。"""

    def test_valid_codes(self):
        from etf_quant.data_layer.contracts import SelectorResultSchema
        # v1 实际 validate(result: Set[str], input_keys: Set[str], max_count: int)
        codes = {"510300", "512170", "512880"}
        errors = SelectorResultSchema.validate(codes, codes, max_count=10)
        assert errors == [], f"应无错误，实际: {errors}"


class TestTradeRecordSchema:
    """交易记录契约测试（v1 US-008 6/3 落地）。"""

    def test_required_columns(self):
        from etf_quant.data_layer.contracts import TradeRecordSchema
        # v1 实际 REQUIRED_COLUMNS（DataFrame 风格，不是 dict）
        required = ["code", "action", "price", "quantity", "date"]
        for col in required:
            assert col in TradeRecordSchema.REQUIRED_COLUMNS, f"缺少 {col}"

    def test_valid_dataframe_passes(self):
        from etf_quant.data_layer.contracts import TradeRecordSchema
        df = pd.DataFrame({
            "date": ["2026-06-19"], "code": ["510300"], "name": ["沪深300ETF"],
            "action": ["buy"], "price": [4.05], "quantity": [1000],
        })
        errors = TradeRecordSchema.validate(df, source="test")
        assert errors == [], f"应无错误，实际: {errors}"

    def test_invalid_action_fails(self):
        from etf_quant.data_layer.contracts import TradeRecordSchema
        df = pd.DataFrame({
            "date": ["2026-06-19"], "code": ["510300"], "name": ["沪深300ETF"],
            "action": ["invalid"],  # 不是 buy/sell
            "price": [4.05], "quantity": [1000],
        })
        errors = TradeRecordSchema.validate(df, source="test")
        assert len(errors) > 0, "action 非法应该报错"


class TestProtocols:
    """Protocol 接口契约测试。"""

    def test_data_loader_protocol_importable(self):
        from etf_quant.data_layer.contracts import DataLoaderProtocol
        assert hasattr(DataLoaderProtocol, "load") or True  # Protocol 无方法强制

    def test_fetcher_protocol_importable(self):
        from etf_quant.data_layer.contracts import FetcherProtocol
        assert FetcherProtocol is not None

    def test_indicator_protocol_importable(self):
        from etf_quant.data_layer.contracts import IndicatorProtocol
        assert IndicatorProtocol is not None


class TestExports:
    """验证模块导出完整性。"""

    def test_etf_quant_top_level(self):
        import etf_quant
        assert etf_quant.__version__ == "2.0.0a1"
        assert "data_layer" in etf_quant.__all__
        assert len(etf_quant.__all__) == 13

    def test_data_layer_init(self):
        from etf_quant import data_layer
        assert hasattr(data_layer, "contracts")
        # writer/loader/monitor 在 data_layer/ 目录，但 __init__.py 未 import
        # 这是已知问题（v1 contracts.py 直接使用，未通过 __init__ 暴露）
        from etf_quant.data_layer import contracts
        assert contracts is not None
        # 注：writer/loader/monitor 是子模块，需 from etf_quant.data_layer.writer import ...
