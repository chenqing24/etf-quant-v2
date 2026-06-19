"""
notify/scenario.py — 场景通知器（v2 notify 模块）

用途：场景化通知（buy/sell/daily_report）。
被谁调用：etf-daily skill（每日报告）+ monitor（告警）。
按 v1 scenario_adapter.py 适配。
"""
from __future__ import annotations

from typing import Dict, List
from .notifier import SignalNotifier, TradeSignal
from .dingtalk import DingTalkClient


class ScenarioAdapter:
    """场景通知器（v2 notify）"""

    def __init__(self, notifier: SignalNotifier = None):
        self.notifier = notifier or SignalNotifier()

    def notify_buy(self, code: str, price: float, reason: str) -> bool:
        """通知买入"""
        signal = TradeSignal(
            date=str(__import__("datetime").date.today()),
            code=code, action="buy", price=price, reason=reason,
        )
        return self.notifier.notify_signal(signal)

    def notify_sell(self, code: str, price: float, pnl: float, reason: str) -> bool:
        """通知卖出"""
        signal = TradeSignal(
            date=str(__import__("datetime").date.today()),
            code=code, action="sell", price=price, reason=reason, pnl=pnl,
        )
        return self.notifier.notify_signal(signal)

    def notify_daily_report(self, report: Dict) -> bool:
        """通知每日报告"""
        content = (
            f"📊 ETF 每日报告\n"
            f"决策: {report.get('decision', 'HOLD')}\n"
            f"持仓: {report.get('holdings_count', 0)} 只\n"
            f"市场模式: {report.get('market_mode', 'unknown')}\n"
        )
        if report.get("warnings"):
            content += f"⚠️ 警告: {', '.join(report['warnings'])}\n"
        return self.notifier.dingtalk.send_markdown(
            title="ETF 每日报告",
            content=content,
        )
