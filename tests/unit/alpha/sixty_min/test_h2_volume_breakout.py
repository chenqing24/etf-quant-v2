"""
tests/unit/alpha/sixty_min/test_h2_volume_breakout.py — H2 因子单测（D-007）

总计：6 测试
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_quant.alpha.factor_base import FactorCategory
from etf_quant.alpha.factors.sixty_min.h2_volume_breakout import H2VolumeBreakoutFactor


def make_volume_df(n_bars: int = 100, pattern: str = "constant") -> pd.DataFrame:
    """构造 60min 测试数据."""
    np.random.seed(42)
    if pattern == "constant":
        volume = np.full(n_bars, 1000000.0)
    elif pattern == "breakout":
        # 前 70 bar 1M，后 30 bar 3M（放量）
        volume = np.concatenate([np.full(70, 1000000.0), np.full(30, 3000000.0)])
    elif pattern == "shrink":
        # 前 70 bar 3M，后 30 bar 1M（缩量）
        volume = np.concatenate([np.full(70, 3000000.0), np.full(30, 1000000.0)])
    else:
        volume = np.random.randint(500000, 2000000, n_bars).astype(float)

    rows = []
    for i in range(n_bars):
        ts = pd.Timestamp("2025-06-01") + pd.Timedelta(hours=i)
        rows.append({
            "datetime": ts,
            "open": 1.0,
            "close": 1.0,
            "high": 1.01,
            "low": 0.99,
            "volume": volume[i],
        })
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df["datetime"])
    return df


def test_h2_basic_shape_and_alignment():
    """AC1: 输出 Series 形状正确，索引与 df 对齐."""
    df = make_volume_df(100)
    f = H2VolumeBreakoutFactor()
    result = f(df)
    assert isinstance(result.series, pd.Series)
    assert len(result.series) == len(df)
    assert result.series.index.equals(df.index)


def test_h2_breakout_positive():
    """AC2: 放量期 H2 > 0（短期均量 > 长期均量）."""
    df = make_volume_df(100, pattern="breakout")
    f = H2VolumeBreakoutFactor()
    result = f(df)
    # 后 30 bar（放量期）应 > 0
    tail = result.series.iloc[70:].dropna()
    assert (tail > 0).mean() > 0.7, f"放量期 H2 应 > 0，实测正率 {(tail > 0).mean():.2f}"


def test_h2_shrink_negative():
    """AC3: 缩量期 H2 < 0（短期均量 < 长期均量）."""
    df = make_volume_df(100, pattern="shrink")
    f = H2VolumeBreakoutFactor()
    result = f(df)
    # 后 30 bar（缩量期）应 < 0
    tail = result.series.iloc[70:].dropna()
    assert (tail < 0).mean() > 0.7, f"缩量期 H2 应 < 0，实测负率 {(tail < 0).mean():.2f}"


def test_h2_constant_near_zero():
    """AC4: 成交量恒定 H2 ≈ 0（无量变）."""
    df = make_volume_df(100, pattern="constant")
    f = H2VolumeBreakoutFactor()
    result = f(df)
    valid = result.series.dropna()
    # 量比 = 1 → breakout = 0
    assert abs(valid).mean() < 0.01, f"恒定量 H2 应接近 0，实测均值 {abs(valid).mean():.6f}"


def test_h2_category_and_name():
    """AC5: 类目为 VOLUME，因子名为 H2_volume_breakout."""
    f = H2VolumeBreakoutFactor()
    assert f.category == FactorCategory.VOLUME
    assert f.name == "H2_volume_breakout"


def test_h2_aliases_contain_volume():
    """AC6: aliases 含业界别名（规则 28）."""
    f = H2VolumeBreakoutFactor()
    assert "H2" in f._aliases
    assert "VolumeBreakout" in f._aliases
    assert "量比" in f._aliases