"""
tests/unit/alpha/test_ma_arrangement.py — T7 MA 排列因子单测（D-013.1）

按规则 11（先测试再交付）+ 规则 5.1（关键路径覆盖）。

总计：8 测试
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_quant.alpha.factor_base import FactorCategory
from etf_quant.alpha.factors.t7_ma_arrangement import T7MAArrangementFactor


def make_df(n: int = 200, trend: str = "up") -> pd.DataFrame:
    """构造测试用 OHLCV 数据（带转折点的趋势）.

    前 min(50, n//2) 日横盘 + 后 n - 前段 日趋势。
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
        close = np.full(n, 100.0) + np.random.randn(n) * 0.01
    df = pd.DataFrame({
        "open": close,
        "high": close + 0.1,
        "low": close - 0.1,
        "close": close,
        "volume": np.random.randint(100000, 200000, n),
    })
    df.index = pd.date_range("2025-01-01", periods=n, freq="D")
    return df


def test_ma_arr_basic_shape_and_alignment():
    """AC1: 输出 Series 形状正确，索引与 df 对齐."""
    df = make_df(200)
    f = T7MAArrangementFactor()
    result = f(df)
    assert isinstance(result.series, pd.Series)
    assert len(result.series) == len(df)
    assert result.series.index.equals(df.index)


def test_ma_arr_uptrend_bull():
    """AC2: 持续上升趋势后期输出 +1（多头排列）."""
    df = make_df(200, trend="up")
    f = T7MAArrangementFactor()
    result = f(df)
    tail = result.series.dropna().tail(30)
    assert (tail == 1).mean() > 0.7, \
        f"持续上升趋势后段应多为多头，实测多头率 {(tail == 1).mean():.2f}"


def test_ma_arr_downtrend_bear():
    """AC3: 持续下降趋势后期输出 -1（空头排列）."""
    df = make_df(200, trend="down")
    f = T7MAArrangementFactor()
    result = f(df)
    tail = result.series.dropna().tail(30)
    assert (tail == -1).mean() > 0.7, \
        f"持续下降趋势后段应多为空头，实测空头率 {(tail == -1).mean():.2f}"


def test_ma_arr_flat_ranging():
    """AC4: 横盘/纠缠时输出 0（不强制多头/空头）."""
    df = make_df(200, trend="flat")
    f = T7MAArrangementFactor()
    result = f(df)
    # 横盘时 MA5~MA60 应很接近，绝大多数时间纠缠
    valid = result.series.dropna()
    assert (valid == 0).mean() > 0.8, \
        f"横盘应多为纠缠，实测纠缠率 {(valid == 0).mean():.2f}"


def test_ma_arr_output_values():
    """AC5: 输出值域严格为 {-1, 0, +1}."""
    df = make_df(200, trend="up")
    f = T7MAArrangementFactor()
    result = f(df)
    valid = result.series.dropna().astype(int)
    unique_values = set(valid.unique())
    assert unique_values.issubset({-1, 0, 1}), f"输出值域越界：{unique_values}"


def test_ma_arr_nan_warmup():
    """AC6: 前 59 行输出 0（NaN 被 fill_method 填 0 或 drop 丢弃）.

    T7 compute 默认初始化为 0（pd.Series(0, ...)），所以 NaN 转 0。
    fill_method="zero" 时前 59 行 = 0，fill_method="drop" 时 NaN 丢弃。
    """
    df = make_df(100)
    # 测试 zero 模式（前 59 行应为 0）
    f_zero = T7MAArrangementFactor(fill_method="zero")
    result_zero = f_zero(df)
    # 前 59 行（MA60 滚动前）应全为 0
    head = result_zero.series.head(59)
    assert (head == 0).all(), f"前 59 行应全 0，实测非 0 个数：{(head != 0).sum()}"


def test_ma_arr_category_and_name():
    """AC7: 类目为 TREND，因子名为 T7_ma_arrangement."""
    f = T7MAArrangementFactor()
    assert f.category == FactorCategory.TREND
    assert f.name == "T7_ma_arrangement"


def test_ma_arr_aliases_contain_fib():
    """AC8: aliases 含 FIB（规则 28 业界别名）."""
    f = T7MAArrangementFactor()
    assert "FIB" in f._aliases
    assert "fib" in f._aliases
    assert "MA_alignment" in f._aliases
    assert "均线排列" in f._aliases
