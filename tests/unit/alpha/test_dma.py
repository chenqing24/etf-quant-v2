"""
tests/unit/alpha/test_dma.py — T6 DMA 因子单测（D-013.1）

按规则 11（先测试再交付）+ 规则 5.1（关键路径覆盖）。

总计：8 测试

注意：
    基类默认 fill_method="zero" 会把 NaN 填 0（业务上让 scoring 不出 NaN）。
    所以测试时用 fill_method="drop" 才能检测 NaN。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_quant.alpha.factor_base import FactorCategory
from etf_quant.alpha.factors.t6_dma import T6DMAFactor


def make_df(n: int = 200, trend: str = "up") -> pd.DataFrame:
    """构造测试用 OHLCV 数据（带转折点的趋势）.

    前 min(50, n//2) 日横盘 + 后 n - 前段 日趋势。
    让 DDD/AMA 在转折后有明显变化（否则稳态下 DDD 恒定）。
    """
    np.random.seed(42)
    flat_len = min(50, n // 2)
    trend_len = n - flat_len
    if trend == "up":
        flat = np.full(flat_len, 100.0)
        up = np.arange(trend_len) * 2.0
        close = np.concatenate([flat, up]) + np.random.randn(n) * 0.1
    elif trend == "down":
        flat = np.full(flat_len, 200.0)
        down = np.arange(trend_len) * -2.0
        close = np.concatenate([flat, down]) + np.random.randn(n) * 0.1
    else:
        close = 100 + np.random.randn(n) * 1.0
    df = pd.DataFrame({
        "open": close,
        "high": close + 0.1,
        "low": close - 0.1,
        "close": close,
        "volume": np.random.randint(100000, 200000, n),
    })
    df.index = pd.date_range("2025-01-01", periods=n, freq="D")
    return df


def test_dma_basic_shape_and_alignment():
    """AC1: 输出 Series 形状正确，索引与 df 对齐."""
    df = make_df(200)
    f = T6DMAFactor()
    result = f(df)
    assert isinstance(result.series, pd.Series)
    assert len(result.series) == len(df)
    assert result.series.index.equals(df.index)


def test_dma_uptrend_ddd_turns_positive():
    """AC2: 上升趋势（带转折点）后 DDD 由负转正.

    DMA 设计复盘（D-013.1）：DMA 是转折点指标，不是趋势指标。
    转折后 DDD 应明显大于 0（多头信号）。
    """
    df = make_df(200, trend="up")
    ddd = df["close"].rolling(10).mean() - df["close"].rolling(50).mean()
    # 转折点后（idx 100+）DDD 应 > 0
    tail_ddd = ddd.iloc[100:].dropna()
    assert (tail_ddd > 0).mean() > 0.8, \
        f"上升趋势后段 DDD 应多为正，实测 {(tail_ddd > 0).mean():.2f}"


def test_dma_downtrend_ddd_turns_negative():
    """AC3: 下降趋势（带转折点）后 DDD 由正转负."""
    df = make_df(200, trend="down")
    ddd = df["close"].rolling(10).mean() - df["close"].rolling(50).mean()
    tail_ddd = ddd.iloc[100:].dropna()
    assert (tail_ddd < 0).mean() > 0.8, \
        f"下降趋势后段 DDD 应多为负，实测 {(tail_ddd < 0).mean():.2f}"


def test_dma_nan_for_warmup_period():
    """AC4: 滚动窗口前 59 行 NaN（10 + 50 - 1 + 10 - 1）."""
    df = make_df(100)
    f = T6DMAFactor(fill_method="drop")
    result = f(df)
    # drop 模式下 NaN 被丢弃，series 长度 < 100
    assert len(result.series) < len(df), \
        f"drop 模式应丢弃 NaN，实测 series={len(result.series)} vs df={len(df)}"


def test_dma_category_is_trend():
    """AC5: 类目为 TREND."""
    f = T6DMAFactor()
    assert f.category == FactorCategory.TREND
    assert f.name == "T6_dma"


def test_dma_aliases_contain_dma():
    """AC6: aliases 含 DMA（规则 28 业界别名）."""
    f = T6DMAFactor()
    assert "DMA" in f._aliases
    assert "dma" in f._aliases
    assert "Difference of Moving Averages" in f._aliases


def test_dma_description_includes_params():
    """AC7: 中文描述含 N1/N2/M 参数."""
    f = T6DMAFactor(n1=10, n2=50, m=10)
    desc = f.description
    assert "10" in desc
    assert "50" in desc
    assert "DMA" in desc


def test_dma_zero_fill_default():
    """AC8: 默认 fill_method="zero" 把 NaN 填 0（业务行为）."""
    df = make_df(50)  # 短数据
    f = T6DMAFactor()  # 默认 zero
    result = f(df)
    # 全部 NaN 被填成 0，series 没有 NaN
    assert result.series.isna().sum() == 0, "zero 模式应无 NaN"
    # 前 49 行应为 0
    assert (result.series.head(49) == 0).all(), "前 49 行应全填 0"
