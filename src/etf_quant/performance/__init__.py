"""
performance — 43 指标绩效评估（v2 US-011）

用途：8 大类 43 指标绩效评估 + 报告生成。
被谁调用：etf-research skill（综合验证）+ backtest 模块（绩效对比）。
按 v1 v7 评价体系：8 大类 43 指标。
"""
from .metrics import compute_all_metrics, METRIC_CATEGORIES
from .report import generate_performance_report

__all__ = ["compute_all_metrics", "METRIC_CATEGORIES", "generate_performance_report"]
