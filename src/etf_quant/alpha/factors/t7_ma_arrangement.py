"""
alpha/factors/t7_ma_arrangement.py — T7 MA 排列因子（D-013.1 新增）

用途：
    均线排列（MA Arrangement），趋势类因子。
    输出三值：+1 多头 / 0 纠缠 / -1 空头。
    比 T2_ma_bull（0/1）提供更细粒度的趋势方向。

公式：
    bull = MA5 > MA10 > MA20 > MA60
    bear = MA5 < MA10 < MA20 < MA60
    arrangement = +1 if bull, -1 if bear, else 0

输出：Series[int]，值域 {-1, 0, +1}

边界处理（按规则 11 + J. Murphy Ch 8）：
    严格不等号 > 和 <（相等算纠缠）

与 T2_ma_bull 关系：
    T2 只输出 0/1（多头/不是多头），保留现有行为（向后兼容）
    T7 输出 -1/0/1，提供更细粒度
    两者并存不冲突

aliases: FIB / fib / MA_alignment / 均线排列（规则 28）

业界参考（按规则 13）：
    - J. Murphy 1999《Technical Analysis of the Financial Markets》Ch 8
      "Moving Averages"——MA 排列是经典趋势识别方法
    - WorldQuant 101 Alphas 趋势类因子注册模式

被谁调用：
    - src/etf_quant/alpha/factors/__init__.py（FACTOR_REGISTRY 注册）
    - tests/unit/alpha/test_ma_arrangement.py（单测覆盖）

v2 背景（D-013.1）：
    D-013 Sprint-8 daily 横截面打分暴露"宣称 8 因子实际跑 6 因子"。
    DMA（T6）+ MA 排列（T7）补齐 T 类趋势因子。

注意事项：
    - 不允许用未来函数（按 L121 教训）
    - 前 59 行 NaN（MA60 滚动 60 行），调用方需 fillna(0)
    - 输出 int 类型，scoring 用 scipy.stats.rankdata 转 float 兼容
"""
from __future__ import annotations

import pandas as pd

from etf_quant.alpha.factor_base import Factor, FactorCategory


class T7MAArrangementFactor(Factor):
    """T7 MA 排列：+1 多头 / 0 纠缠 / -1 空头（FIB 别名）。"""

    def __init__(self, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)

    @property
    def name(self) -> str:
        return "T7_ma_arrangement"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.TREND

    @property
    def description(self) -> str:
        return "均线排列（MA5/10/20/60）：+1 多头排列 / 0 纠缠 / -1 空头排列"

    @property
    def _aliases(self) -> list[str]:
        """US-001 业界别名（按规则 28 必填）."""
        return ["FIB", "fib", "MA_alignment", "均线排列"]

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        ma5 = close.rolling(5, min_periods=5).mean()
        ma10 = close.rolling(10, min_periods=10).mean()
        ma20 = close.rolling(20, min_periods=20).mean()
        ma60 = close.rolling(60, min_periods=60).mean()

        # 严格不等号（相等算纠缠）
        bull = (ma5 > ma10) & (ma10 > ma20) & (ma20 > ma60)
        bear = (ma5 < ma10) & (ma10 < ma20) & (ma20 < ma60)

        result = pd.Series(0, index=df.index, dtype=int)  # 默认纠缠
        result[bull] = 1
        result[bear] = -1
        return result.rename(self.name)
