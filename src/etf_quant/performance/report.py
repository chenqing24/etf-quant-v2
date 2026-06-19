"""
performance/report.py — 绩效报告生成（v2 performance 模块）

用途：基于 metrics.py 计算结果生成绩效报告（结构化输出）。
被谁调用：etf-research skill / 任何需要"绩效报告"的模块。
"""
from __future__ import annotations

from typing import Dict
import pandas as pd

from .metrics import compute_all_metrics, METRIC_CATEGORIES


def generate_performance_report(returns: pd.Series) -> Dict:
    """生成绩效报告（结构化输出）"""
    metrics = compute_all_metrics(returns)
    return {
        "summary": {
            "total_return": f"{metrics['total_return']:.2%}",
            "annualized_return": f"{metrics['annualized_return']:.2%}",
            "max_drawdown": f"{metrics['max_drawdown']:.2%}",
            "sharpe_ratio": f"{metrics['sharpe_ratio']:.2f}",
            "win_rate": f"{metrics['win_rate']:.2%}",
        },
        "metrics": metrics,
        "n_categories": len(METRIC_CATEGORIES),
        "n_metrics": sum(len(v) for v in METRIC_CATEGORIES.values()),
    }
