"""
alpha/factors/b1_boll.py — B1 布林上轨突破因子

业界参考：Bollinger 1980s, Murphy 1999 Ch 9
v2 README: IC=0.0484, IR=0.99
"""
from __future__ import annotations

import pandas as pd

# v1 继承：v1 indicator 接口
# 这里采用 v2 自实现，避免跨仓 import 串扰
from etf_quant.alpha.factor_base import Factor, FactorCategory


class B1BollUpperFactor(Factor):
    """B1 布林上轨突破：close - 布林上轨（值 > 0 表示突破）。"""

    def __init__(self, window: int = 20, num_std: float = 2.0, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.window = window
        self.num_std = num_std

    @property
    def name(self) -> str:
        return "B1_boll_upper"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLATILITY

    @property
    def description(self) -> str:
        return f"布林上轨突破：close - 布林上轨（{self.window}日±{self.num_std}σ）"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if "close" not in df.columns:
            raise ValueError("df must have 'close' column")
        close = df["close"].astype(float)
        ma = close.rolling(window=self.window, min_periods=self.window).mean()
        std = close.rolling(window=self.window, min_periods=self.window).std(ddof=0)
        upper = ma + self.num_std * std
        return (close - upper).rename(self.name)
