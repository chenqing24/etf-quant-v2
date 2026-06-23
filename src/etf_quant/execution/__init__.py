"""
etf_quant/execution — 交易执行模块

用途：订单跟踪 + 滑点记录 + 成交回报处理。
被谁调用：etf-daily skill / stock-portfolio skill / execution_repo。

子模块：
    - tracker: TradeTracker（订单跟踪 + 滑点记录）

入口示例：
    from etf_quant.execution import TradeTracker
    tracker = TradeTracker(db_path="/path/etf.db")
    tracker.record_trade(...)
"""
from etf_quant.execution.tracker import TradeTracker

__all__ = ["TradeTracker"]
