"""
alpha/factors/t5_ma5.py — T5 MA5 因子（散户新加，2026-06-21）

用途：
    5 日简单移动平均线（close 的 5 日算术平均）。
    最常用的基础均线指标——散户看趋势的第一道参考。

业界参考（按规则 13）：
    - Murphy 1999《Technical Analysis of the Financial Markets》Ch 6
      "Moving Averages"——MA 是趋势跟踪的最古老指标
    - WorldQuant 101 Alphas 编号 #30 也使用 close 的滚动均值

被谁调用：
    - src/etf_quant/alpha/factors/__init__.py（FACTOR_REGISTRY 注册）
    - src/etf_quant/alpha/registry.py（向后兼容导出）
    - tests/unit/test_factors.py（单测覆盖）
    - skills/quantor-onboard/scripts/run_alpha.py（散户注册流程）

v2 背景：
    Sprint-7 后 27 因子无单独 MA5，散户要求补。
    公式：MA5(t) = mean(close[t-4 : t+1])
    输出：滚动 5 日均值 Series（与 df.index 对齐）

注意事项：
    - 不允许用未来函数（按 L121 教训）
    - 5 日内前 4 行为 NaN，调用方需 fillna(0)（基类默认）
"""
from __future__ import annotations

import pandas as pd

from etf_quant.alpha.factor_base import Factor, FactorCategory


class T5MA5Factor(Factor):
    """T5 MA5：5 日简单移动平均线（散户最基础的趋势指标）。"""

    def __init__(self, window: int = 5, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)
        self.window = window

    @property
    def name(self) -> str:
        return "T5_ma5"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.TREND

    @property
    def description(self) -> str:
        return f"MA{self.window} 简单移动平均线（close 的 {self.window} 日算术平均，散户最常用的趋势指标）"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        ma = close.rolling(window=self.window, min_periods=self.window).mean()
        return ma.rename(self.name)
