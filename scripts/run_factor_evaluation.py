"""
scripts/run_factor_evaluation.py — US-004 因子 IC/IR 评估 CLI

用途：
    对 27 因子在 510300（沪深 300 ETF）近 2 年日线上跑 IC/IR。
    510300 是用户拍板的大盘基准（v3 mission 2026-06-21）。
    前瞻窗口 5 日 + 504 交易日（约 2 年）。

被谁调用（按规则 18 / v1 L118）：
    - 散户 alpha 引导（按规则 25 推荐方案：'先跑 IC 看哪些因子有效'）
    - 业务自评 business_check.py（Sprint 2 US-005 验证 IC 输出）
    - 入库校验 US-007 IC 元数据填充
    - 季度巡检 US-010 check_ic_decay.py 历史数据源
    - tests/integration/alpha/test_batch_ic.py 集成测试

使用方式：
    python scripts/run_factor_evaluation.py
    python scripts/run_factor_evaluation.py --benchmark 510300 --forward-window 5 --lookback-days 504
    python scripts/run_factor_evaluation.py --output data/factor_icir.csv

业界参考（按规则 13）：
    - Grinold & Kahn 2000 *Active Portfolio Management* Ch 4 (IC/IR 定义)
    - López de Prado 2018 *Advances in Financial ML* Ch 16 (PBO/CPR 防过拟合)
    - WorldQuant 101 Alphas paper (Kakushadze 2016)

数据源（按规则 15/16.3）：
    - v2 仓 daily 表（69,480 行历史价，source='tencent'，按规则 16.3 排序首选）
    - 不新建 etf_price_history（数据已有，避免冗余）
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# 让 Python 找到 etf_quant 包
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from etf_quant.alpha.factors import FACTOR_REGISTRY, list_factors, get_factor  # noqa: E402
from etf_quant.alpha.analysis.batch_ic import BatchICEvaluator, ICResult  # noqa: E402

DB_PATH = PROJECT_ROOT / "data" / "etf.db"
OUTPUT_CSV = PROJECT_ROOT / "data" / "factor_icir.csv"
HISTORY_CSV = PROJECT_ROOT / "data" / "factor_icir_history.csv"


def load_daily(benchmark: str, lookback_days: int) -> pd.DataFrame:
    """
    从 etf.db daily 表加载 benchmark 近 lookback_days 交易日 OHLCV。

    Args:
        benchmark: ETF code（510300 / sh510300 都接受）
        lookback_days: 前 N 个交易日

    Returns:
        DataFrame with columns: code, date, open, high, low, close, volume
    """
    # 尝试多种 code 格式
    candidates = [benchmark]
    if not benchmark.startswith("sh") and not benchmark.startswith("sz"):
        candidates.append(f"sh{benchmark}")
        candidates.append(f"sz{benchmark}")
    elif benchmark.startswith("sh") or benchmark.startswith("sz"):
        candidates.append(benchmark[2:])

    conn = sqlite3.connect(str(DB_PATH))
    placeholders = ",".join("?" * len(candidates))
    query = f"""
        SELECT code, date, open, high, low, close, volume
        FROM daily
        WHERE code IN ({placeholders})
        ORDER BY date DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=tuple(candidates) + (lookback_days,))
    conn.close()
    if df.empty:
        raise ValueError(f"No daily data for {benchmark} (candidates: {candidates})")
    # 排序为时间正序
    df = df.sort_values("date").reset_index(drop=True)
    return df


def compute_factors(df: pd.DataFrame, factor_names: list[str]) -> pd.DataFrame:
    """
    对每只 ETF（实际只有 1 只 benchmark）计算所有因子的因子值。

    Returns:
        原 df + 每个因子 1 列
    """
    df = df.copy()
    for name in factor_names:
        try:
            factor = get_factor(name)
            result = factor(df)
            df[name] = result.series.values
        except Exception as e:
            print(f"  ⚠ {name}: {e}", file=sys.stderr)
            df[name] = np.nan
    return df


