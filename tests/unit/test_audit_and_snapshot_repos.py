"""
test_audit_and_snapshot_repos.py — audit_log + decision_snapshot Repos 测试
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
    return str(db_path)


class TestAuditLogRepository:
    def test_insert_and_list(self, temp_db_with_schema):
        from etf_quant.data_layer.audit_log_repo import (
            AuditLogRepository, AuditLog,
        )
        repo = AuditLogRepository(db_path=temp_db_with_schema)
        log_id = repo.insert(AuditLog(
            action="record_buy", code="510300",
            from_state="EMPTY", to_state="HOLDING",
            detail='{"price": 4.05, "quantity": 1000}',
        ))
        assert log_id > 0
        logs = repo.list_by_code("510300")
        assert len(logs) == 1
        assert logs[0]["action"] == "record_buy"
        assert logs[0]["from_state"] == "EMPTY"
        assert "price" in logs[0]["detail"]


class TestDecisionSnapshotRepository:
    def test_insert_and_get(self, temp_db_with_schema):
        from etf_quant.data_layer.decision_snapshot_repo import (
            DecisionSnapshotRepository, DecisionSnapshot,
        )
        repo = DecisionSnapshotRepository(db_path=temp_db_with_schema)
        snap = DecisionSnapshot(
            snapshot_id="snap_20260619_001",
            snapshot_time="2026-06-19 14:30:00",
            trigger="daily",
            model_name="v8_sop",
            model_version="1.0",
            strategy_name="C21-1",
            config_json='{"max_hold_days": 99999}',
            evaluation_json='{"alpha": 0.5296}',
            market_regime="趋势市",
            reasoning="BOLL 中轨 + MA60 入场",
            created_at="2026-06-19 14:30:05",
        )
        repo.insert(snap)
        loaded = repo.get("snap_20260619_001")
        assert loaded is not None
        assert loaded.trigger == "daily"
        assert loaded.strategy_name == "C21-1"
        assert loaded.market_regime == "趋势市"
        assert loaded.reasoning == "BOLL 中轨 + MA60 入场"

    def test_list_recent(self, temp_db_with_schema):
        from etf_quant.data_layer.decision_snapshot_repo import (
            DecisionSnapshotRepository, DecisionSnapshot,
        )
        repo = DecisionSnapshotRepository(db_path=temp_db_with_schema)
        for i in range(3):
            repo.insert(DecisionSnapshot(
                snapshot_id=f"snap_{i}",
                snapshot_time=f"2026-06-1{i}",
                trigger="daily",
                market_regime="趋势市",
                created_at=f"2026-06-1{i} 14:30:00",
            ))
        snaps = repo.list_recent(limit=2)
        assert len(snaps) == 2
