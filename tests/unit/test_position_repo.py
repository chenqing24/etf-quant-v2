"""
test_position_repo.py — positions Repository 单元测试
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
    # 插入 etf_names 外键
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO etf_names (code, name) VALUES ('510300', '沪深300ETF')"
    )
    conn.execute(
        "INSERT INTO etf_names (code, name) VALUES ('512170', '医疗ETF')"
    )
    conn.commit()
    conn.close()
    return str(db_path)


class TestPositionRepository:
    def test_insert_and_get(self, temp_db_with_schema):
        from etf_quant.data_layer.position_repo import PositionRepository, Position
        repo = PositionRepository(db_path=temp_db_with_schema)
        pos = Position(
            code="510300", name="沪深300ETF",
            entry_date="2026-06-19", entry_price=4.05, quantity=1000,
            current_price=4.10, pnl_pct=0.0123, hold_days=5,
            status="HOLDING", score=85, is_real=1,
        )
        repo.insert(pos)
        loaded = repo.get("510300")
        assert loaded is not None
        assert loaded.code == "510300"
        assert loaded.status == "HOLDING"
        assert loaded.pnl_pct == 0.0123
        assert loaded.is_real == 1

    def test_list_all(self, temp_db_with_schema):
        from etf_quant.data_layer.position_repo import PositionRepository, Position
        repo = PositionRepository(db_path=temp_db_with_schema)
        for code in ["510300", "512170"]:
            repo.insert(Position(
                code=code, name=f"ETF{code}",
                entry_date="2026-06-19", entry_price=4.0, quantity=100,
            ))
        positions = repo.list_all()
        assert len(positions) == 2

    def test_list_by_status(self, temp_db_with_schema):
        from etf_quant.data_layer.position_repo import PositionRepository, Position
        repo = PositionRepository(db_path=temp_db_with_schema)
        repo.insert(Position(
            code="510300", name="沪深300ETF",
            entry_date="2026-06-19", entry_price=4.0, quantity=100,
            status="HOLDING",
        ))
        repo.insert(Position(
            code="512170", name="医疗ETF",
            entry_date="2026-06-19", entry_price=4.0, quantity=100,
            status="EMPTY",
        ))
        holdings = repo.list_by_status("HOLDING")
        assert len(holdings) == 1
        assert holdings[0].code == "510300"

    def test_insert_or_replace(self, temp_db_with_schema):
        """PRIMARY KEY code：重复 insert 应 REPLACE。"""
        from etf_quant.data_layer.position_repo import PositionRepository, Position
        repo = PositionRepository(db_path=temp_db_with_schema)
        repo.insert(Position(
            code="510300", name="沪深300ETF",
            entry_date="2026-06-19", entry_price=4.0, quantity=100,
        ))
        # 重复 code 应替换（不报错）
        repo.insert(Position(
            code="510300", name="沪深300ETF",
            entry_date="2026-06-20", entry_price=4.1, quantity=200,
        ))
        loaded = repo.get("510300")
        assert loaded.entry_price == 4.1
        assert loaded.quantity == 200

    def test_delete(self, temp_db_with_schema):
        from etf_quant.data_layer.position_repo import PositionRepository, Position
        repo = PositionRepository(db_path=temp_db_with_schema)
        repo.insert(Position(
            code="510300", name="沪深300ETF",
            entry_date="2026-06-19", entry_price=4.0, quantity=100,
        ))
        assert repo.delete("510300") is True
        assert repo.get("510300") is None
