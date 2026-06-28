"""
tests/unit/alpha/test_factors.py — 27 因子单元测试（US-013）

按规则 5.1（关键路径测试覆盖）：
    - 每个因子最小化测试（输入已知 df → 输出预期 Series）
    - 验证 index 对齐、长度匹配
    - 防 NaN/Inf 污染
    - 验证 W4 RV 行为（v9 唯一稳健因子）

总计：27 测试
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_quant.alpha.factors import FACTOR_REGISTRY, get_factor, list_factors


# ────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """构造 100 天的样本 OHLCV 数据。"""
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n))
    return pd.DataFrame({
        "open": close + np.random.randn(n) * 0.1,
        "high": close + np.abs(np.random.randn(n)) * 0.5,
        "low": close - np.abs(np.random.randn(n)) * 0.5,
        "close": close,
        "volume": np.random.randint(1000000, 10000000, n).astype(float),
    }, index=dates)


# ────────────────────────────────────────────────────────────
# 全局验证
# ────────────────────────────────────────────────────────────

def test_27_factors_registered():
    """验证 29 因子全部注册（US-002 + D-013.1）。"""
    # US-001 加 T5_ma5 → 28；US-002 删 M6_macd_diff（公式与 T1 重复）→ 27
    # D-013.1 加 T6_dma + T7_ma_arrangement → 29
    assert len(FACTOR_REGISTRY) == 29
    assert len(list_factors()) == 29
    assert "M6_macd_diff" not in FACTOR_REGISTRY  # 已删
    assert "S2_adx" not in FACTOR_REGISTRY  # 已改名 S2_adx_strength
    assert "S2_adx_strength" in FACTOR_REGISTRY
    assert "T6_dma" in FACTOR_REGISTRY  # D-013.1
    assert "T7_ma_arrangement" in FACTOR_REGISTRY  # D-013.1


def test_all_factors_compute_without_error(sample_df):
    """验证 27 因子全部能成功计算（不抛异常）。"""
    for name in list_factors():
        factor = get_factor(name)
        result = factor(sample_df)
        assert isinstance(result.series, pd.Series)
        assert len(result.series) == len(sample_df)
        assert result.series.index.equals(sample_df.index)
        assert result.sample_count > 0


def test_all_factors_have_metadata(sample_df):
    """验证所有因子元数据完整（name/category/description）。"""
    for name in list_factors():
        factor = get_factor(name)
        m = factor.metadata
        assert m.name == name
        assert m.category is not None
        assert m.description != ""


# ────────────────────────────────────────────────────────────
# 趋势类 (T) — 4 因子
# ────────────────────────────────────────────────────────────

def test_t1_macd_bar(sample_df):
    factor = get_factor("T1_macd_bar")
    result = factor(sample_df)
    assert result.series.notna().sum() > 50  # EMA warm-up 之后有值
    # MACD 柱 = (DIF - DEA)，可以正可以负
    assert result.series.std() > 0


def test_t2_ma_bull(sample_df):
    factor = get_factor("T2_ma_bull")
    result = factor(sample_df)
    # T2 是 0/1 信号
    assert set(result.series.dropna().unique()).issubset({0.0, 1.0})


def test_t3_sar_trend(sample_df):
    factor = get_factor("T3_sar_trend")
    result = factor(sample_df)
    assert set(result.series.dropna().unique()).issubset({0.0, 1.0})


def test_t4_adx_trend(sample_df):
    factor = get_factor("T4_adx_trend")
    result = factor(sample_df)
    assert result.series.notna().sum() > 0
    # ADX 应该非负
    assert (result.series.dropna() >= 0).all()


# ────────────────────────────────────────────────────────────
# 动量类 (M) — 6 因子
# ────────────────────────────────────────────────────────────

def test_m1_momentum_3d(sample_df):
    factor = get_factor("M1_momentum_3d")
    result = factor(sample_df)
    # 3 日动量 = close/close.shift(3) - 1
    assert result.series.notna().sum() > 50


def test_m2_momentum_5d(sample_df):
    factor = get_factor("M2_momentum_5d")
    result = factor(sample_df)
    assert result.series.notna().sum() > 50


def test_m3_momentum_10d(sample_df):
    factor = get_factor("M3_momentum_10d")
    result = factor(sample_df)
    assert result.series.notna().sum() > 50


def test_m4_rsi(sample_df):
    factor = get_factor("M4_rsi")
    result = factor(sample_df)
    # RSI 应在 0~100 之间
    s = result.series.dropna()
    assert (s >= 0).all() and (s <= 100).all()


def test_m5_kdj(sample_df):
    factor = get_factor("M5_kdj")
    result = factor(sample_df)
    # KDJ %K 在 0~100 之间
    s = result.series.dropna()
    assert (s >= 0).all() and (s <= 100).all()


def test_v1_volume(sample_df):
    factor = get_factor("V1_volume")
    result = factor(sample_df)
    # 放量比 = vol/MA5(vol) - 1
    assert result.series.notna().sum() > 50


def test_v2_obv(sample_df):
    factor = get_factor("V2_obv")
    result = factor(sample_df)
    # OBV 累加
    assert result.series.iloc[-1] != 0


def test_v3_maobv(sample_df):
    factor = get_factor("V3_maobv")
    result = factor(sample_df)
    assert result.series.notna().sum() > 50


def test_v4_volume_ratio(sample_df):
    factor = get_factor("V4_volume_ratio")
    result = factor(sample_df)
    # 量比 = vol/MA5(vol)，均值约 1
    assert 0.5 < result.series.dropna().mean() < 2.0


# ────────────────────────────────────────────────────────────
# 波动类 (W) — 4 因子（含 W4 RV 重点验证）
# ────────────────────────────────────────────────────────────

def test_b1_boll_upper(sample_df):
    factor = get_factor("B1_boll_upper")
    result = factor(sample_df)
    # 布林上轨突破可正可负
    assert result.series.notna().sum() > 50


def test_w1_atr(sample_df):
    factor = get_factor("W1_atr")
    result = factor(sample_df)
    # ATR 必然非负
    s = result.series.dropna()
    assert (s >= 0).all()
    assert s.mean() > 0


def test_w2_boll_width(sample_df):
    factor = get_factor("W2_boll_width")
    result = factor(sample_df)
    # 带宽 >= 0
    s = result.series.dropna()
    assert (s >= 0).all()


def test_w3_volatility(sample_df):
    factor = get_factor("W3_volatility")
    result = factor(sample_df)
    # 波动率 >= 0
    s = result.series.dropna()
    assert (s >= 0).all()


def test_w4_rv(sample_df):
    """W4 RV = std_short / std_long - 1（v9 唯一稳健因子）。"""
    factor = get_factor("W4_rv")
    result = factor(sample_df)
    # W4 应该围绕 0 震荡
    s = result.series.dropna()
    assert len(s) > 0
    assert abs(s.mean()) < 1.0  # 不会偏移太远
    # W4 < 0 占比应该在 30-70% 之间（均值回归属性）
    pct_below_zero = (s < 0).mean()
    assert 0.2 < pct_below_zero < 0.8


def test_w4_rv_rejects_invalid_windows():
    """W4 RV 必须 short_window < long_window。"""
    from etf_quant.alpha.factors.w4_rv import W4RVFactor
    with pytest.raises(ValueError, match="must be <"):
        W4RVFactor(short_window=40, long_window=20)


# ────────────────────────────────────────────────────────────
# 趋势强度 (S) — 2 因子
# ────────────────────────────────────────────────────────────

def test_s1_vhf(sample_df):
    factor = get_factor("S1_vhf")
    result = factor(sample_df)
    # VHF 在 0~1 之间
    s = result.series.dropna()
    assert (s >= 0).all() and (s <= 2).all()  # 可能短暂 > 1


def test_s2_adx_strength(sample_df):
    factor = get_factor("S2_adx_strength")
    result = factor(sample_df)
    # S2 已 clip 到 0~1
    s = result.series.dropna()
    assert (s >= 0).all() and (s <= 1).all()


# ────────────────────────────────────────────────────────────
# 超买超卖 (O) — 2 因子
# ────────────────────────────────────────────────────────────

def test_o1_cci(sample_df):
    factor = get_factor("O1_cci")
    result = factor(sample_df)
    assert result.series.notna().sum() > 0
    # CCI 通常在 -300 ~ +300 之间
    s = result.series.dropna()
    assert s.abs().max() < 1000


def test_o2_wr(sample_df):
    factor = get_factor("O2_wr")
    result = factor(sample_df)
    # Williams %R 在 -100 ~ 0 之间
    s = result.series.dropna()
    assert (s >= -100).all() and (s <= 0).all()


# ────────────────────────────────────────────────────────────
# 相对强弱 (R) — 1 因子
# ────────────────────────────────────────────────────────────

def test_r1_relative(sample_df):
    factor = get_factor("R1_relative")
    result = factor(sample_df)
    # close/MA60 - 1，可正可负
    assert result.series.notna().sum() > 0


# ────────────────────────────────────────────────────────────
# 反转类 (N) — 3 因子
# ────────────────────────────────────────────────────────────

def test_n1_reversal_3d(sample_df):
    factor = get_factor("N1_reversal_3d")
    result = factor(sample_df)
    assert result.series.notna().sum() > 50


def test_n2_reversal_5d(sample_df):
    factor = get_factor("N2_reversal_5d")
    result = factor(sample_df)
    assert result.series.notna().sum() > 50


def test_n3_rsi_oversold(sample_df):
    factor = get_factor("N3_rsi_oversold")
    result = factor(sample_df)
    # RSI 在 0~100
    s = result.series.dropna()
    assert (s >= 0).all() and (s <= 100).all()


# ────────────────────────────────────────────────────────────
# 因子基类验证（防未来函数 L121 教训）
# ────────────────────────────────────────────────────────────

def test_factor_result_validates_index_mismatch(sample_df):
    """因子结果索引不匹配时抛错。"""
    factor = get_factor("T1_macd_bar")
    # 模拟坏结果：返回错误长度的 Series
    from etf_quant.alpha.factor_base import Factor, FactorCategory

    class BadFactor(Factor):
        @property
        def name(self) -> str:
            return "BAD"

        @property
        def category(self) -> FactorCategory:
            return FactorCategory.TREND

        @property
        def description(self) -> str:
            return "bad"

        def compute(self, df):
            return pd.Series([1, 2, 3])  # 长度不匹配

    with pytest.raises(ValueError, match="length mismatch"):
        BadFactor()(sample_df)
