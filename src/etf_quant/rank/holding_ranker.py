"""
rank/holding_ranker.py — 持仓 Sharpe 排名（按 L321 教训 P1-1）

用途：
    给定 db_path + 持仓代码列表，跑 RealBacktestEngine 拿 sharpe，
    按 sharpe 升序排名（rank=0 最差，rank=N-1 最佳）。
    run_daily.py 用此判断"持仓是否在 universe 末位 → 触发 SELL 评估"。

被谁调用：
    - skills/etf-daily/scripts/run_daily.py（每日决策）
    - tests/unit/test_holding_ranker.py

功能说明：
    - rank_holdings_by_sharpe(db_path, codes) -> Dict[code, {sharpe, return_pct, rank_in_universe, universe_size}]
    - rank_in_universe 0=最差, N-1=最佳
    - 单 ETF 回测失败时，sharpe=None, rank=universe_size（末位）

使用方式：
    from etf_quant.rank.holding_ranker import rank_holdings_by_sharpe
    rankings = rank_holdings_by_sharpe(db_path, ["512170", "515050"])
    # {"512170": {sharpe=-0.67, rank=0, ...}, "515050": {sharpe=1.07, rank=1, ...}}

依赖：
    - src/etf_quant/backtest/backtesting_adapter.py
    - src/etf_quant/config/constants.py
    - L321 教训 P1-1：当前持仓 512170 = Sharpe 末位，策略未触发 SELL

注意事项：
    - 单只 ETF 回测 ~3s，14 只约 30-60s
    - daily cron 跑要控制频率（建议缓存到 snapshot）
    - 若 db 缺 daily 数据，sharpe=None 不阻塞 daily

业界参考：
    - scipy.stats.rankdata：标准排名函数
    - Morningstar 星级评级：按 risk-adjusted return 排名
    - QuantConnect CoarseSelectionFunction：选 top-N by score
    - 12-Factor Process：stateless 函数易测
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, TypedDict


class HoldingRanking(TypedDict):
    """单只 ETF 的排名结果。"""

    code: str
    sharpe: Optional[float]
    return_pct: Optional[float]
    max_drawdown: Optional[float]
    rank_in_universe: int  # 0=最差, N-1=最佳
    universe_size: int
    status: str  # "ok" | "error" | "missing_data"


def _run_single_sharpe(db_path: Path, code: str) -> HoldingRanking:
    """跑单只 ETF 回测拿 sharpe（失败时 sharpe=None）。"""
    try:
        from etf_quant.backtest.backtesting_adapter import RealBacktestEngine
        engine = RealBacktestEngine()
        r = engine.run(code=code, db_path=db_path)
        return {
            "code": code,
            "sharpe": r.sharpe,
            "return_pct": r.total_return,
            "max_drawdown": r.max_drawdown,
            "rank_in_universe": -1,  # 占位，rank_holdings_by_sharpe 中赋值
            "universe_size": 0,  # 占位
            "status": "ok",
        }
    except Exception as e:
        return {
            "code": code,
            "sharpe": None,
            "return_pct": None,
            "max_drawdown": None,
            "rank_in_universe": -1,
            "universe_size": 0,
            "status": f"error: {type(e).__name__}: {str(e)[:100]}",
        }


def rank_holdings_by_sharpe(
    db_path: str,
    codes: List[str],
) -> Dict[str, HoldingRanking]:
    """对持仓代码跑回测，按 sharpe 升序排名。

    Args:
        db_path: v2 etf.db 路径（绝对）
        codes: 持仓代码列表

    Returns:
        Dict[code -> HoldingRanking]，包含 sharpe + rank_in_universe

    性能：
        - 单只 ~3s，N 只 ~3N s
        - 14 只约 30-60s

    失败处理：
        - 单只失败 → sharpe=None → 排名末位
        - 不抛异常阻塞 daily
    """
    db_path_p = Path(db_path)
    n = len(codes)
    raw: List[HoldingRanking] = []
    for code in codes:
        r = _run_single_sharpe(db_path_p, code)
        raw.append(r)

    # 按 sharpe 升序排名：sharpe 最低的 rank=0，最高的 rank=N-1
    # 失败（sharpe=None）排到末位
    sorted_codes = sorted(
        range(n),
        key=lambda i: (
            raw[i]["sharpe"] is None,  # None 排到末位
            raw[i]["sharpe"] if raw[i]["sharpe"] is not None else float("inf"),
        ),
    )
    rank_map = {idx: rank for rank, idx in enumerate(sorted_codes)}

    for i, r in enumerate(raw):
        r["rank_in_universe"] = rank_map[i]
        r["universe_size"] = n

    return {r["code"]: r for r in raw}


def is_holding_in_bottom(
    holding_code: str,
    rankings: Dict[str, HoldingRanking],
    bottom_ratio: float = 0.3,
) -> bool:
    """判断持仓是否在 universe 末位（默认后 30%）。

    Args:
        holding_code: 持仓 ETF 代码
        rankings: rank_holdings_by_sharpe 的输出
        bottom_ratio: 末位比例（默认 0.3 = 后 30%）

    Returns:
        True=持仓在末位（建议 SELL 评估）

    业界参考：
        - Morningstar 末位 10% 警告
        - Kelly Criterion：负 edge 应减仓
        - v8 SOP-17：SELL 决策需 min_hold + 末位 + 持续下跌 3 条件

    注意：本函数仅作"末位"判断，不直接下单（仍需 min_hold 检查 + 钉钉推送）
    """
    r = rankings.get(holding_code)
    if r is None or r["universe_size"] == 0:
        return False
    # rank 升序：0=最差, N-1=最佳
    # 末位 bottom_ratio = 后 30% → rank < N * bottom_ratio
    # e.g. N=14, bottom_ratio=0.3 → 末位 30% = rank < 4.2 → rank ∈ {0,1,2,3,4}
    threshold_rank = int(r["universe_size"] * bottom_ratio)
    return r["rank_in_universe"] < threshold_rank
