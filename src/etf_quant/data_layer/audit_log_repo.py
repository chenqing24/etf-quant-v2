"""
data_layer/audit_log_repo.py — audit_log 表 Repository
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AuditLog:
    """审计日志（v1 兼容）。"""

    action: str  # 'state_change'/'record_buy'/'record_sell'/'check_stop'/'migrate'
    code: Optional[str] = None
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    detail: Optional[str] = None
    timestamp: Optional[str] = None  # 自动生成


class AuditLogRepository:
    """audit_log 表 Repository。"""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def insert(self, log: AuditLog) -> int:
        """插入审计日志。"""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "INSERT INTO audit_log (action, code, from_state, to_state, detail) "
                "VALUES (?, ?, ?, ?, ?)",
                (log.action, log.code, log.from_state, log.to_state, log.detail),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def list_by_code(self, code: str, limit: int = 50) -> List[dict]:
        """按 code 查询审计日志。"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE code = ? ORDER BY timestamp DESC LIMIT ?",
                (code, limit),
            ).fetchall()
        finally:
            conn.close()
        return [
            {"id": r[0], "timestamp": r[1], "action": r[2], "code": r[3],
             "from_state": r[4], "to_state": r[5], "detail": r[6]}
            for r in rows
        ]
