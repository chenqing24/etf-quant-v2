"""
alpha/factors/t1_macd.py — T1 MACD 红柱因子

业界参考：Appel 1970s MACD, Murphy 1999 Ch 12
v2 README: IC=0.0423, IR=1.44（最高 IR 的继承因子）
"""
from __future__ import annotations

import pandas as pd

from etf_quant.alpha.factor_base import Factor, FactorCategory


class T1MACDbarFactor(Factor):
    """T1 MACD 红柱：DIF - DEA > 0 时为红柱（值本身 = 柱高度）。"""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.fast = fast
        self.slow = slow
        self.signal = signal

    @property
    def name(self) -> str:
        return "T1_macd_bar"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.TREND

    @property
    def description(self) -> str:
        return f"MACD 红柱：(EMA{self.fast} - EMA{self.slow}) - EMA_signal({self.signal})（v9 IC=0.0423, IR=1.44）"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        ema_fast = close.ewm(span=self.fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=self.signal, adjust=False).mean()
        bar = dif - dea
        return bar.rename(self.name)
