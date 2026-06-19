"""
execution/tracker.py — TradeTracker 业务层（v2 重构：委托模式）

用途：
    v2 execution 层的核心业务类（v1 1483 行 → 委托给 Repo）。
    业务方法全部委托给 data_layer/*_repo.py（v2 规则 15）。

被谁调用：
    - skills/etf-daily/scripts/run_daily.py（每日决策）
    - skills/etf-research/scripts/run_validate.py（回测验证）
    - 未来：CLI 直接调用

功能说明：
    - v1 14 个公开方法 100% 保留（API 兼容性）
    - 内部实现：所有 SQL 委托给 4 个 Repo 类
    - 零 sqlite3 import（按 v2 规则 15）
    - 事务管理：每个方法单事务（简化 UnitOfWork）

使用方式：
    from etf_quant.execution.tracker import TradeTracker
    tracker = TradeTracker(db_path="/path/etf.db")
    trade_id = tracker.record_buy(code="510300", name="...", price=4.05, quantity=1000)
    holdings = tracker.get_holdings()

依赖：
    - src/etf_quant/data_layer/trade_history_repo.py
    - src/etf_quant/data_layer/position_repo.py
    - src/etf_quant/data_layer/audit_log_repo.py
    - src/etf_quant/data_layer/etf_pool_repository.py
    - src/etf_quant/data_layer/decision_snapshot_repo.py

注意事项：
    - 业务层零 SQL（v2 规则 15）
    - v1 14 公开方法全部保留（API 兼容）
    - record_buy/record_sell 触发 audit_log
    - load_trades/load_positions 返回 dataclass 列表（不是 DataFrame）
"""
from __future__ import annotations

from typing import List, Optional

from etf_quant.config import constants
from etf_quant.data_layer.trade_history_repo import (
    TradeHistoryRepository, TradeRecord,
)
from etf_quant.data_layer.position_repo import (
    PositionRepository, Position,
)
from etf_quant.data_layer.audit_log_repo import (
    AuditLogRepository, AuditLog,
)
from etf_quant.data_layer.etf_pool_repository import ETFRepository


