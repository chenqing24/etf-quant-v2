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

    # 5.5 L321 教训 P1-1：持仓 Sharpe 排名（核心池 vs 持仓）
    # 仅在持仓非空时跑（避免空仓白耗 30s）
    holding_ranks = None
    rank_warning = None
    if holdings_guide:
        try:
            from etf_quant.rank.holding_ranker import (
                rank_holdings_by_sharpe, is_holding_in_bottom,
            )
            holding_codes = [h.code for h in holdings_guide]
            # 核心池全集 + 持仓（即使持仓不在 core 池也排名）
            all_codes = list(set(core_codes + holding_codes))
            holding_ranks = rank_holdings_by_sharpe(db_path=db_path, codes=all_codes)
        except Exception as e:
            rank_warning = f"持仓排名失败: {type(e).__name__}: {str(e)[:100]}"
            warnings.append(rank_warning)

    # 6. 决策（v2 简化：基于 holdings_count + market_mode + Sharpe 排名）
    # L297 教训：market_mode 真实检测，crash 强制空仓，range_bound 只持有不买入
    # L321 教训 P1-1：持仓在 universe 末位 → 触发 SELL 评估（不强制 T+0）
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
    else:
        # P1-1 修复：检查持仓是否在 universe 末位（后 30%）
        sell_candidates = []
        if holding_ranks:
            for h in holdings_guide:
                if is_holding_in_bottom(h.code, holding_ranks, bottom_ratio=0.3):
                    r = holding_ranks[h.code]
                    sell_candidates.append({
                        "code": h.code,
                        "reason": f"持仓 Sharpe 末位（rank={r['rank_in_universe']}/{r['universe_size']}，"
                                  f"sharpe={r['sharpe']:.2f}），建议减仓评估"
                    })
        if sell_candidates:
            # 末位持仓 + 非崩盘 → SELL 评估（不强制，提示风险）
            decision = "SELL"
            buy_candidates = []
        elif market_mode == "range_bound":
            # 震荡市：只持有不买入（避免被套）
            decision = "HOLD"
            buy_candidates = []
        else:
            # trend_up / trend_down：持有 + 趋势跟随
            decision = "HOLD"
            buy_candidates = []

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
    """运行完整评估（多时段回测）。

    修复 P0-3（L321 教训）：
    - 旧实现：只返回 validator.config（占位，SKILL.md 文档与实现不符）
    - 新实现：调用 RealBacktestEngine 跑全部 core 池 + ComprehensiveValidator 4 验证器
    - 返回结构：validator_config + real_backtest_results + validation_result + summary

    业界参考：
    - 12-Factor App § IV Backing Services：eval 是薄包装
    - Cargo/Go CLI：子命令 = 子功能
    - Sphinx doc + 实际行为一致（Read the Docs 最佳实践）

    注意：ComprehensiveValidator 需要每个 result 含 etf_code/test_return/sharpe/max_drawdown
    RealBacktestEngine 输出含 etf_code(start) test_period(start~end) train_period（隐含 full）test_return
    这里 train_period = test_period = 完整回测（v2 简化：等效 in-sample）
    """
    from etf_quant.backtest.backtesting_adapter import RealBacktestEngine
    from etf_quant.backtest.comprehensive_validator import ComprehensiveValidator
    from etf_quant.universe import ETFListLoader

    # 1. 跑全部 core 池真实回测
    engine = RealBacktestEngine()
    codes = [e.code for e in ETFListLoader().get_core_pool()]
    raw_results = []
    for i, code in enumerate(codes, 1):
        try:
            r = engine.run(code=code, db_path=db_path)
            raw_results.append({
                "etf_code": r.code,
                "train_period": (r.start, r.end),
                "test_period": (r.start, r.end),
                "train_return": r.total_return,
                "test_return": r.total_return,
                "sharpe": r.sharpe,
                "max_drawdown": r.max_drawdown,
                "n_trades": r.n_trades,
                "win_rate": r.win_rate,
            })
        except Exception as e:
            raw_results.append({"etf_code": code, "error": str(e)})

    # 2. 综合验证
    validator = ComprehensiveValidator()
    # 过滤掉有 error 的，构造 validator 期望的格式
    valid = [r for r in raw_results if "error" not in r]
    validation = validator.validate(valid) if valid else None

    # 3. 汇总
    if valid:
        n = len(valid)
        summary = {
            "n_etfs_tested": n,
            "n_etfs_passed": sum(1 for r in valid if r["test_return"] > 0),
            "avg_return": round(sum(r["test_return"] for r in valid) / n, 2),
            "avg_sharpe": round(sum(r["sharpe"] for r in valid) / n, 2),
            "avg_max_drawdown": round(sum(r["max_drawdown"] for r in valid) / n, 2),
        }
    else:
        summary = {"n_etfs_tested": 0, "error": "no valid backtest results"}

    return {
        "validator_config": validator.config,
        "real_backtest_results": raw_results,
        "validation_result": {
            "composite_score": validation.composite_score if validation else None,
            "pass": validation.pass_ if validation else False,
            "confidence": validation.confidence if validation else "UNKNOWN",
            "walk_forward_score": validation.walk_forward_score if validation else None,
            "monte_carlo_score": validation.monte_carlo_score if validation else None,
            "cross_etf_score": validation.cross_etf_score if validation else None,
            "consistency": validation.consistency if validation else None,
        } if validation else None,
        "summary": summary,
    }


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

    # 数据库路径（按 L321 教训：使用 resolve_db_path 兜底 cwd 漂移）
    from etf_quant.config.constants import resolve_db_path
    db_path = resolve_db_path(args.db_path)
    print(f"[etf-daily] db_path = {db_path}", file=sys.stderr)  # 启动时打印便于 debug

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
