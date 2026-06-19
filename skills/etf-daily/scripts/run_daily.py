"""
etf-daily/scripts/run_daily.py — ETF 每日决策入口

按 v2 设计（EXECUTION_REFACTOR_DESIGN.md + US-020）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 路径设置
_SKILL_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SKILL_ROOT.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from etf_quant.alpha.strategy_c21 import C21Strategy
from etf_quant.data_layer.trade_history_repo import TradeHistoryRepository
from etf_quant.data_layer.position_repo import PositionRepository
from etf_quant.data_layer.decision_snapshot_repo import (
    DecisionSnapshot, DecisionSnapshotRepository,
)
from etf_quant.risk.position_guide import PositionGuideAnalyzer


def run_daily(db_path: str) -> dict:
    """运行每日决策。

    Returns:
        决策报告 dict（含 model_name, strategy_name, holdings, signals）
    """
    # 1. 加载策略
    strategy = C21Strategy.from_config()

    # 2. 加载数据
    trade_repo = TradeHistoryRepository(db_path=db_path)
    position_repo = PositionRepository(db_path=db_path)
    snapshot_repo = DecisionSnapshotRepository(db_path=db_path)

    # 3. 评估持仓（PositionGuide）
    analyzer = PositionGuideAnalyzer(db_path=db_path)
    holdings_guide = analyzer.analyze_all(
        current_prices={}, market_regime="range_bound",
    )

    # 4. 决策快照
    _now = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    snapshot = DecisionSnapshot(
        snapshot_id=f"snap_{Path(db_path).stem}_{_now}",
        snapshot_time=_now,
        created_at=_now,
        trigger="daily",
        model_name="v2_sop",
        strategy_name=strategy.__class__.__name__,
        market_regime="range_bound",
    )
    snapshot_repo.insert(snapshot)

    return {
        "model_name": "v2_sop",
        "strategy_name": strategy.__class__.__name__,
        "holdings_count": len(holdings_guide),
        "snapshot_id": snapshot.snapshot_id,
    }


def run_eval(db_path: str) -> dict:
    """运行完整评估（多时段回测）。"""
    from etf_quant.backtest.comprehensive_validator import ComprehensiveValidator
    validator = ComprehensiveValidator()
    # v2 简化版：占位（实际回测结果由 US-021 注入）
    return {"validator_config": validator.config}


def run_history(db_path: str) -> dict:
    """查询历史交易。"""
    trade_repo = TradeHistoryRepository(db_path=db_path)
    position_repo = PositionRepository(db_path=db_path)
    trades = trade_repo.list_all(limit=20)
    positions = position_repo.list_all()
    return {
        "trades_count": len(trades),
        "positions_count": len(positions),
        "recent_trades": [
            {"date": t.date, "code": t.code, "action": t.action, "price": t.price}
            for t in trades[:5]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ETF Daily Skill")
    parser.add_argument(
        "mode", nargs="?", default="daily",
        choices=["daily", "eval", "history"],
        help="执行模式（默认 daily）",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="数据库路径（默认用 ETF_QUANT_DB_PATH 环境变量）",
    )
    args = parser.parse_args()

    # 数据库路径
    import os
    db_path = args.db_path or os.environ.get("ETF_QUANT_DB_PATH")
    if db_path is None:
        from etf_quant.config import constants
        db_path = constants.DB_PATH

    if args.mode == "daily":
        result = run_daily(db_path=db_path)
    elif args.mode == "eval":
        result = run_eval(db_path=db_path)
    elif args.mode == "history":
        result = run_history(db_path=db_path)
    else:
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
