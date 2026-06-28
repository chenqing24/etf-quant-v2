"""
alpha/factors/sixty_min/h2_volume_breakout.py — H2 60min 量能突破（D-007）

用途：
    量能突破因子，捕捉盘中资金异动信号。
    **不参与实时决策**（按 D-007 5 项隔离原则）。

公式（TA-Lib AD 类似思路 + 短期/长期均值比）：
    short_volume = mean(volume[-5:])
    long_volume = mean(volume[-25:-5])  # 前 20 个 bar（不含最近 5）
    ratio = short_volume / long_volume
    breakout = (ratio - 1)  # 0=无变化，>0=放量，<0=缩量

输出：Series[float]
    > 0 放量（短期均量 > 长期均量）
    < 0 缩量
    0 横盘

业界参考（按规则 13）：
    - TA-Lib AD（Accumulation/Distribution Line）Volume Indicators 章节
      https://ta-lib.org/api/
    - 经典量比指标（同花顺/通达信）

被谁调用：
    - scripts/eval_60min_factors.py（D-007 C5）
    - tests/unit/alpha/sixty_min/test_h2_volume_breakout.py

注意事项：
    - 不允许用未来函数（前 20 个 bar 用作基线）
    - 数据依赖：60min K 线 ≥ 25 个 bar
    - 不参与 daily 决策链
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from etf_quant.alpha.factor_base import Factor, FactorCategory


class H2VolumeBreakoutFactor(Factor):
    """H2 量能突破：短期/长期均量比 - 1."""

    def __init__(
        self,
        short_window: int = 5,
        long_window: int = 20,
        fill_method: str = "zero",
    ):
        super().__init__(fill_method=fill_method)
        self.short_window = short_window
        self.long_window = long_window

    @property
    def name(self) -> str:
        return "H2_volume_breakout"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLUME

    @property
    def description(self) -> str:
        return (
            f"量能突破（短期{self.short_window}/长期{self.long_window}均量比-1，"
            f"TA-Lib AD 类似思路）"
        )

    @property
    def _aliases(self) -> list[str]:
        return ["H2", "VolumeBreakout", "volume_ratio_short", "量能突破", "量比"]

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if "volume" not in df.columns:
            raise ValueError("df 必须包含 volume 列")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("df.index 必须为 DatetimeIndex")

        # 短期均量（最近 5 个 bar）
        short_ma = df["volume"].rolling(window=self.short_window, min_periods=self.short_window).mean()

        # 长期均量（前 20 个 bar，不含最近 5 个）
        long_ma = df["volume"].rolling(
            window=self.short_window + self.long_window,
            min_periods=self.short_window + self.long_window,
        ).mean().shift(self.short_window)

        # 量比 - 1（中心化处理：0=无变化）
        ratio = short_ma / long_ma
        breakout = ratio - 1.0

        return breakout.rename(self.name)