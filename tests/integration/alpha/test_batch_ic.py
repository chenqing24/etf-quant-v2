"""
tests/integration/alpha/test_batch_ic.py — IC/IR 集成测试（US-013）

按规则 5.1（关键路径测试覆盖）：
    - 多因子批量 IC/IR 评估
    - 跨多 ETF（code 分组）
    - 验证 IC 序列与 IR 计算
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from etf_quant.alpha.analysis import BatchICEvaluator, calculate_ic, calculate_ir


@pytest.fixture
def multi_etf_df() -> pd.DataFrame:
    """构造 5 只 ETF × 200 天的样本数据。"""
    np.random.seed(42)
    n_etfs = 5
    n_days = 200
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    rows = []
    for i in range(n_etfs):
        code = f"{510000 + i:06d}"
        close = pd.Series(100 + np.cumsum(np.random.randn(n_days)))
        f1 = close / close.shift(5) - 1.0
        f2 = close.rolling(20).std() / close.rolling(40).std() - 1.0
        for j in range(n_days):
            rows.append({
                "code": code,
                "date": dates[j],
                "close": close[j],
                "M2_momentum_5d": f1.iloc[j] if pd.notna(f1.iloc[j]) else 0.0,
                "W4_rv": f2.iloc[j] if pd.notna(f2.iloc[j]) else 0.0,
            })
    return pd.DataFrame(rows)


def test_calculate_ic_perfect_correlation():
    """完全正相关 → IC = 1.0。"""
    f = pd.Series([1, 2, 3, 4, 5], index=pd.date_range("2024-01-01", periods=5))
    r = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5], index=pd.date_range("2024-01-01", periods=5))
    assert abs(calculate_ic(f, r) - 1.0) < 1e-6


def test_calculate_ic_perfect_negative():
    """完全负相关 → IC = -1.0。"""
    f = pd.Series([1, 2, 3, 4, 5], index=pd.date_range("2024-01-01", periods=5))
    r = pd.Series([0.5, 0.4, 0.3, 0.2, 0.1], index=pd.date_range("2024-01-01", periods=5))
    assert abs(calculate_ic(f, r) - (-1.0)) < 1e-6


def test_calculate_ir_basic():
    """IR = mean / std（pd.Series.std() ddof=1，与 np.std 不同）。"""
    ic_list = [0.05, 0.04, 0.06, 0.03, 0.05]
    ir, std = calculate_ir(ic_list)
    s = pd.Series(ic_list)
    expected_ir = s.mean() / s.std()  # pd 默认 ddof=1
    expected_std = s.std()
    assert ir == pytest.approx(expected_ir, rel=1e-3)
    assert std == pytest.approx(expected_std, rel=1e-3)


def test_calculate_ir_empty():
    """空列表 → NaN。"""
    ir, std = calculate_ir([])
    assert np.isnan(ir) and np.isnan(std)


def test_calculate_ir_single():
    """单值 → 无法算 std → NaN。"""
    ir, std = calculate_ir([0.05])
    assert np.isnan(ir)


def test_batch_evaluator_runs(multi_etf_df):
    """批量评估在 5 ETF 上跑通。"""
    evaluator = BatchICEvaluator(
        factor_names=["M2_momentum_5d", "W4_rv"],
        forward_window=5,
        min_samples=2,
    )
    results = evaluator.evaluate(multi_etf_df)
    assert len(results) == 2
    for r in results:
        assert r.factor_name in ("M2_momentum_5d", "W4_rv")
        assert r.sample_count > 0


def test_batch_evaluator_to_dataframe(multi_etf_df):
    """结果转 DataFrame。"""
    evaluator = BatchICEvaluator(
        factor_names=["M2_momentum_5d"],
        forward_window=5,
        min_samples=2,
    )
    results = evaluator.evaluate(multi_etf_df)
    df = evaluator.to_dataframe(results)
    assert len(df) == 1
    assert "ic" in df.columns
    assert "ir" in df.columns
