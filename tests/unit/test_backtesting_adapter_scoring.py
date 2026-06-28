"""
tests/unit/test_backtesting_adapter_scoring.py — backtesting_adapter 接 D-013 Scorer

覆盖：
    - 等权硬编码已替换为 D-004 B2 加权
    - WeightScheme.d004_b2() 在 backtest 链路可用
    - 工厂函数签名兼容
"""
from src.etf_quant.backtest.backtesting_adapter import _make_strategy_class
from etf_quant.alpha.weight_scheme import WeightScheme


def test_make_strategy_class_works():
    """工厂函数：能生成 Backtesting.py Strategy 类"""
    Strategy = _make_strategy_class(["W2_boll_width", "M4_rsi"], top_k=1)
    assert Strategy.__name__ == "FactorCompositeStrategy"
    assert hasattr(Strategy, "init")
    assert hasattr(Strategy, "next")


def test_weight_scheme_d004_b2_available_in_backtest():
    """D-004 B2 权重在 backtest 链路可用（不再用等权硬编码）"""
    scheme = WeightScheme.d004_b2()
    weights_t = scheme.get_weights("trend_up")
    # B2 trend_up 关键权重：D-013.1 已改 T6_dma 30% + T7_ma_arrangement 25%（重趋势）
    assert weights_t["T6_dma"] == 0.30
    assert weights_t["T7_ma_arrangement"] == 0.25
    # 权重和 = 1
    assert abs(sum(weights_t.values()) - 1.0) < 1e-6


def test_weight_scheme_has_8_factors():
    """B2 方案覆盖 8 因子（全部参与）"""
    scheme = WeightScheme.d004_b2()
    assert len(scheme.factor_names()) == 8


def test_make_strategy_class_with_empty_factors():
    """边界：空因子列表不应崩（factory 不校验，交由 Backtesting.py 内部处理）"""
    Strategy = _make_strategy_class([], top_k=1)
    assert Strategy.__name__ == "FactorCompositeStrategy"