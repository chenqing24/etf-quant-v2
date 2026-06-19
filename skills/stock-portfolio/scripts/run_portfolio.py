"""
stock-portfolio/scripts/run_portfolio.py — 持仓组合管理入口

按 v2 设计（US-023）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SKILL_ROOT.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))


def get_db_path() -> str:
    return os.environ.get("ETF_QUANT_DB_PATH", str(_REPO_ROOT / "data" / "etf.db"))


def run_status(db_path: str) -> dict:
    """当前持仓状态。"""
    from etf_quant.risk.position_guide import PositionGuideAnalyzer
    analyzer = PositionGuideAnalyzer(db_path=db_path)
    guides = analyzer.analyze_all(market_regime="range_bound")
    return {
        "holdings_count": len(guides),
        "guides": [
            {"code": g.code, "action": g.action, "reason": g.reason,
             "should_stop_loss": g.should_stop_loss,
             "should_take_profit": g.should_take_profit}
            for g in guides
        ],
    }


def run_rebalance(db_path: str) -> dict:
    """再平衡建议。"""
    from etf_quant.risk.position_guide import PositionGuideAnalyzer
    analyzer = PositionGuideAnalyzer(db_path=db_path)
    guides = analyzer.analyze_all(market_regime="range_bound")
    return {
        "actions": [
            {"code": g.code, "action": g.action, "reason": g.reason}
            for g in guides
            if g.action in ("STOP_LOSS", "TAKE_PROFIT", "EXPIRE_REVIEW", "CLEAR_LEGACY", "GO_CASH")
        ],
    }


def run_attribution(db_path: str) -> dict:
    """业绩归因（基于 trade_history）。"""
    from etf_quant.data_layer.trade_history_repo import TradeHistoryRepository
    trade_repo = TradeHistoryRepository(db_path=db_path)
    trades = trade_repo.list_all(limit=100)
    return {
        "total_trades": len(trades),
        "real_trades": sum(1 for t in trades if t.is_real == 1),
        "paper_trades": sum(1 for t in trades if t.is_paper == 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Stock Portfolio Skill")
    parser.add_argument("action", nargs="?", default="status", choices=["status", "rebalance", "attribution"])
    args = parser.parse_args()

    db_path = get_db_path()

    if args.action == "status":
        result = run_status(db_path)
    elif args.action == "rebalance":
        result = run_rebalance(db_path)
    elif args.action == "attribution":
        result = run_attribution(db_path)
    else:
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())