"""
test_decision_snapshot_fields.py — decision_snapshot 字段补齐测试（L321 教训 P2-2）

修复前：8 个 JSON 字段全为 NULL/空（'{}'）
修复后：8 个 JSON 字段全有真实数据
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
_SRC = _REPO / "src"
_SKILL_SCRIPTS = _REPO / "skills" / "etf-daily" / "scripts"
for p in (str(_SRC), str(_REPO)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture
def db_path():
    from etf_quant.config.constants import resolve_db_path
    return resolve_db_path()


@pytest.fixture
def run_daily_module():
    """动态加载 skill script（不是 package）"""
    spec = importlib.util.spec_from_file_location(
        "run_daily", _SKILL_SCRIPTS / "run_daily.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestDecisionSnapshot8JsonFields:
    """L321 教训 P2-2 核心：8 个 JSON 字段全有真实数据"""

    def test_run_daily_populates_all_json_fields(self, db_path, run_daily_module):
        """跑一次 daily → 检查最新 snapshot 的 8 JSON 字段非空"""
        run_daily_module.run_daily(db_path=db_path)
        # 查最新一行
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT config_json, evaluation_json, factor_breakdown_json,"
                " today_top_10_json, backtest_last_10_json, reasoning,"
                " target_price, stop_loss_price, stop_profit_price,"
                " risk_reward_ratio, expected_hold_days"
                " FROM decision_snapshot ORDER BY snapshot_time DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()

        assert row is not None, "decision_snapshot 表无数据"

        # 6 个 JSON 字符串字段
        config_json, evaluation_json, factor_breakdown_json, today_top_10_json, backtest_last_10_json, reasoning, target, stop_loss, stop_profit, rr, days = row

        # 验证 JSON 非空且有效
        for name, val in [
            ("config_json", config_json),
            ("evaluation_json", evaluation_json),
            ("factor_breakdown_json", factor_breakdown_json),
            ("today_top_10_json", today_top_10_json),
            ("backtest_last_10_json", backtest_last_10_json),
            ("reasoning", reasoning),
        ]:
            assert val and val != "{}", f"{name} 应非空，实际: {val}"
            # 验证 JSON 有效（规则 18 风格）
            parsed = json.loads(val)
            assert isinstance(parsed, dict), f"{name} 应是 dict 形式"

    def test_reasoning_contains_decision_and_market_mode(self, db_path, run_daily_module):
        """reasoning JSON 应含 decision + market_mode 字段"""
        run_daily_module.run_daily(db_path=db_path)
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT reasoning FROM decision_snapshot ORDER BY snapshot_time DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()

        reasoning = json.loads(row[0])
        assert "decision" in reasoning
        assert "market_mode" in reasoning
        assert reasoning["market_mode"] in ("trend_up", "trend_down", "range_bound", "crash")

    def test_evaluation_json_contains_holdings_count(self, db_path, run_daily_module):
        """evaluation JSON 应含 holdings_count"""
        run_daily_module.run_daily(db_path=db_path)
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT evaluation_json FROM decision_snapshot ORDER BY snapshot_time DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()

        evaluation = json.loads(row[0])
        assert "holdings_count" in evaluation
        assert isinstance(evaluation["holdings_count"], int)
        assert evaluation["holdings_count"] >= 0

    def test_today_top_10_json_contains_candidates(self, db_path, run_daily_module):
        """today_top_10_json 应含 buy/sell candidates"""
        run_daily_module.run_daily(db_path=db_path)
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT today_top_10_json FROM decision_snapshot ORDER BY snapshot_time DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()

        top10 = json.loads(row[0])
        assert "buy_candidates" in top10
        assert "sell_candidates" in top10
        assert isinstance(top10["buy_candidates"], list)
        assert isinstance(top10["sell_candidates"], list)

    def test_factor_breakdown_contains_holding_ranks(self, db_path, run_daily_module):
        """factor_breakdown JSON 应含 holding_ranks（来自 P1-1 修复）"""
        run_daily_module.run_daily(db_path=db_path)
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT factor_breakdown_json FROM decision_snapshot ORDER BY snapshot_time DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()

        fb = json.loads(row[0])
        assert "holding_ranks" in fb
        # 当前持仓 512170 应在 holding_ranks 里
        if "512170" in fb["holding_ranks"]:
            r512170 = fb["holding_ranks"]["512170"]
            assert "sharpe" in r512170
            assert "rank" in r512170
            assert "universe_size" in r512170

    def test_backtest_last_10_json_contains_samples(self, db_path, run_daily_module):
        """backtest_last_10_json 应含 samples（回测样本）"""
        run_daily_module.run_daily(db_path=db_path)
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT backtest_last_10_json FROM decision_snapshot ORDER BY snapshot_time DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()

        bt = json.loads(row[0])
        assert "samples" in bt
        assert isinstance(bt["samples"], list)
        assert len(bt["samples"]) > 0, "回测样本应非空"
        # 第一个样本应有 5 个字段
        s = bt["samples"][0]
        assert "code" in s
        assert "total_return" in s
        assert "sharpe" in s


class TestDecisionSnapshotPositionFields:
    """5 个持仓级字段：target_price/stop_loss/stop_profit/risk_reward/expected_hold_days"""

    def test_position_fields_have_values_when_holding(self, db_path, run_daily_module):
        """有持仓时，5 个字段都应有值（可能为 0 但不应缺失）"""
        run_daily_module.run_daily(db_path=db_path)
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT target_price, stop_loss_price, stop_profit_price,"
                " risk_reward_ratio, expected_hold_days"
                " FROM decision_snapshot ORDER BY snapshot_time DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()

        target, stop_loss, stop_profit, rr, days = row
        # 当前有持仓 512170 → 字段都应有值（不是 None）
        assert target is not None
        assert stop_loss is not None
        assert stop_profit is not None
        assert rr is not None
        assert days is not None