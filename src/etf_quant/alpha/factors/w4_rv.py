"""
alpha/factors/w4_rv.py — W4 波动率变化因子（US-013 唯一新写）

用途：
    v9 唯一稳健因子（OOS/IS=0.90，pass_rate=18%，见 MEMORY.md:738/994）。
    公式：W4_RV(t) = std(close(t-19:t)) / std(close(t-39:t)) - 1
    逻辑：短期波动率 / 长期波动率 - 1
        - W4 > 0：波动率放大（趋势形成 / 恐慌性抛售）→ 不买
        - W4 < 0：波动率收敛（震荡市 / 即将反转）→ 买入信号

被谁调用：
    - src/etf_quant/alpha/registry.py
    - tests/unit/alpha/test_factors.py
    - tests/regression/alpha/test_w4_rv_v9.py（与 v9 OOS/IS=0.90 对比）

功能说明：
    - W4RVFactor: 因子实现
    - 窗口默认：短期 20 日 / 长期 40 日
    - 含最小周期保护（短期 < 长期）
    - 返回值：Series[index], values = std_ratio - 1

使用方式：
    from etf_quant.alpha.factors.w4_rv import W4RVFactor
    factor = W4RVFactor(short_window=20, long_window=40)
    result = factor(df)  # df 含 close 列
    print(result.series, result.metadata)

依赖：
    - pandas: Series 处理
    - numpy: std 计算
    - etf_quant.alpha.factor_base: 因子基类
    - L218 教训（IC/IR 验证）
    - L121 教训（防未来函数）

注意事项：
    - 必须用 t 及之前数据（rolling().std() 天然无未来函数）
    - 短窗口 < 长窗口（默认 20 < 40）
    - 至少需要 long_window + 1 行数据
    - 数据不足时返回 NaN（fillna(0) 在基类完成）

业界参考（按规则 13）：
    - Andersen & Bollerslev 1998 *Answering the Skeptics: Yes, Standard Volatility Models Do
      Provide Accurate Forecasts* (Realized Volatility 基础)
    - Murphy 1999 *Technical Analysis of Financial Markets* Ch 11 (Volatility Ratio)
    - Moreira & Muir 2017 *Overcoming Long-Term Challenges to Value* (Vol Targeting 应用)
    - v9 沉淀：MEMORY.md:738/994 OOS/IS=0.90
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from etf_quant.alpha.factor_base import Factor, FactorCategory


class W4RVFactor(Factor):
    """
    W4 波动率变化因子（Realized Volatility Ratio - 1）。

    Attributes:
        short_window: 短期波动率窗口（默认 20 日）
        long_window: 长期波动率窗口（默认 40 日）
    """

    def __init__(self, short_window: int = 20, long_window: int = 40, fill_method: str = "zero"):
        if short_window >= long_window:
            raise ValueError(
                f"short_window ({short_window}) must be < long_window ({long_window})"
            )
        super().__init__(fill_method=fill_method)
        self.short_window = short_window
        self.long_window = long_window

    @property
    def name(self) -> str:
        return "W4_rv"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.VOLATILITY

    @property
    def description(self) -> str:
        return (
            f"波动率变化：std(close[-{self.short_window}:]) / std(close[-{self.long_window}:]) - 1。"
            f"v9 唯一稳健因子，OOS/IS=0.90"
        )

    def compute(self, df: pd.DataFrame) -> pd.Series:
        """
        计算 W4 RV 因子值。

        Args:
            df: 包含 close 列的 DataFrame

        Returns:
            Series[index]: W4_RV = std_short / std_long - 1
                - 接近 0：波动率稳定
                - > 0：短期波动放大
                - < 0：短期波动收敛（潜在反转买入信号）
        """
        if "close" not in df.columns:
            raise ValueError(f"DataFrame must contain 'close' column, got: {df.columns.tolist()}")

        close = df["close"].astype(float)

        # 滚动标准差（用 ddof=0 保持与业界一致：总体标准差）
        std_short = close.rolling(window=self.short_window, min_periods=self.short_window).std(ddof=0)
        std_long = close.rolling(window=self.long_window, min_periods=self.long_window).std(ddof=0)

        # 比率 - 1：避免长期为 0 时除零
        # 用 np.where 处理 std_long == 0 的情况（返回 NaN，由基类 fill）
        w4 = np.where(
            std_long > 0,
            std_short / std_long - 1.0,
            np.nan,
        )

        return pd.Series(w4, index=df.index, name=self.name)
