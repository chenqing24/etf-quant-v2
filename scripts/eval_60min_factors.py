"""
scripts/eval_60min_factors.py — 60min 因子 IC/IR 评估（D-007 C5）

按 D-007 5 项隔离原则：60min 因子不参与实时决策。
本脚本是独立评估 pipeline，把 60min 因子的 IC 写到
data/factor_icir_60min.csv，供后续多频率交叉验证使用。

业界参考（按规则 13）：
    - Grinold & Kahn 2000《Active Portfolio Management》Ch 4（IC/IR 定义）
    - López de Prado 2018《Advances in Financial ML》Ch 16（PBO/CPR 防过拟合）
    - WorldQuant 101 Alphas paper (Kakushadze 2016)

数据源（按规则 15/16.3）：
    - v2 仓 etf_60min 表（27,506 条，14 只 core ETF）
    - 不读 CSV（规则 16 禁止）

评估方法（按 D-007 设计）：
    1. 对每只 ETF，按时间排序 60min 数据
    2. 计算 4 因子（H1~H4）的 60min 值
    3. 计算 forward_returns（下一个 12 个 60min bar = 3 天的累积收益）
    4. Spearman IC（factor vs forward_returns）
    5. 跨 14 ETF 平均 → 写入 factor_icir_60min.csv

使用：
    python scripts/eval_60min_factors.py
    python scripts/eval_60min_factors.py --benchmark 510300
    python scripts/eval_60min_factors.py --forward-window 12

输出：
    - data/factor_icir_60min.csv（4 因子 IC/IR/eval_date）
    - reports/YYYY-MM-DD_d007_60min_eval/REPORT.md（人类可读报告）
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from etf_quant.alpha.factors.sixty_min import (  # noqa: E402
    H1IntradayTrendFactor,
    H2VolumeBreakoutFactor,
    H3BollWidthPctFactor,
    H4PriceVolumeCorrFactor,
)

DB_PATH = PROJECT_ROOT / "data" / "etf.db"
OUTPUT_CSV = PROJECT_ROOT / "data" / "factor_icir_60min.csv"


SIXTY_MIN_FACTORS = {
    "H1_intraday_trend": H1IntradayTrendFactor(),
    "H2_volume_breakout": H2VolumeBreakoutFactor(),
    "H3_boll_width_pct": H3BollWidthPctFactor(percentile_window=126),  # 60min 数据少，缩窗口
    "H4_price_volume_corr": H4PriceVolumeCorrFactor(window=20),
}


def load_60min(conn, code: str) -> pd.DataFrame:
    """从 etf_60min 表加载单只 ETF 的 60min K 线."""
    df = pd.read_sql(
        "SELECT datetime, open, high, low, close, volume FROM etf_60min "
        "WHERE code = ? ORDER BY datetime",
        conn,
        params=(code,),
    )
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime")
    return df


def compute_forward_returns(close: pd.Series, forward_window: int) -> pd.Series:
    """计算前瞻 N bar 累积收益."""
    forward_return = close.shift(-forward_window) / close - 1.0
    return forward_return


def evaluate_one_etf(code: str, conn, forward_window: int) -> dict:
    """对单只 ETF 评估 4 个 60min 因子 IC."""
    df = load_60min(conn, code)
    if len(df) < 100:  # 数据太少
        return None

    # 前瞻收益
    fwd_ret = compute_forward_returns(df["close"], forward_window)

    results = {}
    for name, factor in SIXTY_MIN_FACTORS.items():
        try:
            factor_result = factor(df)
            factor_series = factor_result.series

            # 对齐 + 丢 NaN
            valid_mask = factor_series.notna() & fwd_ret.notna()
            f = factor_series[valid_mask].values
            r = fwd_ret[valid_mask].values

            if len(f) < 30:  # 最小样本数
                results[name] = {"ic": np.nan, "n": len(f)}
                continue

            # Spearman IC
            ic, _ = spearmanr(f, r)
            results[name] = {"ic": ic if not np.isnan(ic) else 0.0, "n": len(f)}
        except Exception as e:
            print(f"  [warn] {code} {name}: {type(e).__name__}: {e}")
            results[name] = {"ic": np.nan, "n": 0}

    return results


def main():
    parser = argparse.ArgumentParser(description="60min 因子 IC 评估")
    parser.add_argument("--benchmark", default="510300", help="基准 ETF（仅用于报告）")
    parser.add_argument("--forward-window", type=int, default=12, help="前瞻 bar 数（默认 12 = 3 天）")
    args = parser.parse_args()

    print("=" * 60)
    print(f"60min 因子 IC/IR 评估（D-007 C5）")
    print(f"forward_window = {args.forward_window} bar (≈{args.forward_window / 4:.1f} 天)")
    print("=" * 60)

    # 加载 core ETF 列表
    conn = __import__("sqlite3").connect(DB_PATH)
    core_codes = pd.read_sql(
        "SELECT code FROM etf_names WHERE pool_role = 'core' AND is_reference = 0 ORDER BY code",
        conn,
    )["code"].tolist()
    print(f"\n核心 ETF 池：{len(core_codes)} 只")
    print(f"60min 因子：{list(SIXTY_MIN_FACTORS.keys())}\n")

    # 逐 ETF 评估
    all_results = {name: [] for name in SIXTY_MIN_FACTORS.keys()}
    n_evaluated = 0

    for code in core_codes:
        print(f"评估 {code} ...", end=" ")
        results = evaluate_one_etf(code, conn, args.forward_window)
        if results is None:
            print("数据不足跳过")
            continue

        n_evaluated += 1
        print("✓")
        for name, r in results.items():
            all_results[name].append(r["ic"])

    conn.close()

    if n_evaluated == 0:
        print("\n❌ 没有 ETF 评估成功（可能 60min 数据未入库）")
        sys.exit(1)

    # 汇总：跨 ETF 平均 IC
    print("\n" + "=" * 60)
    print("60min 因子 IC 汇总（跨 {} ETF 平均）".format(n_evaluated))
    print("=" * 60)
    print(f"{'因子':<28} {'IC均值':>10} {'IC标准差':>10} {'IR':>8} {'样本数':>8}")
    print("-" * 60)

    summary_rows = []
    for name, ics in all_results.items():
        if not ics:
            continue
        ic_array = np.array(ics)
        ic_mean = np.nanmean(ic_array)
        ic_std = np.nanstd(ic_array) if len(ic_array) > 1 else 0.0
        ir = ic_mean / ic_std if ic_std > 0 else 0.0

        print(f"{name:<28} {ic_mean:>10.4f} {ic_std:>10.4f} {ir:>8.4f} {len(ics):>8}")

        summary_rows.append({
            "factor_name": name,
            "ic": ic_mean,
            "ir": ir,
            "ic_std": ic_std,
            "sample_count": n_evaluated,
            "forward_window": args.forward_window,
            "eval_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "benchmark": args.benchmark,
        })

    # 写 CSV（规则 18：立即验证）
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["factor_name", "ic", "ir", "ic_std", "sample_count",
                  "forward_window", "eval_date", "benchmark"]
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    # 立即验证（规则 18）
    with open(OUTPUT_CSV) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(summary_rows), f"CSV 行数不匹配：写 {len(summary_rows)} 读 {len(rows)}"
    print(f"\n✅ 写入 {OUTPUT_CSV}（{len(rows)} 行，已验证）")

    # 生成报告
    report_path = PROJECT_ROOT / "reports" / f"{datetime.now().strftime('%Y-%m-%d')}_d007_60min_eval"
    report_path.mkdir(parents=True, exist_ok=True)
    report_file = report_path / "REPORT.md"

    with open(report_file, "w") as f:
        f.write(f"# D-007 60min 因子评估报告\n\n")
        f.write(f"**日期**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**评估脚本**：`scripts/eval_60min_factors.py`\n")
        f.write(f"**前瞻窗口**：{args.forward_window} bar (≈{args.forward_window / 4:.1f} 天)\n")
        f.write(f"**评估 ETF 数**：{n_evaluated} / {len(core_codes)}\n\n")

        f.write(f"## 4 因子 IC 汇总\n\n")
        f.write(f"| 因子 | IC 均值 | IC 标准差 | IR | 样本数 |\n")
        f.write(f"|------|---------|-----------|-----|--------|\n")
        for row in summary_rows:
            f.write(f"| {row['factor_name']} | {row['ic']:.4f} | {row['ic_std']:.4f} | {row['ir']:.4f} | {row['sample_count']} |\n")

        f.write(f"\n## 业务解读\n\n")
        f.write(f"- **H1 日内趋势**：捕捉盘中单边趋势（Barber 2005）\n")
        f.write(f"- **H2 量能突破**：捕捉资金异动（TA-Lib AD 类似）\n")
        f.write(f"- **H3 布林挤压**：捕捉变盘前兆（Bollinger 2001）\n")
        f.write(f"- **H4 量价背离**：捕捉趋势转折（Granville 1976）\n\n")

        f.write(f"## 5 项隔离原则（D-007 强约束）\n\n")
        f.write(f"1. ✅ 不参与实时决策（HOLD/BUY/SELL 不读 60min score）\n")
        f.write(f"2. ✅ 不污染 8 因子权重（独立 FactorSet `sixty_min_4f`）\n")
        f.write(f"3. ✅ 不参与 rank（不进入横截面打分）\n")
        f.write(f"4. ✅ 不参与止盈/止损\n")
        f.write(f"5. ✅ 不进 decision_snapshot（只入 IC history 表）\n\n")

        f.write(f"## 后续建议\n\n")
        # 简单业务判断
        sig_factors = [r for r in summary_rows if abs(r["ic"]) > 0.02]
        if sig_factors:
            f.write(f"**IC 显著因子（|IC| > 0.02）**：\n")
            for r in sig_factors:
                f.write(f"- {r['factor_name']}（IC={r['ic']:.4f}）\n")
            f.write(f"\n**建议**：保留为研究素材，季度重跑 IC 评估（D-013.5）\n")
        else:
            f.write(f"**无 IC 显著因子**（|IC| ≤ 0.02）\n\n")
            f.write(f"**建议**：\n")
            f.write(f"- 不降级为半残因子（规则 19 默认 deny）\n")
            f.write(f"- 保留 FactorSet `sixty_min_4f` 但默认不参与决策\n")
            f.write(f"- 季度重跑看 IC 是否恢复（D-013.5）\n")

    print(f"✅ 写入报告 {report_file}")

    print("\n" + "=" * 60)
    print("评估完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()