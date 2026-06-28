"""
tests/unit/alpha/sixty_min/test_h4_price_volume_corr.py — H4 因子单测（D-007）

总计：6 测试
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_quant.alpha.factor_base import FactorCategory
from etf_quant.alpha.factors.sixty_min.h4_price_volume_corr import H4PriceVolumeCorrFactor


def make_pv_df(n_bars: int = 60, pattern: str = "sync") -> pd.DataFrame:
    """构造 60min 测试数据：60 个 bar（满足 20 bar window 需求 + 测试余地）.

    关键设计：close 和 volume 在后段必须明显同步/背离，
    否则 Spearman 看不出相关性。
    """
    np.random.seed(42)
    if pattern == "sync":
        # 价量同步：close 上升时 volume 上升，close 下降时 volume 下降
        close_moves = np.random.randn(n_bars) * 0.01
        close = np.cumsum(close_moves) + 1.0
        # volume = close_moves 同步映射（保留符号）
        volume = (close_moves + 1.0) * 1000000 + 500000
    elif pattern == "diverge":
        # 价量背离：close 上升时 volume 下降
        close_moves = np.random.randn(n_bars) * 0.01
        close = np.cumsum(close_moves) + 1.0
        # volume = close_moves 反向映射
        volume = (-close_moves + 1.0) * 1000000 + 500000
    else:
        close = np.cumsum(np.random.randn(n_bars) * 0.01) + 1.0
        volume = np.random.randint(500000, 2000000, n_bars).astype(float)

    rows = []
    for i in range(n_bars):
        ts = pd.Timestamp("2025-06-01") + pd.Timedelta(hours=i)
        rows.append({
            "datetime": ts,
            "open": close[i],
            "close": close[i],
            "high": close[i] * 1.01,
            "low": close[i] * 0.99,
            "volume": max(volume[i], 100),  # 避免负值
        })
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df["datetime"])
    return df


def test_h4_basic_shape_and_alignment():
    """AC1: 输出 Series 形状正确，索引与 df 对齐."""
    df = make_pv_df(60)
    f = H4PriceVolumeCorrFactor(window=20)
    result = f(df)
    assert isinstance(result.series, pd.Series)
    assert len(result.series) == len(df)
    assert result.series.index.equals(df.index)


def test_h4_sync_positive():
    """AC2: 价升量增期 H4 > 0（量价同向）."""
    df = make_pv_df(60, pattern="sync")
    f = H4PriceVolumeCorrFactor(window=20)
    result = f(df)
    # 后 30 bar（同步期）应 > 0
    tail = result.series.iloc[30:].dropna()
    assert tail.mean() > 0, f"量价同步期 H4 应 > 0，实测均值 {tail.mean():.4f}"


def test_h4_diverge_negative():
    """AC3: 价升量缩期 H4 < 0（量价背离）."""
    df = make_pv_df(60, pattern="diverge")
    f = H4PriceVolumeCorrFactor(window=20)
    result = f(df)
    # 后 30 bar（背离期）应 < 0
    tail = result.series.iloc[30:].dropna()
    assert tail.mean() < 0, f"量价背离期 H4 应 < 0，实测均值 {tail.mean():.4f}"


def test_h4_value_range():
    """AC4: H4 值域应在 [-1, 1]."""
    df = make_pv_df(60)
    f = H4PriceVolumeCorrFactor(window=20)
    result = f(df)
    valid = result.series.dropna()
    assert valid.min() >= -1.0, f"H4 最小值 {valid.min()} < -1"
    assert valid.max() <= 1.0, f"H4 最大值 {valid.max()} > 1"


def test_h4_category_and_name():
    """AC5: 类目为 VOLUME，因子名为 H4_price_volume_corr."""
    f = H4PriceVolumeCorrFactor()
    assert f.category == FactorCategory.VOLUME
    assert f.name == "H4_price_volume_corr"


def test_h4_aliases_contain_pv():
    """AC6: aliases 含业界别名（规则 28）."""
    f = H4PriceVolumeCorrFactor()
    assert "H4" in f._aliases
    assert "PriceVolumeCorr" in f._aliases
    assert "量价背离" in f._aliases