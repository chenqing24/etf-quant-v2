"""
tests/unit/alpha/test_weight_scheme.py — WeightScheme 单测

覆盖：
    - D-004 5 维度校验（权重和 / 范围 / 非空 / 不为 0 / market_mode 必备）
    - d004_b2 factory 数据正确性
    - to_dict / from_dict 往返
    - get_weights 返回拷贝（防外部修改）
"""
import pytest

from etf_quant.alpha.weight_scheme import (
    WeightScheme,
    MIN_WEIGHT,
    MAX_WEIGHT,
    SUPPORTED_MARKET_MODES,
)


def test_d004_b2_factory_basics():
    """D-004 B2 factory：scheme_id / 必备 market_mode / 8 因子全参与"""
    ws = WeightScheme.d004_b2()
    assert ws.scheme_id == "B2"
    assert "trend_up" in ws.weights_by_mode
    assert "range_bound" in ws.weights_by_mode
    # 8 因子全部参与
    trend_factors = set(ws.weights_by_mode["trend_up"].keys())
    range_factors = set(ws.weights_by_mode["range_bound"].keys())
    assert trend_factors == range_factors  # B2 两个 mode 用同一组 8 因子
    assert len(trend_factors) == 8


def test_d004_b2_weights_sum_to_one():
    """D-004 B2：两个 mode 权重和都 = 1.0"""
    ws = WeightScheme.d004_b2()
    for mode in SUPPORTED_MARKET_MODES:
        total = sum(ws.weights_by_mode[mode].values())
        assert abs(total - 1.0) < 1e-6, f"{mode} 权重和 {total} ≠ 1.0"


def test_d004_b2_weights_in_range():
    """D-004 B2：所有权重在 [5%, 40%] 范围"""
    ws = WeightScheme.d004_b2()
    for mode, weights in ws.weights_by_mode.items():
        for fname, w in weights.items():
            assert MIN_WEIGHT - 1e-9 <= w <= MAX_WEIGHT + 1e-9, \
                f"{mode} / {fname} 权重 {w} 超出范围"


def test_weights_sum_not_one_raises():
    """权重和 ≠ 1 → 报错"""
    bad = {
        "trend_up": {"A": 0.5, "B": 0.3},  # 0.8 ≠ 1.0
        "range_bound": {"A": 0.5, "B": 0.5},
    }
    with pytest.raises(ValueError, match="权重和"):
        WeightScheme(scheme_id="bad", weights_by_mode=bad)


def test_weight_too_small_raises():
    """权重 < 5% → 报错（D-004 硬约束）"""
    bad = {
        "trend_up": {"A": 0.04, "B": 0.96},  # 0.04 < 0.05
        "range_bound": {"A": 0.5, "B": 0.5},
    }
    with pytest.raises(ValueError, match="最小值"):
        WeightScheme(scheme_id="bad", weights_by_mode=bad)


def test_weight_too_large_raises():
    """权重 > 40% → 报错（D-004 硬约束）"""
    bad = {
        "trend_up": {"A": 0.50, "B": 0.50},  # 0.50 > 0.40
        "range_bound": {"A": 0.5, "B": 0.5},
    }
    with pytest.raises(ValueError, match="最大值"):
        WeightScheme(scheme_id="bad", weights_by_mode=bad)


def test_zero_weight_raises():
    """权重 = 0 → 报错（D-004 "删除因子" 硬约束）"""
    bad = {
        "trend_up": {"A": 0.0, "B": 1.0},
        "range_bound": {"A": 0.5, "B": 0.5},
    }
    with pytest.raises(ValueError, match="权重为 0"):
        WeightScheme(scheme_id="bad", weights_by_mode=bad)


def test_missing_market_mode_raises():
    """缺少 trend_up / range_bound → 报错"""
    bad = {
        "trend_up": {"A": 0.5, "B": 0.5},
        # 缺 range_bound
    }
    with pytest.raises(ValueError, match="缺少 market_mode"):
        WeightScheme(scheme_id="bad", weights_by_mode=bad)


def test_empty_scheme_raises():
    """空 scheme → 报错"""
    with pytest.raises(ValueError, match="不能为空"):
        WeightScheme(scheme_id="empty", weights_by_mode={})


def test_get_weights_returns_copy():
    """get_weights 返回拷贝（防外部修改污染内部状态）"""
    ws = WeightScheme.d004_b2()
    w1 = ws.get_weights("trend_up")
    w1["T6_dma"] = 0.99  # 修改拷贝（D-013.1：DMA → T6_dma）
    w2 = ws.get_weights("trend_up")
    assert w2["T6_dma"] == 0.30  # 原始未变


def test_get_weights_invalid_mode():
    """不支持的 market_mode → 报错"""
    ws = WeightScheme.d004_b2()
    with pytest.raises(ValueError, match="不支持 market_mode"):
        ws.get_weights("crash")


def test_factor_names_union():
    """factor_names 返回所有 mode 因子并集"""
    ws = WeightScheme.d004_b2()
    factors = ws.factor_names()
    assert len(factors) == 8


def test_to_from_dict_roundtrip():
    """to_dict / from_dict 往返一致"""
    ws = WeightScheme.d004_b2()
    data = ws.to_dict()
    ws2 = WeightScheme.from_dict(data)
    assert ws.scheme_id == ws2.scheme_id
    assert ws.weights_by_mode == ws2.weights_by_mode


def test_frozen():
    """frozen=True 不允许直接赋值"""
    ws = WeightScheme.d004_b2()
    with pytest.raises(Exception):
        ws.scheme_id = "new"