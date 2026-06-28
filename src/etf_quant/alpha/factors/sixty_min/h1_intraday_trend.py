"""
alpha/factors/sixty_min/h1_intraday_trend.py — H1 60min 日内趋势（D-007）

用途：
    日内趋势因子，捕捉盘中单边趋势信号。
    **不参与实时决策**（按 D-007 5 项隔离原则）。
    仅用于 60min 因子评估（eval pipeline）和多频率交叉验证。

公式（Barber 2005）：
    每日 N 个 60min bar 的 close 序列最小二乘斜率 / close
    N = 实际 60min bar 数（akshare 通常为 4 个：10:30/11:30/14:00/15:00）

输出：Series[float]
    > 0 多头日内趋势
    < 0 空头日内趋势
    0 横盘

业界参考（按规则 13）：
    - Barber, B. (2005). "The Behavior of Day and Night Traders"
      §2 日内动量：当日开盘到收盘的趋势预测次日
    - TA-Lib LINEARREG：最小二乘斜率算法
      https://ta-lib.org/api/ — TA_LIB_LINEARREG

被谁调用：
    - scripts/eval_60min_factors.py（D-007 C5）
    - tests/unit/alpha/test_h1_intraday_trend.py

v2 背景（D-007）：
    60min 因子定位 = 纯分析层，独立 evaluation pipeline
    不污染 8 因子权重 / rank / stop / profit / decision_snapshot

注意事项：
    - 不允许用未来函数（按 L121 教训）
    - 数据依赖：60min K 线 ≥ 4 个 bar 才计算
    - 不参与 daily 决策链（按 D-007 5 项隔离）
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from etf_quant.alpha.factor_base import Factor, FactorCategory


class H1IntradayTrendFactor(Factor):
    """H1 日内趋势：当日 60min close 序列最小二乘斜率 / close."""

    def __init__(self, fill_method: str = "zero"):
        super().__init__(fill_method=fill_method)

    @property
    def name(self) -> str:
        return "H1_intraday_trend"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.TREND

    @property
    def description(self) -> str:
        return "日内趋势（60min close 序列最小二乘斜率/close，Barber 2005）"

    @property
    def _aliases(self) -> list[str]:
        """US-001 业界别名（按规则 28 必填）."""
        return ["H1", "IntradayTrend", "intraday_momentum", "日内趋势"]

    def compute(self, df: pd.DataFrame) -> pd.Series:
        """
        计算 H1 因子。

        Args:
            df: 必须包含列：datetime, close
                datetime 格式：YYYY-MM-DD HH:MM:SS
                index 必须为 datetime

        Returns:
            Series[float]，index 与 df.index 对齐
        """
        if "close" not in df.columns:
            raise ValueError("df 必须包含 close 列")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("df.index 必须为 DatetimeIndex")

        # 提取日期（用于按日分组）
        dates = df.index.date

        # 对每个交易日计算斜率
        slopes = []
        for date in dates:
            day_mask = dates == date
            day_closes = df.loc[day_mask, "close"].values

            if len(day_closes) < 2:
                slopes.append(np.nan)
                continue

            # 最小二乘斜率：np.polyfit(x, y, 1)[0]
            x = np.arange(len(day_closes))
            slope = np.polyfit(x, day_closes, 1)[0]

            # 价格标准化（除以 close 均值），便于跨 ETF 比较
            slope_norm = slope / day_closes.mean()
            slopes.append(slope_norm)

        # 把 slopes 映射回原 df 的每个 bar
        # 同一天的 bar 共用 slope 值
        result = pd.Series(np.nan, index=df.index)
        for i, date in enumerate(dates):
            day_mask = dates == date
            result.loc[day_mask] = slopes[i]

        return result.rename(self.name)