"""
test_execution_tracker_v2.py — v2 TradeTracker 单元测试

按 v2 委托模式 + v1 14 公开方法 100% 保留。
按"测试驱动"（用户原话"完整测试"）。
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def temp_db_with_schema(tmp_path):
    db_path = tmp_path / "etf.db"
    schema_dir = _SRC.parent / "schema" / "migrations"
    sql_files = sorted(schema_dir.glob("00[0-9]_*.sql"))
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    for sql_path in sql_files:
        sql = sql_path.read_text(encoding="utf-8")
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError:
                    pass
    conn.commit()
    conn.close()
    # 插入 etf_names（外键依赖 + tradable=1 才能 can_buy）
    conn = sqlite3.connect(str(db_path))
    for code, name in [
        ("510300", "沪深300ETF"), ("512170", "医疗ETF"), ("515050", "通信ETF"),
    ]:
        conn.execute(
            "INSERT INTO etf_names (code, name, tradable, pool_role) "
            "VALUES (?, ?, 1, 'core')",
            (code, name),
        )
    conn.commit()
    conn.close()
    return str(db_path)


class TestTradeTrackerV2Init:
    def test_init_uses_default_db_path(self, tmp_path, monkeypatch):
        from etf_quant.execution.tracker import TradeTracker
        from etf_quant.config import constants
        db_path = tmp_path / "etf.db"
        original = constants.DB_PATH
        constants.DB_PATH = str(db_path)
        try:
            tracker = TradeTracker(data_dir=".")
            assert tracker.db_path == str(db_path)
        finally:
            constants.DB_PATH = original

    def test_init_accepts_custom_db_path(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        assert tracker.db_path == temp_db_with_schema

    def test_init_zero_sqlite3_in_business(self, temp_db_with_schema):
        """v2 规则 15：业务层零 sqlite3。"""
        from etf_quant.execution.tracker import TradeTracker
        import inspect, re
        src = inspect.getsource(TradeTracker)
        sqlite_uses = re.findall(r"sqlite3\.\w+|import sqlite3", src)
        assert len(sqlite_uses) == 0, f"业务层禁止 sqlite3，实际: {sqlite_uses}"


class TestTradeTrackerV2Record:
    def test_record_buy_creates_trade_and_position(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        trade_id = tracker.record_buy(
            code="510300", name="沪深300ETF",
            price=4.05, quantity=1000, reason="测试买入",
            is_real=0,
        )
        assert trade_id > 0
        # trade_history 应有 1 条
        trades = tracker.load_trades()
        assert len(trades) == 1
        assert trades[0].action == "buy"
        # positions 应有 1 条（HOLDING）
        positions = tracker.load_positions()
        assert len(positions) == 1
        assert positions[0].status == "HOLDING"
        # audit_log 应有 1 条
        logs = tracker._audit_repo.list_by_code("510300")
        assert len(logs) == 1
        assert logs[0]["action"] == "record_buy"

    def test_record_sell_creates_trade_and_removes_position(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        tracker.record_buy(code="510300", name="沪深300ETF", price=4.05, quantity=1000)
        sell_id = tracker.record_sell(
            code="510300", name="沪深300ETF",
            price=4.10, quantity=1000, reason="测试卖出",
        )
        assert sell_id > 0
        # 2 笔交易（1 buy + 1 sell）
        trades = tracker.load_trades()
        assert len(trades) == 2
        # 持仓应删除（quantity 完全匹配）
        positions = tracker.load_positions()
        assert len(positions) == 0


class TestTradeTrackerV2Query:
    def test_load_trades_returns_list(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        tracker.record_buy(code="510300", name="沪深300ETF", price=4.05, quantity=1000)
        trades = tracker.load_trades()
        assert isinstance(trades, list)
        assert len(trades) == 1

    def test_load_positions_returns_list(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        tracker.record_buy(code="510300", name="沪深300ETF", price=4.05, quantity=1000)
        positions = tracker.load_positions()
        assert isinstance(positions, list)
        assert len(positions) == 1

    def test_get_holdings_returns_list(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        holdings = tracker.get_holdings()
        assert isinstance(holdings, list)
        assert len(holdings) == 0


class TestTradeTrackerV2Risk:
    def test_can_buy_new_code(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        # 池内有 510300，未持仓 → 可以买
        assert tracker.can_buy("510300") is True

    def test_can_buy_existing_holding(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        tracker.record_buy(code="510300", name="沪深300ETF", price=4.05, quantity=1000)
        # 已持仓 → 不能买
        assert tracker.can_buy("510300") is False

    def test_can_buy_invalid_code(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        # 999999 不在池内 → 不能买
        assert tracker.can_buy("999999") is False

    def test_check_stop_loss(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        tracker.record_buy(code="510300", name="沪深300ETF", price=4.05, quantity=1000)
        # 模拟 -5% 止损（v1 真实 API: code + threshold）
        result = tracker.check_stop_loss("510300", threshold=-5)
        assert isinstance(result, bool)

    def test_check_take_profit(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        result = tracker.check_take_profit("510300", threshold=8)
        assert isinstance(result, bool)


class TestTradeTrackerV2Portfolio:
    def test_check_portfolio(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        tracker.record_buy(code="510300", name="沪深300ETF", price=4.05, quantity=1000)
        portfolio = tracker.check_portfolio()
        assert portfolio["total_positions"] == 1
        assert portfolio["holding_positions"] == 1
        assert portfolio["total_quantity"] == 1000

    def test_check_data_consistency(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        tracker.record_buy(code="510300", name="沪深300ETF", price=4.05, quantity=1000)
        report = tracker.check_data_consistency()
        assert report["trade_count"] == 1
        assert report["position_count"] == 1
        assert report["consistent"] is True

    def test_get_consistency_report(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        report = tracker.get_consistency_report()
        assert "trade_count" in report
        assert "position_count" in report

    def test_get_account_summary(self, temp_db_with_schema):
        from etf_quant.execution.tracker import TradeTracker
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        summary = tracker.get_account_summary()
        assert "cash" in summary
        assert "positions_value" in summary
        assert "total_pnl" in summary

    def test_export_csv(self, temp_db_with_schema, tmp_path):
        from etf_quant.execution.tracker import TradeTracker
        import os
        tracker = TradeTracker(data_dir=".", db_path=temp_db_with_schema)
        tracker.record_buy(code="510300", name="沪深300ETF", price=4.05, quantity=1000)
        output = tmp_path / "trades.csv"
        tracker.export_csv(str(output))
        # CSV 头应存在
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "code" in content  # CSV header
        assert "510300" in content  # 数据
