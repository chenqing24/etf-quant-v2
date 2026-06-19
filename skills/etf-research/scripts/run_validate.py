"""
etf-research/scripts/run_validate.py — ETF 深度研究入口

按 v2 设计（US-021）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SKILL_ROOT.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from etf_quant.backtest.comprehensive_validator import (
    ComprehensiveValidator, DEFAULT_CONFIG,
)


def run_validate(backtest_results: list) -> dict:
    """运行综合验证（4 验证器）。"""
    validator = ComprehensiveValidator()
    result = validator.validate(backtest_results)
    return {
        "composite_score": result.composite_score,
        "pass_": result.pass_,
        "confidence": result.confidence,
        "walk_forward_score": result.walk_forward_score,
        "monte_carlo_score": result.monte_carlo_score,
        "cross_etf_score": result.cross_etf_score,
        "consistency": result.consistency,
        "warnings": result.warnings,
    }


def run_factor(backtest_results: list) -> dict:
    """因子分解。"""
    validator = ComprehensiveValidator()
    result = validator.validate(backtest_results)
    return {
        "weights": validator.config["weights"],
        "factors": {
            "walk_forward": result.walk_forward_score,
            "monte_carlo": result.monte_carlo_score,
            "cross_etf": result.cross_etf_score,
            "consistency": result.consistency,
        },
    }


def run_backtest(backtest_results: list) -> dict:
    """回测样本（最近 10 个）。"""
    return {
        "samples": backtest_results[-10:],
        "total": len(backtest_results),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ETF Research Skill")
    parser.add_argument(
        "action", nargs="?", default="validate",
        choices=["validate", "factor", "backtest"],
    )
    args = parser.parse_args()

    # 占位回测结果（实际由 etf-daily 注入）
    backtest_results = [
        {"etf_code": f"51{3000+i%10}", "train_period": ("2020-01-01", "2022-01-01"),
         "test_period": ("2022-01-01", "2023-01-01"),
         "train_return": 0.10, "test_return": 0.08 if i%3==0 else -0.04,
         "sharpe": 1.5, "max_drawdown": -0.10}
        for i in range(60)
    ]

    if args.action == "validate":
        result = run_validate(backtest_results)
    elif args.action == "factor":
        result = run_factor(backtest_results)
    elif args.action == "backtest":
        result = run_backtest(backtest_results)
    else:
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())