"""
test_holding_ranker.py — 持仓 Sharpe 排名单元测试（L321 教训 P1-1）

修复前：run_daily 决策不查 Sharpe 排名
修复后：持仓在 universe 末位（后 30%）→ 触发 SELL 评估
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestIsHoldingInBottom:
    """L321 教训 P1-1 核心：末位判断逻辑"""

    def _mk(self, rank, n=14, sharpe=0.0):
        from etf_quant.rank.holding_ranker import HoldingRanking
        return HoldingRanking(
            code="X", sharpe=sharpe, return_pct=0.0, max_drawdown=0.0,
            rank_in_universe=rank, universe_size=n, status="ok",
        )

    def test_rank_0_is_bottom_30_percent(self):
        from etf_quant.rank.holding_ranker import is_holding_in_bottom
        # N=14, bottom_ratio=0.3 → threshold_rank=4
        # rank=0,1,2,3 在末位
        rk = {"X": self._mk(rank=0, n=14)}
        assert is_holding_in_bottom("X", rk, 0.3) is True

    def test_rank_4_is_not_bottom_30_percent(self):
        from etf_quant.rank.holding_ranker import is_holding_in_bottom
        rk = {"X": self._mk(rank=4, n=14)}
        assert is_holding_in_bottom("X", rk, 0.3) is False

    def test_rank_top_not_in_bottom(self):
        from etf_quant.rank.holding_ranker import is_holding_in_bottom
        rk = {"X": self._mk(rank=13, n=14)}
        assert is_holding_in_bottom("X", rk, 0.3) is False

    def test_missing_code_returns_false(self):
        from etf_quant.rank.holding_ranker import is_holding_in_bottom
        assert is_holding_in_bottom("X", {}, 0.3) is False

    def test_empty_universe_returns_false(self):
        from etf_quant.rank.holding_ranker import is_holding_in_bottom
        rk = {"X": self._mk(rank=0, n=0)}
        assert is_holding_in_bottom("X", rk, 0.3) is False

    def test_512170_scenario_rank_0_of_14(self):
        """L321 教训核心场景：512170 是 core 池 Sharpe 末位"""
        from etf_quant.rank.holding_ranker import is_holding_in_bottom
        rk = {"512170": self._mk(rank=0, n=14, sharpe=-0.67)}
        assert is_holding_in_bottom("512170", rk, 0.3) is True

    def test_515050_scenario_rank_top_of_14(self):
        """L321 教训核心场景：515050 是 core 池 Sharpe 最佳"""
        from etf_quant.rank.holding_ranker import is_holding_in_bottom
        rk = {"515050": self._mk(rank=13, n=14, sharpe=1.07)}
        assert is_holding_in_bottom("515050", rk, 0.3) is False

    def test_bottom_ratio_50_percent(self):
        """bottom_ratio=0.5：后 50% = rank < N/2"""
        from etf_quant.rank.holding_ranker import is_holding_in_bottom
        # N=10, bottom_ratio=0.5 → threshold_rank=5
        rk = {"X": self._mk(rank=4, n=10)}
        assert is_holding_in_bottom("X", rk, 0.5) is True
        rk = {"X": self._mk(rank=5, n=10)}
        assert is_holding_in_bottom("X", rk, 0.5) is False


class TestRankHoldingsBySharpe:
    """真实回测排名（受 9.0.3 pytest buffer 卡死 L318 影响，单文件测试独立）"""

    def test_empty_codes_returns_empty(self):
        from etf_quant.rank.holding_ranker import rank_holdings_by_sharpe
        # 不调用回测（空列表）
        result = rank_holdings_by_sharpe.__wrapped__ if hasattr(rank_holdings_by_sharpe, '__wrapped__') else rank_holdings_by_sharpe
        # mock 真实回测避免 buffer 问题
        with patch("etf_quant.rank.holding_ranker._run_single_sharpe") as mock_run:
            mock_run.return_value = {
                "code": "X", "sharpe": None, "return_pct": None,
                "max_drawdown": None, "rank_in_universe": -1,
                "universe_size": 0, "status": "ok",
            }
            r = rank_holdings_by_sharpe("data/etf.db", [])
            assert r == {}
