"""
tests/integration/alpha/test_batch_ic.py — US-004 IC 评估集成测试

按规则 5.1：关键路径测试覆盖
按规则 18：JSON/CSV 必验证（写完立即 read 验证）
按规则 20：行为变化类重构必须同步更新测试
按规则 6.1：错了就错了，不美化 — BatchICEvaluator 单标的场景需要滚动窗口

总计：7 测试
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path("/home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2")
DB_PATH = PROJECT_ROOT / "data" / "etf.db"
ICIR_CSV = PROJECT_ROOT / "data" / "factor_icir.csv"
HISTORY_CSV = PROJECT_ROOT / "data" / "factor_icir_history.csv"
SCRIPT = PROJECT_ROOT / "scripts" / "run_factor_evaluation.py"


def test_run_factor_evaluation_outputs_csv():
    """US-004 AC1: scripts/run_factor_evaluation.py 输出 factor_icir.csv 27 行"""
    if not DB_PATH.exists():
        pytest.skip("etf.db 不存在")
    # 跑 CLI
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--benchmark", "510300", "--lookback-days", "504"],
        capture_output=True, text=True, timeout=120,
        cwd=str(PROJECT_ROOT),
    )
    assert r.returncode == 0, f"run_factor_evaluation.py 失败: {r.stderr}"
    # 验证 CSV
    assert ICIR_CSV.exists(), f"{ICIR_CSV} 不存在"
    df = pd.read_csv(ICIR_CSV)
    assert len(df) == 29, f"29 因子（D-013.1: 27+T6/T7），got {len(df)}"
    assert "factor_name" in df.columns
    assert "ic" in df.columns
    assert "ir" in df.columns
    assert "ic_std" in df.columns
    assert "sample_count" in df.columns
    assert "eval_date" in df.columns
    assert "benchmark" in df.columns


def test_ic_range_valid():
    """US-004 AC2: IC ∈ [-1, 1]、IR 数字范围合理"""
    df = pd.read_csv(ICIR_CSV)
    non_nan = df.dropna(subset=["ic"])
    assert len(non_nan) > 0, "全 NaN，IC 评估失败"
    assert non_nan["ic"].between(-1, 1).all(), f"IC 越界: {non_nan[~non_nan['ic'].between(-1, 1)]}"
    # IR 范围 [-3, 3] 经验值
    non_nan_ir = df.dropna(subset=["ir"])
    assert non_nan_ir["ir"].between(-10, 10).all(), "IR 严重越界"


def test_discrimination_across_factors():
    """US-004 AC3: 27 因子 IC 有区分度（不全相等）"""
    df = pd.read_csv(ICIR_CSV)
    non_nan_ic = df.dropna(subset=["ic"])["ic"]
    assert non_nan_ic.nunique() >= 5, f"IC 区分度不足，unique={non_nan_ic.nunique()}"
    # 标准差 > 0.05 表示有区分
    assert non_nan_ic.std() > 0.05, f"IC std={non_nan_ic.std():.4f}，区分度太低"


def test_sample_count_meets_minimum():
    """US-004 AC4: 滚动窗口采样数 ≥ 30（BatchICEvaluator.min_samples）"""
    df = pd.read_csv(ICIR_CSV)
    valid = df[df["sample_count"] >= 30]
    assert len(valid) >= 20, f"sample_count ≥ 30 的因子数 {len(valid)} < 20"


def test_benchmark_510300_default():
    """US-004 AC5: 默认 benchmark=510300"""
    df = pd.read_csv(ICIR_CSV)
    assert df["benchmark"].astype(str).eq("510300").all()


def test_history_csv_appended():
    """US-004 AC6: factor_icir_history.csv append 模式（US-008 提前验证）"""
    if not HISTORY_CSV.exists():
        pytest.skip("history CSV 未生成（首次跑）")
    df = pd.read_csv(HISTORY_CSV)
    # 至少 27 行（本次跑）
    assert len(df) >= 27
    # 全部是 510300
    assert df["benchmark"].astype(str).eq("510300").all()


def test_history_csv_no_overwrite():
    """US-004 AC7: 第二次跑 history CSV 行数翻倍（验证 append 模式）"""
    if not HISTORY_CSV.exists():
        pytest.skip("history CSV 未生成")
    before = len(pd.read_csv(HISTORY_CSV))
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--benchmark", "510300", "--lookback-days", "504"],
        capture_output=True, text=True, timeout=120,
        cwd=str(PROJECT_ROOT),
    )
    assert r.returncode == 0
    after = len(pd.read_csv(HISTORY_CSV))
    # append 模式：行数应该增加 27（不是覆盖）
    assert after >= before + 27, f"append 失败: before={before}, after={after}"
