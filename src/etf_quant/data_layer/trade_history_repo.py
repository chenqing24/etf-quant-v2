"""
data_layer/trade_history_repo.py — trade_history 表 Repository

用途：
    v2 封装 trade_history 表所有 SQL（按 Repository 模式 + Data Mapper）。
    v1 tracker.py 散落的 20 处 SQL 集中到 5 个 Repo 类（trade_history/position/
    audit_log/decision_snapshot/etf_pool）。

被谁调用：
    - src/etf_quant/execution/tracker.py（v1 兼容，委托模式）
    - 未来：v2 直接调用

功能说明：
    - 5 标准方法：insert / get / list / update / delete
    - Data Mapper 集中：dataclass ↔ SQL 转换
    - 集中事务管理：每个方法单事务

使用方式：
    from etf_quant.data_layer.trade_history_repo import TradeHistoryRepository
    repo = TradeHistoryRepository(db_path="/path/etf.db")
    trade_id = repo.insert(TradeRecord(...))
    trades = repo.list_by_code("510300")

依赖：
    - sqlite3：直接 SQL（data_layer 豁免规则 15）
    - schema/migrations/004_add_trade_tables.sql（trade_history 表）
    - L238 教训：先读真实 v1 SQL 再写

注意事项：
    - v1 trade_history 31 字段，v2 必须全部支持
    - 业务层（execution/）禁止直接 import 此模块外以外的 SQL
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class TradeRecord:
    """交易记录 dataclass（v1 31 字段 + 兼容）。"""

    date: str
    code: str
    name: str
    action: str  # 'buy' or 'sell'
    price: float
    quantity: int
    amount: float
    reason: Optional[str] = None

    # SOP-06 v2.0 情绪/时段
    emotion: Optional[str] = None  # 'calm'/'fear'/'fomo'/'regret' 等
    session: Optional[str] = None  # 'A'/'B'/'C'/'D'/'E'/'F'

    # SOP-06 v2.0 信号快照
    signal_time: Optional[str] = None
    signal_price: Optional[float] = None
    signal_rsi: Optional[float] = None
    signal_adx: Optional[float] = None
    signal_score: Optional[int] = None

    # 实时快照
    realtime_price: Optional[float] = None
    price_deviation: Optional[float] = None
    rsi_14: Optional[float] = None
    day_change_pct: Optional[float] = None
    score: Optional[int] = None

    # 业绩
    expected_return: Optional[float] = None
    actual_pnl: Optional[float] = None
    note: Optional[str] = None

    # 时间
    trade_time: Optional[str] = None

    # 标记
    is_real: int = 0
    is_paper: int = 0

    # Q-009 决策上下文
    model: Optional[str] = None
    strategy: Optional[str] = None
    evaluation: Optional[str] = None
    snapshot_ref: Optional[str] = None


class TradeHistoryRepository:
    """trade_history 表 Repository（Fowler Repository 模式）。"""

    # v1 真实 31 列（按 schema 004）
    COLUMNS = [
        "date", "code", "name", "action", "price", "quantity", "amount", "reason",
        "expected_return", "actual_pnl", "note",
        "realtime_price", "price_deviation", "rsi_14", "day_change_pct", "score",
        "signal_time", "signal_price", "signal_rsi", "signal_adx", "signal_score",
        "trade_time", "emotion", "session",
        "is_real", "is_paper",
        "model", "strategy", "evaluation", "snapshot_ref",
    ]

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        """获取 SQLite 连接（WAL 模式）。"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def insert(self, trade: TradeRecord) -> int:
        """插入交易记录，返回 trade_id。"""
        values = asdict(trade)
        # 只插入 COLUMNS 定义的字段
        placeholders = ",".join(["?"] * len(self.COLUMNS))
        cols = ",".join(self.COLUMNS)

        conn = self._get_conn()
        try:
            cursor = conn.execute(
                f"INSERT INTO trade_history ({cols}) VALUES ({placeholders})",
                tuple(values[c] for c in self.COLUMNS),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def list_by_code(self, code: str) -> List[TradeRecord]:
        """查询指定 ETF 的所有交易记录。"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM trade_history WHERE code = ? ORDER BY date DESC",
                (code,),
            ).fetchall()
        finally:
            conn.close()
        return [self._row_to_record(r) for r in rows]

    def list_all(self, limit: Optional[int] = None) -> List[TradeRecord]:
        """查询所有交易记录。"""
        conn = self._get_conn()
        try:
            sql = "SELECT * FROM trade_history ORDER BY date DESC"
            if limit:
                sql += f" LIMIT {int(limit)}"
            rows = conn.execute(sql).fetchall()
        finally:
            conn.close()
        return [self._row_to_record(r) for r in rows]

    def get(self, trade_id: int) -> Optional[TradeRecord]:
        """按 ID 查询单条记录。"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM trade_history WHERE id = ?", (trade_id,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return self._row_to_record(row)

    def delete(self, trade_id: int) -> bool:
        """删除单条记录（谨慎使用）。"""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM trade_history WHERE id = ?", (trade_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def _row_to_record(self, row: tuple) -> TradeRecord:
        """DB 行 → dataclass 转换（Data Mapper）。

        v1 trade_history 真实列顺序（按 schema 004）：
        [0]id [1-8]date/code/name/action/price/quantity/amount/reason
        [9-10]emotion/session
        [11-15]signal_time/signal_price/signal_rsi/signal_adx/signal_score
        [16-20]realtime_price/price_deviation/rsi_14/day_change_pct/score
        [21-24]expected_return/actual_pnl/note/trade_time
        [25-26]is_real/is_paper
        [27-30]model/strategy/evaluation/snapshot_ref
        """
        return TradeRecord(
            # [1-8] 基础
            date=row[1], code=row[2], name=row[3], action=row[4],
            price=row[5], quantity=row[6], amount=row[7], reason=row[8],
            # [9-10] 情绪/时段
            emotion=row[9], session=row[10],
            # [11-15] 信号快照
            signal_time=row[11], signal_price=row[12],
            signal_rsi=row[13], signal_adx=row[14], signal_score=row[15],
            # [16-20] 实时快照
            realtime_price=row[16], price_deviation=row[17],
            rsi_14=row[18], day_change_pct=row[19], score=row[20],
            # [21-24] 业绩
            expected_return=row[21], actual_pnl=row[22], note=row[23], trade_time=row[24],
            # [25-26] 标记
            is_real=row[25] or 0, is_paper=row[26] or 0,
            # [27-30] Q-009 决策上下文
            model=row[27], strategy=row[28], evaluation=row[29], snapshot_ref=row[30],
        )
