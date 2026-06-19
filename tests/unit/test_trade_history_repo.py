"""
test_trade_history_repo.py — trade_history_repo 单元测试

按"测试驱动"模式（按 L238 教训：先读真实 API 再写测试）。
按"按优先级"：Step 1 立即测试。
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def temp_db_with_schema(tmp_path):
    """临时 DB + 已建表（防污染）。"""
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
    return str(db_path)


class TestTradeHistoryRepository:
    """trade_history_repo 测试。"""

    def test_repo_init(self, temp_db_with_schema):
        from etf_quant.data_layer.trade_history_repo import TradeHistoryRepository
        repo = TradeHistoryRepository(db_path=temp_db_with_schema)
        assert repo.db_path == temp_db_with_schema

    def test_insert_returns_id(self, temp_db_with_schema):
        from etf_quant.data_layer.trade_history_repo import (
            TradeHistoryRepository, TradeRecord,
        )
        repo = TradeHistoryRepository(db_path=temp_db_with_schema)
        trade = TradeRecord(
            date="2026-06-19", code="510300", name="沪深300ETF",
            action="buy", price=4.05, quantity=1000, amount=4050.0,
            reason="测试", is_real=0,
        )
        trade_id = repo.insert(trade)
        assert trade_id > 0, "trade_id 应大于 0"

    def test_insert_and_get(self, temp_db_with_schema):
        """插入后能 get 出来（Data Mapper 验证）。"""
        from etf_quant.data_layer.trade_history_repo import (
            TradeHistoryRepository, TradeRecord,
        )
        repo = TradeHistoryRepository(db_path=temp_db_with_schema)
        trade = TradeRecord(
            date="2026-06-19", code="510300", name="沪深300ETF",
            action="buy", price=4.05, quantity=1000, amount=4050.0,
            reason="测试", is_real=1, emotion="calm",
        )
        trade_id = repo.insert(trade)
        loaded = repo.get(trade_id)
        assert loaded is not None
        assert loaded.code == "510300"
        assert loaded.action == "buy"
        assert loaded.emotion == "calm"
        assert loaded.is_real == 1

    def test_list_by_code(self, temp_db_with_schema):
        """按 code 查询（v1 record_buy 模式）。"""
        from etf_quant.data_layer.trade_history_repo import (
            TradeHistoryRepository, TradeRecord,
        )
        repo = TradeHistoryRepository(db_path=temp_db_with_schema)
        # 插入 2 笔
        for i in range(2):
            repo.insert(TradeRecord(
                date=f"2026-06-{18 + i}", code="510300", name="沪深300ETF",
                action="buy" if i == 0 else "sell",
                price=4.0 + i * 0.05, quantity=1000, amount=(4.0 + i * 0.05) * 1000,
            ))
        # 插入 1 笔其他 ETF
        repo.insert(TradeRecord(
            date="2026-06-19", code="512170", name="医疗ETF",
            action="buy", price=0.5, quantity=1000, amount=500.0,
        ))
        # 查 510300 应有 2 笔
        trades = repo.list_by_code("510300")
        assert len(trades) == 2
        # 按 date DESC 排序
        assert trades[0].date == "2026-06-19"

    def test_list_all_with_limit(self, temp_db_with_schema):
        """list_all + limit（v1 load_trades 模式）。"""
        from etf_quant.data_layer.trade_history_repo import (
            TradeHistoryRepository, TradeRecord,
        )
        repo = TradeHistoryRepository(db_path=temp_db_with_schema)
        for i in range(5):
            repo.insert(TradeRecord(
                date=f"2026-06-{15 + i}", code=f"51{3000 + i}",
                name=f"ETF{i}", action="buy",
                price=4.0, quantity=100, amount=400.0,
            ))
        # limit=3 应返回 3 条
        all_trades = repo.list_all(limit=3)
        assert len(all_trades) == 3

    def test_delete(self, temp_db_with_schema):
        """delete（v1 不暴露但 Repo 提供）。"""
        from etf_quant.data_layer.trade_history_repo import (
            TradeHistoryRepository, TradeRecord,
        )
        repo = TradeHistoryRepository(db_path=temp_db_with_schema)
        trade_id = repo.insert(TradeRecord(
            date="2026-06-19", code="510300", name="沪深300ETF",
            action="buy", price=4.05, quantity=1000, amount=4050.0,
        ))
        assert repo.delete(trade_id) is True
        assert repo.get(trade_id) is None
        # 重复 delete 应返回 False
        assert repo.delete(trade_id) is False

    def test_wal_mode_enabled(self, temp_db_with_schema):
        """WAL 模式必须启用（v1 6/1 教训）。"""
        from etf_quant.data_layer.trade_history_repo import TradeHistoryRepository
        TradeHistoryRepository(db_path=temp_db_with_schema)
        conn = sqlite3.connect(temp_db_with_schema)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode.lower() == "wal"

    def test_data_mapper_all_31_fields(self, temp_db_with_schema):
        """Data Mapper 验证：31 字段全部往返。"""
        from etf_quant.data_layer.trade_history_repo import (
            TradeHistoryRepository, TradeRecord,
        )
        repo = TradeHistoryRepository(db_path=temp_db_with_schema)
        # 全字段填值
        trade = TradeRecord(
            date="2026-06-19", code="510300", name="沪深300ETF",
            action="buy", price=4.05, quantity=1000, amount=4050.0,
            reason="测试", expected_return=0.05, actual_pnl=0.03,
            note="note1", realtime_price=4.10, price_deviation=0.012,
            rsi_14=55.0, day_change_pct=0.02, score=85,
            signal_time="2026-06-19 09:30:00", signal_price=4.00,
            signal_rsi=50.0, signal_adx=25.0, signal_score=80,
            trade_time="2026-06-19 10:00:00", emotion="calm", session="A",
            is_real=1, is_paper=0,
            model="v8_sop", strategy="C21-1", evaluation="0.5296",
            snapshot_ref="snapshot_20260619",
        )
        trade_id = repo.insert(trade)
        loaded = repo.get(trade_id)
        # 验证每个字段
        assert loaded.date == "2026-06-19"
        assert loaded.expected_return == 0.05
        assert loaded.actual_pnl == 0.03
        assert loaded.note == "note1"
        assert loaded.realtime_price == 4.10
        assert loaded.price_deviation == 0.012
        assert loaded.rsi_14 == 55.0
        assert loaded.day_change_pct == 0.02
        assert loaded.score == 85
        assert loaded.signal_time == "2026-06-19 09:30:00"
        assert loaded.signal_price == 4.00
        assert loaded.signal_rsi == 50.0
        assert loaded.signal_adx == 25.0
        assert loaded.signal_score == 80
        assert loaded.trade_time == "2026-06-19 10:00:00"
        assert loaded.emotion == "calm"
        assert loaded.session == "A"
        assert loaded.is_real == 1
        assert loaded.is_paper == 0
        assert loaded.model == "v8_sop"
        assert loaded.strategy == "C21-1"
        assert loaded.evaluation == "0.5296"
        assert loaded.snapshot_ref == "snapshot_20260619"
