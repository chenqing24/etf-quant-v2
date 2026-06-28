"""
alpha/factors/t6_dma.py — T6 DMA 因子（D-013.1 新增）

用途：
    DMA（Difference of Moving Averages）平行线差，趋势类因子。
    用于识别趋势**转折点**（不是稳态趋势），对标 trend_up 市场状态。

公式（用户 2026-06-25 23:02 偏好定义）：
    N1=10, N2=50, M=10
    DDD = MA(close, N1) - MA(close, N2)    # 短期均线差
    AMA = MA(DDD, M)                        # DDD 的 M 日平滑
    DMA = (DDD - 2 * AMA) / close          # 标准化（除以价格便于跨 ETF 比较）

输出：Series[float]
    - DDD 由负转正 = 多头转折信号
    - DDD 由正转负 = 空头转折信号
    - 稳态趋势下 DDD 趋近常数（DMA 不是"趋势强度"指标，是"转折点"指标）

注意（D-013.1 设计复盘发现）：
    DMA = DDD - 2*AMA，稳态下恒为负（因为 AMA ≈ DDD，所以 DMA ≈ -DDD）。
    在 trend_up 加权中，DMA 应配合其他趋势因子使用，不宜单独高权重。

业界参考（按规则 13）：
    - 经典 DMA 指标（Parallel Lines Difference）
    - Murphy 1999《Technical Analysis of the Financial Markets》Ch 8
    - WorldQuant 101 Alphas 趋势类因子注册模式

被谁调用：
    - src/etf_quant/alpha/factors/__init__.py（FACTOR_REGISTRY 注册）
    - tests/unit/alpha/test_dma.py（单测覆盖）

v2 背景（D-013.1）：
    D-013 Sprint-8 daily 横截面打分暴露"宣称 8 因子实际跑 6 因子"。
    DMA + FIB（MA 排列）补齐 T 类趋势因子。

注意事项：
    - 不允许用未来函数（按 L121 教训）
    - 前 49 行 NaN（10 + 50 - 1 滚动窗口），调用方需 fillna(0)
    - 价格标准化保证跨 ETF 可比
"""
from __future__ import annotations

import pandas as pd

from etf_quant.alpha.factor_base import Factor, FactorCategory


class T6DMAFactor(Factor):
    """T6 DMA：平行线差（DDD=MA10-MA50, AMA=MA(DDD,10), 输出 DDD-2*AMA）。"""

    def __init__(
        self,
        n1: int = 10,
        n2: int = 50,
        m: int = 10,
        fill_method: str = "zero",
    ):
        super().__init__(fill_method=fill_method)
        self.n1 = n1
        self.n2 = n2
        self.m = m

    @property
    def name(self) -> str:
        return "T6_dma"

    @property
    def category(self) -> FactorCategory:
        return FactorCategory.TREND

    @property
    def description(self) -> str:
        return (
            f"DMA 平行线差（DDD=MA{self.n1}-MA{self.n2}, "
            f"AMA=MA(DDD,{self.m}), 输出 (DDD-2*AMA)/close 价格标准化）"
        )

    @property
    def _aliases(self) -> list[str]:
        """US-001 业界别名（按规则 28 必填）."""
        return ["DMA", "dma", "Difference of Moving Averages"]

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        ma_short = close.rolling(window=self.n1, min_periods=self.n1).mean()
        ma_long = close.rolling(window=self.n2, min_periods=self.n2).mean()
        ddd = ma_short - ma_long
        ama = ddd.rolling(window=self.m, min_periods=self.m).mean()
        dma = (ddd - 2 * ama) / close
        return dma.rename(self.name)
