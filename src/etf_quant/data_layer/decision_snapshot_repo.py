"""
data_layer/decision_snapshot_repo.py — decision_snapshot 表 Repository
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class DecisionSnapshot:
    """决策快照 dataclass（schema 007 14 字段）。"""

    snapshot_id: str
    snapshot_time: str
    trigger: str  # 'daily'/'eval'/'manual'
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    strategy_name: Optional[str] = None
    config_json: str = "{}"
    evaluation_json: Optional[str] = None
    factor_breakdown_json: Optional[str] = None
    today_top_10_json: Optional[str] = None
    backtest_last_10_json: Optional[str] = None
    market_regime: Optional[str] = None
    reasoning: Optional[str] = None
    created_at: Optional[str] = None


class DecisionSnapshotRepository:
    """decision_snapshot 表 Repository。"""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def insert(self, snap: DecisionSnapshot) -> None:
        """插入决策快照。"""
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO decision_snapshot ("
                "snapshot_id, snapshot_time, trigger, model_name, model_version,"
                " strategy_name, config_json, evaluation_json, factor_breakdown_json,"
                " today_top_10_json, backtest_last_10_json, market_regime, reasoning, created_at"
                ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    snap.snapshot_id, snap.snapshot_time, snap.trigger,
                    snap.model_name, snap.model_version, snap.strategy_name,
                    snap.config_json, snap.evaluation_json, snap.factor_breakdown_json,
                    snap.today_top_10_json, snap.backtest_last_10_json,
                    snap.market_regime, snap.reasoning, snap.created_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get(self, snapshot_id: str) -> Optional[DecisionSnapshot]:
        """按 snapshot_id 查询。"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM decision_snapshot WHERE snapshot_id = ?",
                (snapshot_id,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return DecisionSnapshot(
            snapshot_id=row[0], snapshot_time=row[1], trigger=row[2],
            model_name=row[3], model_version=row[4], strategy_name=row[5],
            config_json=row[6], evaluation_json=row[7],
            factor_breakdown_json=row[8], today_top_10_json=row[9],
            backtest_last_10_json=row[10], market_regime=row[11],
            reasoning=row[12], created_at=row[13],
        )

    def list_recent(self, limit: int = 10) -> list:
        """查询最近 N 条快照。"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM decision_snapshot ORDER BY snapshot_time DESC LIMIT ?",
                (limit,),
            ).fetchall()
        finally:
            conn.close()
        return [
            {
                "snapshot_id": r[0], "snapshot_time": r[1], "trigger": r[2],
                "model_name": r[3], "model_version": r[4], "strategy_name": r[5],
                "market_regime": r[11], "reasoning": r[12],
            }
            for r in rows
        ]
