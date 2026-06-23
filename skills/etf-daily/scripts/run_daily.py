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
from etf_quant.universe import ETFListLoader
from etf_quant.monitor import DataHealthMonitor, MarketModeDetector


def run_daily(db_path: str) -> dict:
    """运行每日决策。

    Returns:
        决策报告 dict（含 model_name, strategy_name, market_mode, decision,
                       buy_candidates, sell_candidates, holdings, data_freshness, warnings）
    """
    # 1. 加载策略
    strategy = C21Strategy.from_config()

    # 2. 加载数据
    trade_repo = TradeHistoryRepository(db_path=db_path)
    position_repo = PositionRepository(db_path=db_path)
    snapshot_repo = DecisionSnapshotRepository(db_path=db_path)

    # 3. 评估持仓（PositionGuide，先用 market_mode 检测器拿到真实 regime）
    market_report = MarketModeDetector(db_path=db_path).detect()
    market_mode = market_report.mode  # L297 教训：基于外部数据判断，不用硬编码

    analyzer = PositionGuideAnalyzer(db_path=db_path)
    holdings_guide = analyzer.analyze_all(
        current_prices={}, market_regime=market_mode,
    )

    # 4. 数据健康检查
    health = DataHealthMonitor().check()
    data_freshness = f"距最新数据 {health.fresh_minutes:.0f} 分钟"
    warnings = list(health.issues)

    # 5. 加载 ETF 池
    universe = ETFListLoader()
    core_codes = [e.code for e in universe.get_core_pool()]

    # 6. 决策（v2 简化：基于 holdings_count + market_mode）
    # L297 教训：market_mode 真实检测，crash 强制空仓，range_bound 只持有不买入
    if market_mode == "crash":
        decision = "SELL"
        buy_candidates = []
        sell_candidates = [{"code": h.code if hasattr(h, 'code') else str(h),
                            "reason": f"崩盘市（{market_report.reason}），清仓避险"} for h in holdings_guide[:10]]
    elif len(holdings_guide) == 0:
        decision = "BUY"
        buy_candidates = [{"code": c, "score": 0.5} for c in core_codes[:5]]
        sell_candidates = []
    elif len(holdings_guide) > 5:
        decision = "SELL"
        buy_candidates = []
        sell_candidates = [{"code": h.code if hasattr(h, 'code') else str(h),
                            "reason": "持仓超过 5 只"} for h in holdings_guide[:3]]
    elif market_mode == "range_bound":
        # 震荡市：只持有不买入（避免被套）
        decision = "HOLD"
        buy_candidates = []
        sell_candidates = []
    else:
        # trend_up / trend_down：持有 + 趋势跟随
        decision = "HOLD"
        buy_candidates = []
        sell_candidates = []

    # 7. 决策快照
    _now = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    snapshot = DecisionSnapshot(
        snapshot_id=f"snap_{Path(db_path).stem}_{_now}",
        snapshot_time=_now,
        created_at=_now,
        trigger="daily",
        model_name="v2_sop",
        strategy_name=strategy.__class__.__name__,
        market_regime=market_mode,
    )
    snapshot_repo.insert(snapshot)

    return {
        "model_name": "v2_sop",
        "strategy_name": strategy.__class__.__name__,
        "timestamp": _now,
        "market_mode": market_mode,
        "decision": decision,
        "buy_candidates": buy_candidates,
        "sell_candidates": sell_candidates,
        "holdings_count": len(holdings_guide),
        "holdings_detail": [
            {"code": h.code if hasattr(h, 'code') else str(h)}
            for h in holdings_guide
        ],
        "data_freshness": data_freshness,
        "warnings": warnings,
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