def main():
    parser = argparse.ArgumentParser(
        description="v3 mission US-004: 27 因子在 benchmark 近 2 年 IC/IR 评估"
    )
    parser.add_argument(
        "--benchmark", default="510300",
        help="ETF code（默认 510300 沪深 300，用户拍板大盘基准）"
    )
    parser.add_argument(
        "--forward-window", type=int, default=5,
        help="前瞻 N 日收益（默认 5，中期持仓匹配散户节奏）"
    )
    parser.add_argument(
        "--lookback-days", type=int, default=504,
        help="回看 N 个交易日（默认 504 ≈ 2 年）"
    )
    parser.add_argument(
        "--output", type=Path, default=OUTPUT_CSV,
        help=f"输出 CSV 路径（默认 {OUTPUT_CSV.name}）"
    )
    parser.add_argument(
        "--history", action="store_true",
        help="追加到 factor_icir_history.csv（US-008 默认开启）"
    )
    parser.add_argument(
        "--factors", nargs="+", default=None,
        help="要评估的因子列表（默认全 27 因子）"
    )
    args = parser.parse_args()

    factor_names = args.factors or list_factors()
    print(f"=== US-004 IC 评估 ===")
    print(f"benchmark: {args.benchmark}")
    print(f"前瞻窗口: {args.forward_window} 日")
    print(f"回看天数: {args.lookback_days} 交易日")
    print(f"因子数: {len(factor_names)}")

    # 1) 加载历史价
    print(f"\n[1/3] 加载 {args.benchmark} 日线...")
    df = load_daily(args.benchmark, args.lookback_days)
    print(f"  rows: {len(df)}, date range: {df['date'].iloc[0]} ~ {df['date'].iloc[-1]}")

    # 2) 算因子值
    print(f"\n[2/3] 计算 {len(factor_names)} 因子...")
    df_with_factors = compute_factors(df, factor_names)
    # 前瞻收益
    df_with_factors[f"fwd_ret_{args.forward_window}d"] = (
        df_with_factors["close"].pct_change(args.forward_window).shift(-args.forward_window)
    )
    # 实际行数
    valid_rows = df_with_factors.dropna(subset=[f"fwd_ret_{args.forward_window}d"] + factor_names, how="all")
    print(f"  valid rows: {len(valid_rows)}")

    # 3) 跑 BatchICEvaluator
    print(f"\n[3/3] IC/IR 评估...")
    evaluator = BatchICEvaluator(
        factor_names=factor_names,
        forward_window=args.forward_window,
        min_samples=30,
    )
    results = evaluator.evaluate(df_with_factors)

    # 写当前 CSV
    args.output.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # US-010: 含时分，避免同日合并
    rows = []
    for r in results:
        rows.append({
            "factor_name": r.factor_name,
            "ic": r.ic,
            "ir": r.ir,
            "ic_std": r.ic_std,
            "sample_count": r.sample_count,
            "forward_window": r.forward_window,
            "eval_date": today,
            "benchmark": args.benchmark,
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(args.output, index=False)
    print(f"  写 {args.output} ({len(df_out)} 行)")

    # 追加到 history（US-008 append 模式）
    history_path = HISTORY_CSV
    write_header = not history_path.exists()
    df_out.to_csv(history_path, mode="a", header=write_header, index=False)
    print(f"  追加到 {history_path}（header={write_header}）")

    # 打印 top/bottom 5
    print(f"\n=== IC 排名 (按 |IC| 降序) ===")
    df_sorted = df_out.dropna(subset=["ic"]).sort_values("ic", key=abs, ascending=False)
    for _, r in df_sorted.head(5).iterrows():
        print(f"  {r['factor_name']:20s}  IC={r['ic']:+.4f}  IR={r['ir']:+.4f}  n={r['sample_count']:.0f}")
    print("  ...")
    for _, r in df_sorted.tail(5).iterrows():
        print(f"  {r['factor_name']:20s}  IC={r['ic']:+.4f}  IR={r['ir']:+.4f}  n={r['sample_count']:.0f}")

    print(f"\n✓ US-004 完成: {len(results)} 因子 IC 评估，输出 {args.output}")


if __name__ == "__main__":
    main()