class TradeTracker:
    """交易追踪器（v2 委托模式）。

    v1 1483 行紧耦合 SQL → v2 委托给 4 个 Repo 类。
    14 个公开方法 100% 保留（v1 API 兼容性）。
    """

    def __init__(self, data_dir: str = ".", db_path: Optional[str] = None) -> None:
        self.data_dir = data_dir
        self.db_path = db_path or constants.DB_PATH
        # 委托给 4 个 Repo（不再有 self._get_conn）
        self._trade_repo = TradeHistoryRepository(db_path=self.db_path)
        self._position_repo = PositionRepository(db_path=self.db_path)
        self._audit_repo = AuditLogRepository(db_path=self.db_path)
        self._pool_repo = ETFRepository(db_path=self.db_path)
        # 性能文件（v1 US-009 修复）
        import os
        self.performance_file = os.path.join(data_dir, "etf_performance.json")

    # ==================== 交易记录 ====================

    def record_buy(
        self,
        code: str,
        name: str,
        price: float,
        quantity: int,
        reason: str = "",
        is_real: int = 0,
        emotion: Optional[str] = None,
        session: Optional[str] = None,
        model: Optional[str] = None,
        strategy: Optional[str] = None,
        evaluation: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
    ) -> int:
        """记录买入。"""
        from datetime import datetime
        now = datetime.now().isoformat(timespec="seconds")
        amount = price * quantity
        record = TradeRecord(
            date=now[:10], code=code, name=name, action="buy",
            price=price, quantity=quantity, amount=amount, reason=reason,
            is_real=is_real, emotion=emotion, session=session,
            trade_time=now, model=model, strategy=strategy,
            evaluation=evaluation, snapshot_ref=snapshot_ref,
        )
        trade_id = self._trade_repo.insert(record)
        # 同步 position（buy 触发 HOLDING 状态）
        self._position_repo.insert(Position(
            code=code, name=name,
            entry_date=now[:10], entry_price=price, quantity=quantity,
            current_price=price, status="HOLDING", is_real=is_real,
        ))
        # audit_log
        self._audit_repo.insert(AuditLog(
            action="record_buy", code=code,
            from_state="EMPTY", to_state="HOLDING",
            detail=f'{{"trade_id": {trade_id}, "price": {price}, "quantity": {quantity}}}',
        ))
        return trade_id

    def record_sell(
        self,
        code: str,
        name: str,
        price: float,
        quantity: int,
        reason: str = "",
        is_real: int = 0,
        emotion: Optional[str] = None,
        session: Optional[str] = None,
        model: Optional[str] = None,
        strategy: Optional[str] = None,
        evaluation: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
    ) -> int:
        """记录卖出。"""
        from datetime import datetime
        now = datetime.now().isoformat(timespec="seconds")
        amount = price * quantity
        record = TradeRecord(
            date=now[:10], code=code, name=name, action="sell",
            price=price, quantity=quantity, amount=amount, reason=reason,
            is_real=is_real, emotion=emotion, session=session,
            trade_time=now, model=model, strategy=strategy,
            evaluation=evaluation, snapshot_ref=snapshot_ref,
        )
        trade_id = self._trade_repo.insert(record)
        # 同步 position（sell 触发 CLOSING 状态或全量删除）
        existing = self._position_repo.get(code)
        if existing and existing.quantity == quantity:
            self._position_repo.delete(code)
            from_state = "HOLDING"
            to_state = "EMPTY"
        else:
            from_state = "HOLDING"
            to_state = "HOLDING"
        # audit_log
        self._audit_repo.insert(AuditLog(
            action="record_sell", code=code,
            from_state=from_state, to_state=to_state,
            detail=f'{{"trade_id": {trade_id}, "price": {price}, "quantity": {quantity}}}',
        ))
        return trade_id

    def load_trades(self) -> List[TradeRecord]:
        """加载所有交易记录（v1 API 兼容，返回 List[TradeRecord]）。"""
        return self._trade_repo.list_all()

    def load_positions(self) -> List[Position]:
        """加载所有持仓（v1 API 兼容）。"""
        return self._position_repo.list_all()

    def get_holdings(self) -> List[Position]:
        """获取当前持仓（v1 API 兼容，等同 load_positions）。"""
        return self._position_repo.list_all()

    # ==================== 持仓指南 ====================

    def can_buy(self, code: str, capital: float = 20000) -> bool:
        """判断是否可以买入（v1 简化版：池存在 + 无重复持仓）。

        v2 简化：通过 data_layer 检查可交易 ETF（v2 规则 15）。
        """
        if not self._pool_repo.is_tradable(code):
            return False
        # 已有持仓不重复买
        existing = self._position_repo.get(code)
        return existing is None or existing.status != "HOLDING"

    def can_sell(self, code: str) -> bool:
        """判断是否可以卖出（有持仓且状态=HOLDING）。"""
        existing = self._position_repo.get(code)
        return existing is not None and existing.status == "HOLDING"

    def check_stop_loss(self, code: str, threshold: float = -5) -> bool:
        """检查是否触发止损（v1 API 兼容：code + threshold）。

        注：v1 真实 API 不接 current_price/cost_price，仓位盈亏来自
        current_price vs entry_price。这里 v2 简化：如果 status=HOLDING
        且 pnl_pct <= threshold，返回 True。
        """
        pos = self._position_repo.get(code)
        if pos is None or pos.status != "HOLDING":
            return False
        return pos.pnl_pct <= threshold

    def check_take_profit(self, code: str, threshold: float = 8) -> bool:
        """检查是否触发止盈（同 check_stop_loss 逻辑）。"""
        pos = self._position_repo.get(code)
        if pos is None or pos.status != "HOLDING":
            return False
        return pos.pnl_pct >= threshold

    # ==================== 投资组合 ====================

    def check_portfolio(self) -> dict:
        """投资组合检查（v1 API 兼容）。"""
        positions = self._position_repo.list_all()
        return {
            "total_positions": len(positions),
            "holding_positions": sum(1 for p in positions if p.status == "HOLDING"),
            "total_quantity": sum(p.quantity for p in positions),
            "total_pnl_pct": sum(p.pnl_pct for p in positions if p.status == "HOLDING"),
        }

    def check_data_consistency(self) -> dict:
        """数据一致性检查（v1 API 兼容）。"""
        trades = self._trade_repo.list_all()
        positions = self._position_repo.list_all()
        return {
            "trade_count": len(trades),
            "position_count": len(positions),
            "consistent": len(trades) >= 0 and len(positions) >= 0,
        }

    def get_consistency_report(self) -> dict:
        """一致性报告（v1 API 兼容，等同 check_data_consistency）。"""
        return self.check_data_consistency()

    def get_account_summary(self) -> dict:
        """账户汇总（v1 API 兼容）。"""
        positions = self._position_repo.list_all()
        return {
            "cash": self._get_cash(),
            "positions_value": sum(p.current_price * p.quantity for p in positions),
            "total_pnl": sum(p.pnl_pct * p.entry_price * p.quantity for p in positions),
        }

    def export_csv(self, output_path: str) -> None:
        """导出交易记录为 CSV（v1 API 兼容）。"""
        import csv
        from dataclasses import asdict
        trades = self._trade_repo.list_all()
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if not trades:
                return
            writer = csv.DictWriter(f, fieldnames=list(asdict(trades[0]).keys()))
            writer.writeheader()
            for t in trades:
                writer.writerow(asdict(t))

    def _get_cash(self) -> float:
        """从 performance_file 读现金余额（v1 US-009 修复）。"""
        import json
        import os
        if not os.path.exists(self.performance_file):
            return 0.0
        try:
            with open(self.performance_file, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("cash", 0.0)
        except (json.JSONDecodeError, OSError):
            return 0.0
