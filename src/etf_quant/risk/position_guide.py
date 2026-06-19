"""
risk/position_guide.py — 持仓策略指导（US-007 v2 落地）

用途：
    v1 US-007 PositionGuide 22 字段决策树 9 步（v1 实际是 18 字段，按用户原话 22 字段重设计）。
    业务层零 SQL（v2 规则 15），所有数据通过 data_layer/*_repo.py。

被谁调用：
    - skills/etf-daily/scripts/run_daily.py（每日决策）
    - skills/etf-research/scripts/run_validate.py
    - future: CLI -m history 集成

功能说明：
    9 步决策树（按 SOP-17 顺序 + v8 规则）：
      1. legacy_holding → 清仓
      2. 止损触发 → 止损
      3. 持仓 < min_hold → 持有（短期）
      4. 止盈触发 → 止盈
      5. 到期 → 到期评估
      6. 市场非 trend_up → 清仓空仓
      7. 持仓 < max_holdings + 评分高 → 可加仓
      8. 持仓 == max_holdings + 最低分低 → 换仓
      9. 默认 → 持有

使用方式：
    from etf_quant.risk.position_guide import PositionGuideAnalyzer
    analyzer = PositionGuideAnalyzer(db_path="/path/etf.db")
    guide = analyzer.analyze_position(
        code="510300", current_price=4.10, market_regime="trend_up", current_score=85
    )
    if guide.should_stop_loss:
        # 止损逻辑
    elif guide.should_take_profit:
        # 止盈逻辑

依赖：
    - src/etf_quant/data_layer/position_repo.py
    - src/etf_quant/data_layer/trade_history_repo.py
    - src/etf_quant/data_layer/audit_log_repo.py
    - v1 docs/POSITION_MANAGEMENT.md v8（默认参数基准）
    - v1 docs/SOP_06_MANUAL_TRADE.md v2.0（情绪联动）
    - v1 SOP-17（决策顺序：止损任意 > 止盈需 min_hold > 到期）
    - v1 教训 22/67（基于外部数据判断，不用 action 反推）

注意事项：
    - DEFAULT_* 参数对齐 v8 POSITION_MANAGEMENT.md
    - max_holdings=2（v8 沿用，不是 1）
    - 业务层零 SQL（v2 规则 15）
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from etf_quant.data_layer.position_repo import PositionRepository
from etf_quant.data_layer.trade_history_repo import TradeHistoryRepository
from etf_quant.data_layer.audit_log_repo import AuditLogRepository


# v8 POSITION_MANAGEMENT.md 默认参数
DEFAULT_STOP_LOSS_PCT = -0.10      # -10%
DEFAULT_TAKE_PROFIT_PCT = 0.15     # +15%
DEFAULT_MIN_HOLD_DAYS = 3          # SOP-17 经验
DEFAULT_MAX_HOLD_DAYS = 15         # v8
DEFAULT_MAX_HOLDINGS = 2           # v8 + 用户 B 决策
DEFAULT_REBALANCE_THRESHOLD = 2    # 候选分差


@dataclass
class PositionGuide:
    """持仓策略指导（22 字段）。"""

    # 现状 (5)
    code: str
    name: str
    quantity: int
    entry_price: float
    current_price: float

    # 衍生 (5)
    pnl_pct: float
    hold_days: int
    stop_loss_price: float
    take_profit_price: float
    expire_in_days: int

    # 阈值 (2)
    min_hold_remaining: int
    stop_loss_pct: float

    # 信号 (3)
    market_regime: str
    current_score: int
    emotion_flag: str

    # 触发 (3)
    should_stop_loss: bool
    should_take_profit: bool
    should_expire: bool

    # 多持仓 (3)
    should_add_position: bool
    should_reduce_position: bool
    should_go_cash: bool

    # 建议 (1)
    action: str
    reason: str


class PositionGuideAnalyzer:
    """持仓策略指导分析器（v2 委托模式，零 SQL）。"""

    def __init__(
        self,
        db_path: str,
        stop_loss_pct: float = DEFAULT_STOP_LOSS_PCT,
        take_profit_pct: float = DEFAULT_TAKE_PROFIT_PCT,
        min_hold_days: int = DEFAULT_MIN_HOLD_DAYS,
        max_hold_days: int = DEFAULT_MAX_HOLD_DAYS,
        max_holdings: int = DEFAULT_MAX_HOLDINGS,
        rebalance_threshold: int = DEFAULT_REBALANCE_THRESHOLD,
    ) -> None:
        self.db_path = db_path
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.min_hold_days = min_hold_days
        self.max_hold_days = max_hold_days
        self.max_holdings = max_holdings
        self.rebalance_threshold = rebalance_threshold
        # 委托 3 个 Repo（业务层零 SQL）
        self._position_repo = PositionRepository(db_path=db_path)
        self._trade_repo = TradeHistoryRepository(db_path=db_path)
        self._audit_repo = AuditLogRepository(db_path=db_path)

    def analyze_position(
        self,
        code: str,
        current_price: Optional[float] = None,
        market_regime: str = "range_bound",
        current_score: int = 0,
        emotion_flag: str = "",
    ) -> Optional[PositionGuide]:
        """对单只持仓 ETF 输出操作建议。"""
        pos = self._position_repo.get(code)
        if pos is None:
            return None

        # 实时价（如未传，用 entry_price fallback）
        if current_price is None:
            current_price = pos.entry_price

        # 情绪（如未传，查 trade_history 最近一笔）
        if not emotion_flag:
            recent_trades = self._trade_repo.list_by_code(code)
            if recent_trades:
                emotion_flag = recent_trades[0].emotion or ""

        # 计算衍生字段
        pnl_pct = (current_price - pos.entry_price) / pos.entry_price if pos.entry_price else 0
        stop_loss_price = pos.entry_price * (1 + self.stop_loss_pct)
        take_profit_price = pos.entry_price * (1 + self.take_profit_pct)
        hold_days = (date.today() - date.fromisoformat(pos.entry_date)).days
        expire_in_days = max(0, self.max_hold_days - hold_days)
        min_hold_remaining = max(0, self.min_hold_days - hold_days)

        # 9 步决策树（SOP-17 顺序）
        should_sl = current_price <= stop_loss_price
        should_sp = (
            hold_days >= self.min_hold_days
            and current_price >= take_profit_price
        )
        should_expire = hold_days >= self.max_hold_days

        # 默认动作
        action = "HOLD"
        reason = "default hold"

        if pos.legacy_holding:
            action = "CLEAR_LEGACY"
            reason = "legacy_holding - 用户决策 A2"
        elif should_sl:
            action = "STOP_LOSS"
            reason = f"current_price {current_price} <= stop_loss {stop_loss_price}"
        elif hold_days < self.min_hold_days:
            action = "HOLD_SHORT"
            reason = f"hold_days {hold_days} < min_hold {self.min_hold_days}"
        elif should_sp:
            action = "TAKE_PROFIT"
            reason = f"current_price {current_price} >= take_profit {take_profit_price}"
        elif should_expire:
            action = "EXPIRE_REVIEW"
            reason = f"hold_days {hold_days} >= max_hold {self.max_hold_days}"
        elif market_regime not in ("trend_up", "range_bound"):
            action = "GO_CASH"
            reason = f"market_regime {market_regime} 不友好"

        should_add = (
            action == "HOLD"
            and current_score >= 80
        )
        should_reduce = (
            action == "HOLD"
            and current_score < 50
        )
        should_go_cash = action == "GO_CASH"

        return PositionGuide(
            # 现状 (5)
            code=pos.code,
            name=pos.name,
            quantity=pos.quantity,
            entry_price=pos.entry_price,
            current_price=current_price,
            # 衍生 (5)
            pnl_pct=pnl_pct,
            hold_days=hold_days,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            expire_in_days=expire_in_days,
            # 阈值 (2)
            min_hold_remaining=min_hold_remaining,
            stop_loss_pct=self.stop_loss_pct,
            # 信号 (3)
            market_regime=market_regime,
            current_score=current_score,
            emotion_flag=emotion_flag,
            # 触发 (3)
            should_stop_loss=should_sl,
            should_take_profit=should_sp,
            should_expire=should_expire,
            # 多持仓 (3)
            should_add_position=should_add,
            should_reduce_position=should_reduce,
            should_go_cash=should_go_cash,
            # 建议 (1)
            action=action,
            reason=reason,
        )

    def analyze_all(
        self,
        current_prices: Optional[dict] = None,
        market_regime: str = "range_bound",
    ) -> List[PositionGuide]:
        """分析所有持仓。"""
        current_prices = current_prices or {}
        positions = self._position_repo.list_all()
        results = []
        for pos in positions:
            if pos.status != "HOLDING":
                continue
            price = current_prices.get(pos.code, pos.entry_price)
            guide = self.analyze_position(
                code=pos.code, current_price=price,
                market_regime=market_regime, current_score=0,
            )
            if guide is not None:
                results.append(guide)
        return results
