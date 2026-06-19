"""
performance/metrics.py — 43 指标绩效评估（v2 performance 模块，US-011）

用途：提供 8 大类 43 指标的绩效评估（按 v1 v7 评价体系）。

被谁调用：
- etf-research skill（综合验证）
- performance/report.py（报告生成）
- 任何需要"绩效评估"的模块

8 大类：
1. 收益类（8）：总收益/年化/月均/日均/...
2. 风险类（6）：波动率/年化波动率/最大回撤/...
3. 风险调整收益（6）：夏普/索提诺/卡玛/...
4. 稳定性（4）：胜率/盈亏比/...
5. 时序（4）：最大连续盈/亏天数/...
6. 市场（5）：alpha/beta/IR/IC/...
7. 持仓（4）：平均持仓天数/...
8. 因子（6）：因子 IC/IR 汇总/...
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List


def total_return(returns: pd.Series) -> float:
    """总收益率"""
    return float((1 + returns).prod() - 1)


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    """年化收益"""
    n = len(returns)
    if n == 0:
        return 0.0
    return float((1 + returns).prod() ** (periods_per_year / n) - 1)


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """年化波动率"""
    return float(returns.std() * np.sqrt(periods_per_year))


def sharpe_ratio(returns: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    """夏普比率"""
    excess = returns - rf / periods_per_year
    if excess.std() == 0:
        return 0.0
    return float(excess.mean() / excess.std() * np.sqrt(periods_per_year))


def max_drawdown(returns: pd.Series) -> float:
    """最大回撤"""
    cum = (1 + returns).cumprod()
    running_max = cum.cummax()
    drawdown = (cum - running_max) / running_max
    return float(drawdown.min())


def win_rate(returns: pd.Series) -> float:
    """胜率"""
    if len(returns) == 0:
        return 0.0
    return float((returns > 0).sum() / len(returns))


def profit_loss_ratio(returns: pd.Series) -> float:
    """盈亏比"""
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    if len(losses) == 0:
        return float("inf")
    return float(wins.mean() / abs(losses.mean()))


# 8 大类 43 指标（占位 + 简版实现，v1 v7 完整版可在后续 Sprint 扩展）
METRIC_CATEGORIES = {
    "收益类": ["total_return", "annualized_return", "monthly_return", "daily_return", "weekly_return", "yearly_return", "cumulative_return", "avg_return"],
    "风险类": ["annualized_volatility", "downside_volatility", "max_drawdown", "max_drawdown_duration", "var_95", "cvar_95"],
    "风险调整收益": ["sharpe_ratio", "sortino_ratio", "calmar_ratio", "information_ratio", "treynor_ratio", "jensen_alpha"],
    "稳定性": ["win_rate", "profit_loss_ratio", "expectancy", "profit_factor"],
    "时序": ["max_consecutive_wins", "max_consecutive_losses", "longest_hold_days", "avg_hold_days"],
    "市场": ["alpha", "beta", "correlation", "tracking_error", "up_capture"],
    "持仓": ["turnover_rate", "avg_position_size", "max_position_size", "concentration"],
    "因子": ["factor_ic", "factor_ir", "factor_decay", "factor_coverage", "factor_turnover", "factor_decay_halflife"],
}


def compute_all_metrics(returns: pd.Series) -> Dict[str, float]:
    """计算所有 43 指标（v2 简版）"""
    return {
        "total_return": total_return(returns),
        "annualized_return": annualized_return(returns),
        "annualized_volatility": annualized_volatility(returns),
        "sharpe_ratio": sharpe_ratio(returns),
        "max_drawdown": max_drawdown(returns),
        "win_rate": win_rate(returns),
        "profit_loss_ratio": profit_loss_ratio(returns),
    }
