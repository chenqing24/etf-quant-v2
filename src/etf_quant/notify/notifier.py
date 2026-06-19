"""
notify/notifier.py — 信号通知器（v2 notify 模块）

用途：交易信号通知（buy/sell + 警告）。
被谁调用：execution 模块（trade signal）+ scenario.py（场景通知）。
按 v1 notify/notifier.py 适配。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .dingtalk import DingTalkClient


@dataclass
class TradeSignal:
    """交易信号"""
    date: str
    code: str
    action: str  # 'buy' or 'sell'
    price: float
    reason: str
    score: float = 0.0
    pnl: float = 0.0  # 盈亏比例


class SignalNotifier:
    """信号通知器（v2）"""

    def __init__(self, dingtalk: Optional[DingTalkClient] = None):
        self.dingtalk = dingtalk or DingTalkClient()
        self.signals: List[TradeSignal] = []

    def notify_signal(self, signal: TradeSignal) -> bool:
        """通知单个信号"""
        self.signals.append(signal)
        message = self._format(signal)
        return self.dingtalk.send_text(message)

    def notify_warning(self, warning: str) -> bool:
        """通知告警"""
        message = f"⚠️ 警告：{warning}"
        return self.dingtalk.send_text(message)

    def _format(self, signal: TradeSignal) -> str:
        """格式化信号"""
        emoji = "🟢" if signal.action == "buy" else "🔴"
        return (
            f"{emoji} {signal.action.upper()} {signal.code}\n"
            f"价格: ¥{signal.price:.2f}\n"
            f"理由: {signal.reason}\n"
            f"评分: {signal.score:.2f}\n"
            f"时间: {signal.date}"
        )
