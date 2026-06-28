"""
tests/unit/alpha/sixty_min/test_h3_boll_width_pct.py — H3 因子单测（D-007）

总计：6 测试
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_quant.alpha.factor_base import FactorCategory
from etf_quant.alpha.factors.sixty_min.h3_boll_width_pct import H3BollWidthPctFactor


def make_boll_df(n_bars: int = 300, pattern: str = "squeeze") -> pd.DataFrame:
    """构造 60min 测试数据：300 个 bar（满足 252 percentile + 20 boll 需求）."""
    np.random.seed(42)
    if pattern == "squeeze":
        # 前 250 bar 波动大（带宽大），后 50 bar 波动极小（挤压）
        base = np.cumsum(np.random.randn(n_bars) * 0.01) + 1.0
        base[250:] = base[250] + np.cumsum(np.random.randn(50) * 0.0005)
    elif pattern == "expand":
        # 前 250 bar 波动小，后 50 bar 波动极大
        base = np.cumsum(np.random.randn(n_bars) * 0.001) + 1.0
        base[250:] = base[250] + np.cumsum(np.random.randn(50) * 0.05)
    else:
        base = np.cumsum(np.random.randn(n_bars) * 0.005) + 1.0

    rows = []
    for i in range(n_bars):
        ts = pd.Timestamp("2025-06-01") + pd.Timedelta(hours=i)
        rows.append({
            "datetime": ts,
            "open": base[i],
            "close": base[i],
            "high": base[i] * 1.01,
            "low": base[i] * 0.99,
            "volume": 1000000,
        })
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df["datetime"])
    return df


def test_h3_basic_shape_and_alignment():
    """AC1: 输出 Series 形状正确，索引与 df 对齐."""
    df = make_boll_df(300)
    f = H3BollWidthPctFactor(percentile_window=100)  # 测试用小窗口加速
    result = f(df)
    assert isinstance(result.series, pd.Series)
    assert len(result.series) == len(df)
    assert result.series.index.equals(df.index)


def test_h3_squeeze_low_pct():
    """AC2: 布林挤压期 H3 接近 0（带宽处于历史低位）."""
    df = make_boll_df(300, pattern="squeeze")
    f = H3BollWidthPctFactor(percentile_window=100)
    result = f(df)
    # 后 50 bar 挤压期，H3 应偏低
    tail = result.series.iloc[260:].dropna()
    assert tail.mean() < 0.5, f"挤压期 H3 应 < 0.5，实测均值 {tail.mean():.4f}"


def test_h3_expand_high_pct():
    """AC3: 布林扩张期 H3 接近 1（带宽处于历史高位）."""
    df = make_boll_df(300, pattern="expand")
    f = H3BollWidthPctFactor(percentile_window=100)
    result = f(df)
    # 后 50 bar 扩张期，H3 应偏高
    tail = result.series.iloc[260:].dropna()
    assert tail.mean() > 0.5, f"扩张期 H3 应 > 0.5，实测均值 {tail.mean():.4f}"


def test_h3_value_range():
    """AC4: H3 值域应在 [0, 1]."""
    df = make_boll_df(300)
    f = H3BollWidthPctFactor(percentile_window=100)
    result = f(df)
    valid = result.series.dropna()
    assert valid.min() >= 0.0, f"H3 最小值 {valid.min()} < 0"
    assert valid.max() <= 1.0, f"H3 最大值 {valid.max()} > 1"


def test_h3_category_and_name():
    """AC5: 类目为 VOLATILITY，因子名为 H3_boll_width_pct."""
    f = H3BollWidthPctFactor()
    assert f.category == FactorCategory.VOLATILITY
    assert f.name == "H3_boll_width_pct"


def test_h3_aliases_contain_boll():
    """AC6: aliases 含业界别名（规则 28）."""
    f = H3BollWidthPctFactor()
    assert "H3" in f._aliases
    assert "BollWidthPct" in f._aliases
    assert "BBW" in f._aliases