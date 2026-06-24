"""
test_walk_forward_adapter.py — Walk-forward 验证单元测试（L321 教训 P2-1）

修复前：run_real_backtest 只有单段 in-sample 回测（过拟合风险）
修复后：walk_forward 子命令跑滚动窗口，输出 OOS metrics
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestSplitWalkForwardWindows:
    """核心算法：把日期索引切分成滚动窗口"""

    def _mk_dates(self, n_days):
        return pd.date_range("2024-01-01", periods=n_days, freq="D")

    def test_no_dates_no_windows(self):
        from etf_quant.backtest.walk_forward_adapter import split_walk_forward_windows
        assert split_walk_forward_windows(pd.DatetimeIndex([])) == []

    def test_too_short_no_windows(self):
        """数据 < train + test → 无窗口"""
        from etf_quant.backtest.walk_forward_adapter import split_walk_forward_windows
        # train=6 月 + test=3 月 ≈ 270 天，少于 270 天不切分
        dates = self._mk_dates(60)  # 只 60 天
        windows = split_walk_forward_windows(dates, train_months=6, test_months=3, step_months=3)
        # 第一个 test_end = start + 9 月 = start + 270 天 > dates[-1]
        # 所以应返回 0 个
        assert len(windows) == 0

    def test_basic_window_count(self):
        """3 年数据 / 3 月 step = 至少 6 个窗口"""
        from etf_quant.backtest.walk_forward_adapter import split_walk_forward_windows
        dates = self._mk_dates(365 * 3)
        windows = split_walk_forward_windows(
            dates, train_months=6, test_months=3, step_months=3,
        )
        # 3 年 = 36 月，step=3 → ~12 个窗口（最后 1-2 个超出）
        assert len(windows) >= 6, f"应 ≥6 个窗口，实际: {len(windows)}"

    def test_window_boundaries_no_overlap(self):
        """窗口边界：test_start = train_end（不重叠）"""
        from etf_quant.backtest.walk_forward_adapter import split_walk_forward_windows
        dates = self._mk_dates(365 * 3)
        windows = split_walk_forward_windows(
            dates, train_months=6, test_months=3, step_months=3,
        )
        for w in windows:
            assert w["train_end"] == w["test_start"], \
                f"train_end 应等于 test_start: {w}"

    def test_window_step_respected(self):
        """步进 = step_months"""
        from etf_quant.backtest.walk_forward_adapter import split_walk_forward_windows
        dates = self._mk_dates(365 * 3)
        windows = split_walk_forward_windows(
            dates, train_months=6, test_months=3, step_months=3,
        )
        if len(windows) >= 2:
            # 第二个窗口的 train_start 应 = 第一个窗口的 train_start + 3 月
            delta = windows[1]["train_start"] - windows[0]["train_start"]
            # pd.DateOffset(months=3) 实际天数 ≈ 91 天（±1 天）
            assert 85 <= delta.days <= 92, f"步进应 ≈ 3 月，实际 {delta.days} 天"

    def test_window_in_test_range(self):
        """窗口 test_end 不超过数据范围"""
        from etf_quant.backtest.walk_forward_adapter import split_walk_forward_windows
        dates = self._mk_dates(365 * 3)
        windows = split_walk_forward_windows(
            dates, train_months=6, test_months=3, step_months=3,
        )
        for w in windows:
            assert w["test_end"] <= dates[-1], f"窗口超出数据: {w}"


class TestWalkForwardEngine:
    """WalkForwardEngine 端到端（用 mock 避免 buffer 卡死 L318）"""

    def test_engine_returns_walk_forward_result(self):
        from etf_quant.backtest.walk_forward_adapter import WalkForwardEngine, WalkForwardResult
        # mock _load_etf_daily 返回固定数据
        mock_df = pd.DataFrame(
            {"Close": [10.0] * 365 * 3},
            index=pd.date_range("2024-01-01", periods=365 * 3, freq="D"),
        )
        with patch("etf_quant.backtest.walk_forward_adapter._load_etf_daily", return_value=mock_df):
            # mock RealBacktestEngine.run
            mock_r = type("R", (), {
                "code": "512170", "start": "2024-01-01", "end": "2024-04-01",
                "total_return": 5.0, "annual_return": 10.0, "sharpe": 0.5,
                "max_drawdown": -10.0, "n_trades": 3, "win_rate": 50.0,
            })()
            with patch(
                "etf_quant.backtest.backtesting_adapter.RealBacktestEngine"
            ) as MockEngine:
                MockEngine.return_value.run.return_value = mock_r
                engine = WalkForwardEngine()
                result = engine.run(code="512170", db_path=Path("fake.db"))
                assert isinstance(result, WalkForwardResult)
                assert result.code == "512170"
                assert result.n_windows >= 6, f"应 ≥6 窗口，实际 {result.n_windows}"
                # 8 个窗口 mock 跑出来，OOS return 应 = 5.0
                assert result.oos_return == pytest.approx(5.0, abs=0.01)

    def test_engine_insufficient_data_returns_empty(self):
        """数据 < 60 天 → 返回空 result + warning"""
        from etf_quant.backtest.walk_forward_adapter import WalkForwardEngine
        mock_df = pd.DataFrame(
            {"Close": [10.0] * 30},
            index=pd.date_range("2024-01-01", periods=30, freq="D"),
        )
        with patch("etf_quant.backtest.walk_forward_adapter._load_etf_daily", return_value=mock_df):
            engine = WalkForwardEngine()
            result = engine.run(code="512170", db_path=Path("fake.db"))
            assert result.n_windows == 0
            assert len(result.warnings) > 0
            assert "数据不足" in result.warnings[0]

    def test_engine_load_failure_returns_empty(self):
        """加载失败 → 返回空 result + warning（不抛异常）"""
        from etf_quant.backtest.walk_forward_adapter import WalkForwardEngine
        with patch(
            "etf_quant.backtest.walk_forward_adapter._load_etf_daily",
            side_effect=Exception("db not found"),
        ):
            engine = WalkForwardEngine()
            result = engine.run(code="512170", db_path=Path("fake.db"))
            assert result.n_windows == 0
            assert "加载" in result.warnings[0] or "失败" in result.warnings[0]


class TestRunRealBacktestWalkForward:
    """CLI 子命令 walk_forward"""

    def test_subcommand_registered(self):
        import subprocess
        r = subprocess.run(
            ["python", "scripts/run_real_backtest.py", "walk_forward", "--help"],
            capture_output=True, text=True, timeout=30, cwd=str(_REPO),
        )
        assert r.returncode == 0
        assert "train-months" in r.stdout
        assert "test-months" in r.stdout
        assert "step-months" in r.stdout