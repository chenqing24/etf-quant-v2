"""
portfolio/portfolio.py — 组合管理（v2 portfolio 模块）

用途：组合管理（holdings + rebalance + attribution）。
被谁调用：stock-portfolio skill（组合回测）+ risk 模块（组合风控）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class Holding:
    """单只 ETF 持仓"""
    code: str
    qty: int
    entry_price: float
    entry_date: str
    current_price: Optional[float] = None

    def pnl_pct(self) -> float:
        """盈亏比例"""
        if self.current_price is None or self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price

    def market_value(self) -> float:
        """市值"""
        if self.current_price is None:
            return 0.0
        return self.qty * self.current_price


@dataclass
class Portfolio:
    """组合（v2 portfolio 核心类）"""
    name: str
    holdings: List[Holding] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def total_value(self) -> float:
        """总市值"""
        return sum(h.market_value() for h in self.holdings)

    def total_pnl_pct(self) -> float:
        """总盈亏比例（加权）"""
        if not self.holdings:
            return 0.0
        total_mv = self.total_value()
        if total_mv == 0:
            return 0.0
        weighted_pnl = sum(
            h.pnl_pct() * h.market_value() / total_mv
            for h in self.holdings if h.current_price is not None
        )
        return weighted_pnl

    def add_holding(self, holding: Holding) -> None:
        """添加持仓"""
        self.holdings.append(holding)

    def rebalance(self, target_weights: Dict[str, float]) -> List[Dict]:
        """再平衡（按目标权重）

        Args:
            target_weights: {code: weight}, 权重和应为 1.0

        Returns:
            调整动作列表 [{"code": ..., "action": "buy/sell", "qty": ...}]
        """
        actions = []
        total = self.total_value()
        if total == 0:
            return actions
        for code, weight in target_weights.items():
            target_mv = total * weight
            current_mv = sum(
                h.market_value() for h in self.holdings if h.code == code
            )
            diff_mv = target_mv - current_mv
            # 简化：按当前价算 qty
            h = next((h for h in self.holdings if h.code == code), None)
            if h and h.current_price:
                qty_diff = int(diff_mv / h.current_price)
                if qty_diff != 0:
                    actions.append({
                        "code": code,
                        "action": "buy" if qty_diff > 0 else "sell",
                        "qty": abs(qty_diff),
                    })
        return actions

    def attribution(self) -> Dict[str, float]:
        """归因分析（每只持仓对总盈亏的贡献）"""
        result = {}
        total_mv = self.total_value()
        if total_mv == 0:
            return result
        for h in self.holdings:
            if h.current_price is not None:
                contribution = h.pnl_pct() * h.market_value() / total_mv
                result[h.code] = contribution
        return result
