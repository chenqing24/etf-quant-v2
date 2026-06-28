"""
tests/unit/alpha/test_scoring.py — CrossSectionalScorer 单测

覆盖：
    - 3 Layer pipeline（compute / rank / composite）
    - 默认 v2 factory
    - 因子权重校验（FactorSet ⊆ WeightScheme）
    - 边界（空数据 / 全 NaN / 部分 NaN）
    - top_k 输出按 score 降序
"""
import numpy as np
import pandas as pd
import pytest

from etf_quant.alpha.factor_set import FactorSet
from etf_quant.alpha.scoring import CrossSectionalScorer, ScoringResult
from etf_quant.alpha.weight_scheme import WeightScheme


def _make_ohlcv(n: int = 60, start_price: float = 1.0, trend: float = 0.001) -> pd.DataFrame:
    """生成模拟 OHLCV 数据（带趋势）"""
    np.random.seed(42)
    prices = [start_price]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + trend + np.random.normal(0, 0.01)))
    prices = np.array(prices)
    df = pd.DataFrame({
        "open": prices * (1 + np.random.normal(0, 0.005, n)),
        "high": prices * (1 + abs(np.random.normal(0, 0.01, n))),
        "low": prices * (1 - abs(np.random.normal(0, 0.01, n))),
        "close": prices,
        "volume": np.random.randint(1000000, 5000000, n).astype(float),
    })
    df.index = pd.date_range("2024-01-01", periods=n, freq="D")
    return df


def test_default_v2_factory():
    """默认 v2 factory：八因子 + B2 权重"""
    scorer = CrossSectionalScorer.default_v2()
    assert scorer.factor_set.name == "eight_factor_v2"
    assert scorer.weight_scheme.scheme_id == "B2"


def test_factor_set_must_be_subset_of_weight_scheme():
    """FactorSet 因子必须在 WeightScheme 中有权重（否则报错）"""
    # 构造一个 WeightScheme 只含 2 因子（合规权重）
    ws = WeightScheme(
        scheme_id="tiny",
        weights_by_mode={
            "trend_up": {"W2_boll_width": 0.4, "M4_rsi": 0.3, "V2_obv": 0.3},
            "range_bound": {"W2_boll_width": 0.4, "M4_rsi": 0.3, "V2_obv": 0.3},
        },
    )
    # 8 因子的 FactorSet 包含 ws 之外的因子（V3_maobv, M2_momentum_5d, B1_boll_upper）
    fs = FactorSet.eight_factor_v2()  # 6 因子
    with pytest.raises(ValueError, match="在 WeightScheme 中无权重"):
        CrossSectionalScorer(factor_set=fs, weight_scheme=ws)


def test_score_empty_data():
    """factor_data 为空 → 空 result + warning"""
    scorer = CrossSectionalScorer.default_v2()
    result = scorer.score("trend_up", {})
    assert result.scores == {}
    assert "factor_data 为空" in result.warnings


def test_score_produces_scores():
    """正常数据 → 产出有区分度的 score"""
    scorer = CrossSectionalScorer.default_v2()
    codes = ["510300", "515050", "512170"]
    factor_data = {
        "510300": _make_ohlcv(60, start_price=4.0, trend=0.002),
        "515050": _make_ohlcv(60, start_price=1.5, trend=0.005),
        "512170": _make_ohlcv(60, start_price=0.8, trend=-0.003),
    }
    result = scorer.score("trend_up", factor_data)

    # 全部应有 score
    assert set(result.scores.keys()) == set(codes)
    # Score 在 [0, 1]
    for code, s in result.scores.items():
        assert 0.0 <= s <= 1.0, f"{code} score {s} 超出 [0,1]"
    # 必有区分度（不全相等）
    unique_scores = set(round(s, 4) for s in result.scores.values())
    assert len(unique_scores) >= 2, f"score 无区分度：{result.scores}"


