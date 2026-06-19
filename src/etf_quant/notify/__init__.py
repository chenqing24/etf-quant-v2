"""
notify — 钉钉推送（v2 US-016）

用途：钉钉推送（双通道 notifier + scenario）。
被谁调用：etf-daily skill（每日推送）+ monitor（告警推送）+ execution（信号推送）。
按 v1 notifier.py + dingtalk_sender.py + scenario_adapter.py 适配。
"""
from .dingtalk import DingTalkClient
from .notifier import SignalNotifier, TradeSignal
from .scenario import ScenarioAdapter

__all__ = ["DingTalkClient", "SignalNotifier", "TradeSignal", "ScenarioAdapter"]
