"""
scripts/check_ic_decay.py — US-010 季度 IC 巡检（规则 27）

用途：
    对比上季度 vs 本季度 IC，识别 |ΔIC| > 0.03 或 IR < 0.5 的衰减因子。
    输出 reports/ic_decay_YYYYMMDD.md（按规则 13 Grinold 经验值）。

被谁调用（按规则 18 / v1 L118）：
    - cron 每 90 天自动跑（US-011 配置）
    - 钉钉推送（按规则 4.3：警告信息也发送）
    - tests/integration/alpha/test_ic_decay.py（5/5 测试）

使用方式：
    python scripts/check_ic_decay.py
    python scripts/check_ic_decay.py --threshold-delta 0.03 --threshold-ir 0.5
    python scripts/check_ic_decay.py --report-only

业界参考（按规则 13）：
    - Grinold & Kahn 2000 *Active Portfolio Management* Ch 4 (|ΔIC| > 0.03 经验值)
    - López de Prado 2018 *Advances in Financial ML* Ch 16 (PBO 防过拟合)
    - WorldQuant 101 Alphas paper (Kakushadze 2016) (季度因子评估)

数据源（按规则 15/16）：
    - data/factor_icir_history.csv（US-008 写入，append 模式）
    - 不新建表（数据已有，避免冗余）
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

HISTORY_CSV = PROJECT_ROOT / "data" / "factor_icir_history.csv"
REPORTS_DIR = PROJECT_ROOT / "reports"

# 阈值（Grinold 经验值，按规则 13 标注来源）
DEFAULT_DELTA_THRESHOLD = 0.03   # |ΔIC| 超过 0.03 报警
DEFAULT_IR_THRESHOLD = 0.5       # IR 绝对值 < 0.5 报警（基本失效）


def load_history() -> list[dict]:
    """从 history CSV 读所有记录（按 eval_date 排序）."""
    if not HISTORY_CSV.exists():
        return []
    rows = []
    with open(HISTORY_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append({
                    "factor_name": row["factor_name"],
                    "ic": float(row["ic"]) if row.get("ic") else None,
                    "ir": float(row["ir"]) if row.get("ir") else None,
                    "eval_date": row.get("eval_date", ""),
                    "benchmark": row.get("benchmark", ""),
                })
            except (ValueError, KeyError):
                continue
    return rows


def group_by_run(rows: list[dict]) -> list[list[dict]]:
    """按 eval_date 分组，每次跑（eval_date 相同）一组."""
    runs = {}
    for row in rows:
        date = row["eval_date"]
        runs.setdefault(date, []).append(row)
    # 按日期排序
    sorted_dates = sorted(runs.keys())
    return [runs[d] for d in sorted_dates]


def detect_decay(
    current_run: list[dict],
    previous_run: list[dict],
    delta_threshold: float = DEFAULT_DELTA_THRESHOLD,
    ir_threshold: float = DEFAULT_IR_THRESHOLD,
) -> list[dict]:
    """对比两次跑的 IC，识别衰减因子.

    Returns:
        衰减因子列表，每个含: factor_name, old_ic, new_ic, delta_ic, old_ir, new_ir, alert_reason
    """
    prev_map = {r["factor_name"]: r for r in previous_run}
    decayed = []
    for cur in current_run:
        fname = cur["factor_name"]
        if fname not in prev_map:
            continue
        prev = prev_map[fname]
        # 跳过 NaN
        if cur["ic"] is None or prev["ic"] is None:
            continue
        delta_ic = cur["ic"] - prev["ic"]
        abs_delta = abs(delta_ic)
        cur_ir = cur["ir"] if cur["ir"] is not None else 0
        prev_ir = prev["ir"] if prev["ir"] is not None else 0

        reasons = []
        if abs_delta > delta_threshold:
            reasons.append(f"|ΔIC|={abs_delta:.4f} > {delta_threshold}")
        if abs(cur_ir) < ir_threshold:
            reasons.append(f"|IR|={abs(cur_ir):.4f} < {ir_threshold}")
        if reasons:
            decayed.append({
                "factor_name": fname,
                "old_ic": prev["ic"],
                "new_ic": cur["ic"],
                "delta_ic": delta_ic,
                "old_ir": prev_ir,
                "new_ir": cur_ir,
                "ic_decay_alert": True,
                "alert_reasons": reasons,
            })
    return decayed


def generate_report(
    decayed: list[dict],
    current_run: list[dict],
    previous_run: list[dict] | None,
) -> str:
    """生成 Markdown 报告（按规则 13 业界惯例）."""
    today = datetime.now().strftime("%Y-%m-%d")
    report = [
        f"# 季度 IC 巡检报告 ({today})",
        "",
        f"## 概况",
        f"- 巡检因子数: {len(current_run)}",
        f"- 上次巡检因子数: {len(previous_run) if previous_run else 0}",
        f"- 衰减因子数: {len(decayed)}",
        "",
    ]
    if not decayed:
        report.extend([
            "## ✅ 所有因子健康",
            "",
            "本次巡检未发现 IC 衰减。Grinold 阈值: |ΔIC| > 0.03 或 |IR| < 0.5。",
            "",
        ])
    else:
        report.extend([
            f"## ⚠️ 衰减因子（{len(decayed)} 个）",
            "",
            "| 因子 | 旧 IC | 新 IC | ΔIC | 旧 IR | 新 IR | 报警原因 |",
            "|------|------:|------:|----:|------:|------:|----------|",
        ])
        for d in decayed:
            reasons = " / ".join(d["alert_reasons"])
            report.append(
                f"| `{d['factor_name']}` | {d['old_ic']:+.4f} | {d['new_ic']:+.4f} | "
                f"{d['delta_ic']:+.4f} | {d['old_ir']:+.4f} | {d['new_ir']:+.4f} | {reasons} |"
            )
        report.append("")
        report.extend([
            "## 建议",
            "",
            "1. **优先关注 |ΔIC| > 0.05 的因子**（规则 13 严格阈值）",
            "2. **IR < 0.5 的因子**建议降权或弃用",
            "3. **α 池调整**：从核心池移到参考池（规则 21 标记，不删数据）",
            "4. **下次巡检**：(90 天后)",
            "",
        ])
    return "\n".join(report)


def main() -> int:
    parser = argparse.ArgumentParser(description="v3 mission US-010: 季度 IC 巡检")
    parser.add_argument("--threshold-delta", type=float, default=DEFAULT_DELTA_THRESHOLD,
                        help=f"|ΔIC| 阈值 (默认 {DEFAULT_DELTA_THRESHOLD})")
    parser.add_argument("--threshold-ir", type=float, default=DEFAULT_IR_THRESHOLD,
                        help=f"|IR| 阈值 (默认 {DEFAULT_IR_THRESHOLD})")
    parser.add_argument("--output", type=Path, default=None,
                        help="报告输出路径（默认 reports/ic_decay_YYYYMMDD.md）")
    parser.add_argument("--report-only", action="store_true",
                        help="只生成报告，不返回非 0 exit code")
    parser.add_argument("--dingtalk-format", action="store_true",
                        help="输出钉钉消息格式（按规则 4.3 警告信息推送）")
    args = parser.parse_args()

    print(f"=== US-010 季度 IC 巡检 ===")
    print(f"阈值: |ΔIC| > {args.threshold_delta}, |IR| < {args.threshold_ir}")

    # 1) 加载历史
    print(f"\n[1/3] 加载 history CSV...")
    rows = load_history()
    if not rows:
        print("  ⚠ history CSV 空，需要先跑 run_factor_evaluation.py ≥ 2 次")
        return 1
    runs = group_by_run(rows)
    print(f"  共 {len(runs)} 次跑（最新: {runs[-1][0]['eval_date']}）")

    if len(runs) < 2:
        print(f"  ⚠ 只有 {len(runs)} 次跑，需要 ≥ 2 次才能对比 IC 衰减")
        return 1

    # 2) 对比末两次
    print(f"\n[2/3] 对比 {runs[-2][0]['eval_date']} vs {runs[-1][0]['eval_date']}...")
    decayed = detect_decay(runs[-1], runs[-2], args.threshold_delta, args.threshold_ir)
    print(f"  衰减因子数: {len(decayed)}")

    # 3) 生成报告
    print(f"\n[3/3] 生成报告...")
    report = generate_report(decayed, runs[-1], runs[-2])
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output is None:
        today = datetime.now().strftime("%Y%m%d")
        report_path = REPORTS_DIR / f"ic_decay_{today}.md"
    else:
        report_path = args.output
    report_path.write_text(report, encoding="utf-8")
    print(f"  写报告: {report_path}")

    # 4) 钉钉消息格式（按规则 4.3 警告信息也发送）
    if args.dingtalk_format:
        dingtalk_msg = format_dingtalk_message(decayed, runs[-1], runs[-2])
        print(f"\n=== 钉钉消息格式（按规则 4.3）===")
        print(dingtalk_msg)

    if decayed and not args.report_only:
        return 2  # 报警（按 cron 退出码惯例：0=OK, 1=warn, 2=critical）
    return 0


def format_dingtalk_message(decayed: list[dict], current_run: list[dict], previous_run: list[dict]) -> str:
    """生成钉钉消息格式（Markdown，按规则 4.3 警告信息）.

    触发条件：有衰减因子就发（按规则 4.3 "警告信息也发送"）。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    if not decayed:
        return f"✅ 季度 IC 巡检 ({today})：所有因子健康"

    lines = [
        f"## ⚠️ 季度 IC 巡检报警 ({today})",
        "",
        f"**衰减因子数**: {len(decayed)}",
        f"**对比周期**: {previous_run[0]['eval_date']} → {current_run[0]['eval_date']}",
        "",
        "| 因子 | 旧IC | 新IC | ΔIC | 旧IR | 新IR |",
        "|------|------:|------:|----:|------:|------:|",
    ]
    for d in decayed[:5]:  # 钉钉消息长度限制，只列 top 5
        lines.append(
            f"| `{d['factor_name']}` | {d['old_ic']:+.4f} | {d['new_ic']:+.4f} | "
            f"{d['delta_ic']:+.4f} | {d['old_ir']:+.4f} | {d['new_ir']:+.4f} |"
        )
    if len(decayed) > 5:
        lines.append(f"| ... | (共 {len(decayed)} 个衰减因子) | | | | |")
    lines.extend([
        "",
        f"详细报告: `reports/ic_decay_{today.replace('-', '')}.md`",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
