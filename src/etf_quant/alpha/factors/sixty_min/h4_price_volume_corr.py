"""
alpha/factors/sixty_min/h4_price_volume_corr.py — H4 60min 量价相关性（D-007）

用途：
    量价相关性因子，捕捉量价背离信号（Granville 量价八大法则）。
    **不参与实时决策**（按 D-007 5 项隔离原则）。

公式（Granville 1976）：
    在最近 N 个 60min bar 上计算 close 与 volume 的 Spearman 秩相关系数
    Spearman 而非 Pearson：抗异常值（成交量突变）

输出：Series[float]，值域 [-1, 1]
    > 0 量价同向（价升量增 = 健康上涨 / 价跌量增 = 恐慌下跌）
    < 0 量价背离（价升量缩 = 上涨乏力 / 价跌量缩 = 跌势放缓）

业界参考（按规则 13）：
    - Granville, J. (1976). "Granville's New Key to Stock Market Profits"
      量价背离章节：价量同步与背离
    - scipy.stats.spearmanr（Spearman 秩相关）

被谁调用：
    - scripts/eval_60min_factors.py（D-007 C5）
    - tests/unit/alpha/sixty_min/test_h4_price_volume_corr.py

注意事项：
    - 不允许用未来函数
    - 数据依赖：60min K 线 ≥ 20 bar
    - 不参与 daily 决策链
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from etf_quant.alpha.factor_base import Factor, FactorCategory


class H4PriceVolumeCorrFactor(Factor):
    """H4 量价相关性：close 与 volume 在 N bar 的 Spearman 秩相关系数."""

    def __init__(
        self,
        window: int = 20,
        fill_method: str = "zero",
    ):
        super().__init__(fill_method=fill_method)
        self.window = window

    @property
    def name(self) -> str:
        return "H4_price_volume_corr"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLUME  # 量价相关性归类为量能

    @property
    def description(self) -> str:
        return f"量价相关性（最近{self.window}bar close vs volume 的 Spearman 秩相关，Granville 1976）"

    @property
    def _aliases(self) -> list[str]:
        return ["H4", "PriceVolumeCorr", "pv_corr", "量价相关性", "量价背离"]

    def compute(self, df: pd.DataFrame) -> pd.Series:
        if "close" not in df.columns or "volume" not in df.columns:
            raise ValueError("df 必须包含 close 和 volume 列")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("df.index 必须为 DatetimeIndex")

        close = df["close"].astype(float)
        volume = df["volume"].astype(float)

        def rolling_corr(s_close: pd.Series, s_volume: pd.Series) -> float:
            """Spearman 秩相关."""
            if len(s_close) < self.window:
                return np.nan
            if s_close.std() == 0 or s_volume.std() == 0:
                return np.nan
            corr, _ = spearmanr(s_close.values, s_volume.values)
            return corr if not np.isnan(corr) else np.nan

        # 滚动计算
        result = pd.Series(np.nan, index=df.index)
        close_roll = close.rolling(window=self.window, min_periods=self.window)
        volume_roll = volume.rolling(window=self.window, min_periods=self.window)

        for i in range(self.window - 1, len(df)):
            s_close = close.iloc[i - self.window + 1:i + 1]
            s_volume = volume.iloc[i - self.window + 1:i + 1]
            result.iloc[i] = rolling_corr(s_close, s_volume)

        return result.rename(self.name)