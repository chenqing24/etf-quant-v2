"""
etf_quant v2 — 12 模块化 ETF 量化投资策略

按业界标准划分（QuantConnect LEAN / Zipline / BigQuant）：

    5 大核心：data_layer / universe / alpha / portfolio / risk
    3 大支撑：execution / backtest / performance
    4 大辅助：notify / config / monitor / scheduler
    1 工具集：utils

每个模块的 README.md 含详细接口契约。
"""
from __future__ import annotations

__version__ = "2.0.0a1"

__all__ = [
    "data_layer",
    "universe",
    "alpha",
    "portfolio",
    "risk",
    "execution",
    "backtest",
    "performance",
    "notify",
    "config",
    "monitor",
    "scheduler",
    "utils",
]