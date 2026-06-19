"""
data_layer/position_repo.py — positions 表 Repository

按 EXECUTION_REFACTOR_DESIGN.md 业界最佳实践（Repository 模式 + Data Mapper）。
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Position:
    """持仓 dataclass（v1 兼容）。"""

    code: str
    name: str
    entry_date: str
    entry_price: float
    quantity: int
    current_price: float = 0
    pnl_pct: float = 0
    hold_days: int = 0
    status: str = "EMPTY"
    score: int = 0
    is_real: int = 0
    legacy_holding: int = 0
    is_reference: int = 0


class PositionRepository:
    """positions 表 Repository。"""

    COLUMNS = [
        "code", "name", "entry_date", "entry_price", "quantity",
        "current_price", "pnl_pct", "hold_days", "status", "score",
        "is_real", "legacy_holding", "is_reference",
    ]

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def insert(self, pos: Position) -> None:
        """插入持仓（code PRIMARY KEY，重复会 REPLACE）。"""
        placeholders = ",".join(["?"] * len(self.COLUMNS))
        cols = ",".join(self.COLUMNS)
        values = tuple(getattr(pos, c) for c in self.COLUMNS)

        conn = self._get_conn()
        try:
            conn.execute(
                f"INSERT OR REPLACE INTO positions ({cols}) VALUES ({placeholders})",
                values,
            )
            conn.commit()
        finally:
            conn.close()

    def get(self, code: str) -> Optional[Position]:
        """按 code 查询单条持仓。"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM positions WHERE code = ?", (code,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return self._row_to_position(row)

    def list_all(self) -> List[Position]:
        """查询所有持仓。"""
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM positions").fetchall()
        finally:
            conn.close()
        return [self._row_to_position(r) for r in rows]

    def list_by_status(self, status: str) -> List[Position]:
        """按 status 过滤。"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM positions WHERE status = ?", (status,),
            ).fetchall()
        finally:
            conn.close()
        return [self._row_to_position(r) for r in rows]

    def delete(self, code: str) -> bool:
        """删除持仓。"""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM positions WHERE code = ?", (code,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def _row_to_position(self, row: tuple) -> Position:
        """DB 行 → dataclass 转换。

        positions 列顺序（按 schema 004）：
        [0]code [1]name [2]entry_date [3]entry_price [4]quantity
        [5]current_price [6]pnl_pct [7]hold_days [8]status [9]score
        [10]is_real [11]legacy_holding [12]is_reference
        """
        return Position(
            code=row[0], name=row[1], entry_date=row[2], entry_price=row[3],
            quantity=row[4], current_price=row[5] or 0, pnl_pct=row[6] or 0,
            hold_days=row[7] or 0, status=row[8] or "EMPTY", score=row[9] or 0,
            is_real=row[10] or 0, legacy_holding=row[11] or 0,
            is_reference=row[12] or 0,
        )