def test_top_k_sorted_descending():
    """top_k 按 score 降序"""
    scorer = CrossSectionalScorer.default_v2()
    factor_data = {
        "510300": _make_ohlcv(60, start_price=4.0, trend=0.001),
        "515050": _make_ohlcv(60, start_price=1.5, trend=0.008),
        "512170": _make_ohlcv(60, start_price=0.8, trend=-0.005),
        "512880": _make_ohlcv(60, start_price=1.0, trend=0.003),
    }
    result = scorer.score("trend_up", factor_data)
    top3 = result.top_k(3)
    assert len(top3) == 3
    # 降序
    for i in range(len(top3) - 1):
        assert top3[i][1] >= top3[i + 1][1], \
            f"top_k 非降序：{top3[i][1]} < {top3[i + 1][1]}"


def test_score_uses_range_bound_weights():
    """range_bound mode 跑出来跟 trend_up 不同的 score"""
    scorer = CrossSectionalScorer.default_v2()
    # 用不同 trend 强度模拟不同状态的 ETF
    factor_data = {
        "510300": _make_ohlcv(60, start_price=4.0, trend=0.001),
        "515050": _make_ohlcv(60, start_price=1.5, trend=0.010),  # 强趋势
        "512170": _make_ohlcv(60, start_price=0.8, trend=-0.008),  # 强下跌
        "512880": _make_ohlcv(60, start_price=1.0, trend=0.000),  # 震荡
    }
    r_trend = scorer.score("trend_up", factor_data)
    r_range = scorer.score("range_bound", factor_data)
    # 不同 mode → 至少有一个 code score 不同（权重分配差异）
    diffs = [
        abs(r_trend.scores[c] - r_range.scores[c]) for c in factor_data
    ]
    assert any(d > 1e-4 for d in diffs), \
        f"trend_up / range_bound score 完全相同（异常）：{diffs}"


def test_score_invalid_market_mode():
    """不支持的 market_mode → 报错"""
    scorer = CrossSectionalScorer.default_v2()
    with pytest.raises(ValueError, match="不支持 market_mode"):
        scorer.score("crash", {})


def test_rank_normalize_in_unit_interval():
    """rank 归一化到 [0, 1]"""
    scorer = CrossSectionalScorer.default_v2()
    factor_data = {
        f"code_{i}": _make_ohlcv(60, start_price=1.0 + i * 0.1)
        for i in range(5)
    }
    result = scorer.score("trend_up", factor_data)
    # 检查 rank_details
    for code, ranks in result.rank_details.items():
        for fname, r in ranks.items():
            if not np.isnan(r):
                assert 0.0 <= r <= 1.0, f"{code}/{fname} rank {r} 超出 [0,1]"


def test_has_data_method():
    """has_data：是否有有效 score"""
    scorer = CrossSectionalScorer.default_v2()
    # 至少 2 只 ETF 才能横截面排名
    factor_data = {
        "510300": _make_ohlcv(60, start_price=4.0, trend=0.001),
        "515050": _make_ohlcv(60, start_price=1.5, trend=0.005),
    }
    result = scorer.score("trend_up", factor_data)
    assert result.has_data() is True


def test_composite_handles_partial_nan():
    """部分因子 NaN → composite 仍能算出（按有效因子归一化）"""
    # 这个测试通过空 dataframe 模拟（compute 返回 NaN）
    scorer = CrossSectionalScorer.default_v2()
    factor_data = {
        "510300": _make_ohlcv(60, start_price=4.0),
        "515050": _make_ohlcv(60, start_price=1.5),
        "empty": pd.DataFrame(),  # 空数据 → 全 NaN
    }
    result = scorer.score("trend_up", factor_data)
    # 510300/515050 应有 score，empty 应 NaN
    assert not np.isnan(result.scores["510300"])
    assert not np.isnan(result.scores["515050"])
    assert np.isnan(result.scores["empty"])