"""
tests/unit/alpha/sixty_min/test_h1_intraday_trend.py — H1 因子单测（D-007）

按规则 11（先测试再交付）+ 规则 5.1（关键路径覆盖）。

总计：6 测试
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_quant.alpha.factor_base import FactorCategory
from etf_quant.alpha.factors.sixty_min.h1_intraday_trend import H1IntradayTrendFactor


def make_intraday_df(n_days: int = 5, trend: str = "up") -> pd.DataFrame:
    """构造 60min 测试数据：每天 4 个 bar（10:30/11:30/14:00/15:00）."""
    np.random.seed(42)
    rows = []
    for day in range(n_days):
        base_date = pd.Timestamp("2025-06-01") + pd.Timedelta(days=day)
        if trend == "up":
            base_price = 1.0 + day * 0.02  # 每日 +2%
        elif trend == "down":
            base_price = 2.0 - day * 0.02  # 每日 -2%
        else:
            base_price = 1.0
        # 每天 4 个 60min bar，bar 间斜率上/下/横盘
        for bar_idx, (hour, minute) in enumerate([(10, 30), (11, 30), (14, 0), (15, 0)]):
            ts = base_date.replace(hour=hour, minute=minute)
            if trend == "up":
                close = base_price + bar_idx * 0.005  # 日内上升
            elif trend == "down":
                close = base_price - bar_idx * 0.005  # 日内下降
            else:
                close = base_price
            close += np.random.randn() * 0.001
            rows.append({
                "datetime": ts,
                "open": close - 0.001,
                "close": close,
                "high": close + 0.001,
                "low": close - 0.002,
                "volume": 1000000,
            })
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df["datetime"])
    return df


def test_h1_basic_shape_and_alignment():
    """AC1: 输出 Series 形状正确，索引与 df 对齐."""
    df = make_intraday_df(5)
    f = H1IntradayTrendFactor()
    result = f(df)
    assert isinstance(result.series, pd.Series)
    assert len(result.series) == len(df)
    assert result.series.index.equals(df.index)


def test_h1_uptrend_positive():
    """AC2: 持续上升趋势 H1 > 0（多头日内趋势）."""
    df = make_intraday_df(5, trend="up")
    f = H1IntradayTrendFactor()
    result = f(df)
    # 同一天的 4 个 bar 共用一个 slope 值
    valid = result.series.dropna()
    assert (valid > 0).mean() > 0.7, f"上升趋势 H1 应多为正，实测正率 {(valid > 0).mean():.2f}"


def test_h1_downtrend_negative():
    """AC3: 持续下降趋势 H1 < 0（空头日内趋势）."""
    df = make_intraday_df(5, trend="down")
    f = H1IntradayTrendFactor()
    result = f(df)
    valid = result.series.dropna()
    assert (valid < 0).mean() > 0.7, f"下降趋势 H1 应多为负，实测负率 {(valid < 0).mean():.2f}"


def test_h1_category_and_name():
    """AC4: 类目为 TREND，因子名为 H1_intraday_trend."""
    f = H1IntradayTrendFactor()
    assert f.category == FactorCategory.TREND
    assert f.name == "H1_intraday_trend"


def test_h1_aliases_contain_intraday():
    """AC5: aliases 含业界别名（规则 28）."""
    f = H1IntradayTrendFactor()
    assert "H1" in f._aliases
    assert "IntradayTrend" in f._aliases
    assert "intraday_momentum" in f._aliases


def test_h1_requires_close_and_datetime_index():
    """AC6: 缺 close 列或非 DatetimeIndex 必须报错."""
    df = pd.DataFrame({"open": [1.0, 2.0], "volume": [100, 200]})
    f = H1IntradayTrendFactor()
    with pytest.raises(ValueError, match="close"):
        f(df)

    df2 = pd.DataFrame({"close": [1.0, 2.0]}, index=[0, 1])
    with pytest.raises(ValueError, match="DatetimeIndex"):
        f(df2)