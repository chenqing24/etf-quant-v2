"""
alpha/factors/v1_volume.py — V1 放量因子

业界参考：Murphy 1999 Ch 10, Granville 1963
v2 README: IC=0.0369, IR=0.84
"""
from __future__ import annotations

import pandas as pd

from etf_quant.alpha.factor_base import Factor, FactorCategory


class V1VolumeFactor(Factor):
    """V1 放量：当日成交量 / N 日均量 - 1（值 > 0 表示放量）。"""

    def __init__(self, window: int = 5, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.window = window

    @property
    def name(self) -> str:
        return "V1_volume"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLUME

    @property
    def description(self) -> str:
        return f"放量：volume / MA{self.window}(volume) - 1"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns:
            raise ValueError("df must have 'volume' column")
        vol = df["volume"].astype(float)
        avg = vol.rolling(window=self.window, min_periods=self.window).mean()
        return (vol / avg - 1.0).rename(self.name)
