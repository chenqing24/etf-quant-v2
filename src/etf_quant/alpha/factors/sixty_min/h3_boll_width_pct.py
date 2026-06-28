"""
alpha/factors/sixty_min/h3_boll_width_pct.py — H3 60min 布林带宽度百分位（D-007）

用途：
    布林带宽度百分位因子，捕捉波动率蓄势信号（变盘前兆）。
    **不参与实时决策**（按 D-007 5 项隔离原则）。

公式（Bollinger 2001 Ch 5 "BandWidth"）：
    boll_mid = MA(close, 20)
    boll_std = STD(close, 20)
    boll_upper = boll_mid + 2 * boll_std
    boll_lower = boll_mid - 2 * boll_std
    boll_width = (boll_upper - boll_lower) / boll_mid  # 归一化
    boll_width_pct = boll_width 在过去 252 个 bar 的百分位排名

输出：Series[float]，值域 [0, 1]
    0 = 当前带宽是过去一年最低（蓄势极值）
    1 = 当前带宽是过去一年最高（波动极值）
    0.5 = 中位数

业界参考（按规则 13）：
    - Bollinger, J. (2001). "Bollinger on Bollinger Bands" Ch 5 BandWidth
    - TA-Lib BBANDS Overlap Indicators 章节
      https://ta-lib.org/api/

被谁调用：
    - scripts/eval_60min_factors.py（D-007 C5）
    - tests/unit/alpha/sixty_min/test_h3_boll_width_pct.py

注意事项：
    - 不允许用未来函数
    - 数据依赖：60min K 线 ≥ 20 bar（布林）+ 252 bar（百分位历史）= 272 bar
    - 不参与 daily 决策链
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from etf_quant.alpha.factor_base import Factor, FactorCategory


class H3BollWidthPctFactor(Factor):
    """H3 布林带宽度百分位：当前带宽在过去 N bar 的百分位."""

    def __init__(
        self,
        boll_window: int = 20,
        boll_std: float = 2.0,
        percentile_window: int = 252,
        fill_method: str = "zero",
    ):
        super().__init__(fill_method=fill_method)
        self.boll_window = boll_window
        self.boll_std = boll_std
        self.percentile_window = percentile_window

    @property
    def name(self) -> str:
        return "H3_boll_width_pct"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLATILITY

    @property
    def description(self) -> str:
        return (
            f"布林带宽度百分位（{self.boll_window} bar 布林宽度在过去 "
            f"{self.percentile_window} bar 的百分位，Bollinger 2001 Ch 5）"
        )

    @property
    def _aliases(self) -> list[str]:
        return ["H3", "BollWidthPct", "boll_bandwidth", "布林带宽百分位", "BBW"]

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if "close" not in df.columns:
            raise ValueError("df 必须包含 close 列")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("df.index 必须为 DatetimeIndex")

        # 布林带
        close = df["close"].astype(float)
        boll_mid = close.rolling(window=self.boll_window, min_periods=self.boll_window).mean()
        boll_std_val = close.rolling(window=self.boll_window, min_periods=self.boll_window).std()
        boll_width = (2 * self.boll_std * boll_std_val) / boll_mid  # 归一化带宽

        # 滚动百分位：用 rolling + rankdata 计算
        def rolling_rank_pct(s: pd.Series) -> float:
            """计算 s 最后一个值在 s 中的百分位排名."""
            valid = s.dropna()
            if len(valid) < 10:
                return np.nan
            current = valid.iloc[-1]
            rank = (valid < current).sum() / len(valid)
            return rank

        result = boll_width.rolling(
            window=self.percentile_window,
            min_periods=10,
        ).apply(rolling_rank_pct, raw=False)

        return result.rename(self.name)