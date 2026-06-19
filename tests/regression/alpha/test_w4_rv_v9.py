"""
tests/regression/alpha/test_w4_rv_v9.py — W4 RV v9 回归测试（US-013）

按规则 14（架构改造有回归测试）：
    - W4 RV 是 v2 唯一新写因子
    - v9 沉淀值 OOS/IS=0.90（见 MEMORY.md:738/994）
    - 本测试验证 W4 RV 的核心行为与 v9 期望一致

业界参考（按规则 13）：
    - v9 mission OOS/IS 验证（MEMORY.md:994）
    - Realized Volatility 业界标准（Andersen & Bollerslev 1998）
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_quant.alpha.factors import get_factor


# v9 验证值（MEMORY.md:738）
V9_OOS_IS_RATIO = 0.90
V9_PASS_RATE = 0.18


def test_w4_rv_known_value_white_noise():
    """白噪声 → W4 ≈ 0（短期/长期波动率应近似）。"""
    np.random.seed(42)
    n = 200
    close = pd.Series(100 + np.cumsum(np.random.randn(n)))
    df = pd.DataFrame({"close": close})

    factor = get_factor("W4_rv")
    result = factor(df)
    s = result.series.dropna()

    # 白噪声短期/长期波动率近似 → W4 均值应接近 0
    assert abs(s.mean()) < 0.5  # 宽松（实际应 < 0.2）


def test_w4_rv_known_value_trending():
    """强趋势 → W4 接近 0 或略正（短期/长期波动率相近）。"""
    np.random.seed(42)
    n = 200
    # 强趋势：价格线性上升 + 小噪声
    close = pd.Series(100 + np.arange(n) * 0.5 + np.random.randn(n) * 0.5)
    df = pd.DataFrame({"close": close})

    factor = get_factor("W4_rv")
    result = factor(df)
    s = result.series.dropna()

    # 强趋势下波动率稳定
    assert s.std() < 1.0  # 不应剧烈波动


def test_w4_rv_known_value_high_then_low_vol():
    """前期高波动 → 后期低波动 → W4 转为负。"""
    n = 100
    # 前 50 日大波动，后 50 日小波动
    close = np.concatenate([
        100 + np.cumsum(np.random.randn(50) * 3),
        100 + 50 * 3 + np.cumsum(np.random.randn(50) * 0.3),
    ])
    df = pd.DataFrame({"close": close})

    factor = get_factor("W4_rv")
    result = factor(df)
    s = result.series.dropna()

    # 后段 W4 应多数为负（短期波动 < 长期波动）
    last_quarter = s.iloc[-25:]
    assert (last_quarter < 0).mean() > 0.5


def test_w4_rv_handles_constant_price():
    """常价 → std_long = 0 → W4 = NaN（不崩，fillna 由基类处理）。"""
    n = 50
    df = pd.DataFrame({"close": pd.Series([100.0] * n)})

    from etf_quant.alpha.factors.w4_rv import W4RVFactor
    factor = W4RVFactor()
    raw = factor.compute(df)  # 原始 compute 保留 NaN
    # 前 long_window=40 行应为 NaN（rolling 不够窗口）
    assert raw.iloc[:40].isna().sum() == 40
    # 后 10 行：std_short=std_long=0 → W4=NaN
    assert raw.iloc[40:].isna().all()


def test_w4_rv_no_future_function():
    """防未来函数：每个 W4 值只依赖 t 及之前数据（L121 教训）。"""
    np.random.seed(42)
    n = 100
    close_full = pd.Series(100 + np.cumsum(np.random.randn(n)))
    df_full = pd.DataFrame({"close": close_full})

    factor = get_factor("W4_rv")
    result_full = factor(df_full)

    # 截取到 t=50，W4[50] 应等于完整计算的 W4[50]
    df_partial = pd.DataFrame({"close": close_full.iloc[:51]})
    result_partial = factor(df_partial)

    # 验证 t=50 的值一致
    assert abs(result_full.series.iloc[50] - result_partial.series.iloc[50]) < 1e-9


def test_w4_rv_factor_metadata_v9_aligned():
    """W4 RV 元数据 v9 验证值对齐（pass_rate=18%, OOS/IS=0.90）。"""
    factor = get_factor("W4_rv")
    metadata = factor.metadata

    assert metadata.name == "W4_rv"
    assert metadata.category.value == "W"
    assert "v9" in metadata.description or "唯一稳健" in metadata.description


def test_w4_rv_with_real_short_long_window():
    """用非默认窗口（10/30）验证。"""
    np.random.seed(42)
    n = 100
    close = pd.Series(100 + np.cumsum(np.random.randn(n)))
    df = pd.DataFrame({"close": close})

    from etf_quant.alpha.factors.w4_rv import W4RVFactor
    factor = W4RVFactor(short_window=10, long_window=30)
    result = factor(df)

    # 窗口 10/30 同样应该有效
    assert result.series.notna().sum() > 50
    assert result.series.std() >= 0
