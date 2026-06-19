"""
test_strategy_c21.py — C21-1 策略单元测试（含回归测试）

按用户原话"完整测试"——含单元 + 回归。
按 L238 教训（先读真实 API）——测试对齐 v1 真实配置。
按 L225 教训（alpha 颠覆性发现）——验证金三角。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestC21EntryConditions:
    """入场条件测试（L226 + v1 C21 实验）。"""

    def test_boll_strict_middle_in_band(self):
        from etf_quant.alpha.strategy_c21 import C21EntryConditions
        cond = C21EntryConditions(boll_threshold=0.005)
        # close 在 BOLL_middle ±0.5% 内 → True
        assert cond.check_boll_strict_middle(close=4.0, boll_middle=4.0) is True
        assert cond.check_boll_strict_middle(close=4.01, boll_middle=4.0) is True  # +0.25%
        assert cond.check_boll_strict_middle(close=3.99, boll_middle=4.0) is True  # -0.25%

    def test_boll_strict_middle_out_of_band(self):
        from etf_quant.alpha.strategy_c21 import C21EntryConditions
        cond = C21EntryConditions(boll_threshold=0.005)
        # close 在 BOLL_middle ±0.5% 外 → False
        assert cond.check_boll_strict_middle(close=4.05, boll_middle=4.0) is False  # +1.25%
        assert cond.check_boll_strict_middle(close=3.95, boll_middle=4.0) is False  # -1.25%

    def test_boll_must_be_positive(self):
        """防御：boll_middle <= 0 → False（防止除零）。"""
        from etf_quant.alpha.strategy_c21 import C21EntryConditions
        cond = C21EntryConditions(boll_threshold=0.005)
        assert cond.check_boll_strict_middle(close=4.0, boll_middle=0) is False
        assert cond.check_boll_strict_middle(close=4.0, boll_middle=-1) is False

    def test_ma60_trend_up(self):
        from etf_quant.alpha.strategy_c21 import C21EntryConditions
        cond = C21EntryConditions(ma_period=60)
        assert cond.check_ma60_trend_up(close=4.5, ma60=4.0) is True
        assert cond.check_ma60_trend_up(close=3.5, ma60=4.0) is False  # 在 MA60 之下
        assert cond.check_ma60_trend_up(close=4.0, ma60=4.0) is False  # 严格 >

    def test_all_conditions_strict_and(self):
        """v1 严格 AND：两个条件都必须满足。"""
        from etf_quant.alpha.strategy_c21 import C21EntryConditions
        cond = C21EntryConditions(boll_threshold=0.005, ma_period=60)
        # 都在条件内
        assert cond.all_conditions_met(close=4.0, boll_middle=4.0, ma60=3.9) is True
        # BOLL 不在条件内
        assert cond.all_conditions_met(close=4.05, boll_middle=4.0, ma60=3.9) is False
        # MA60 不在条件上
        assert cond.all_conditions_met(close=4.0, boll_middle=4.0, ma60=4.1) is False


class TestC21ExitConditions:
    """退出条件测试（L225 + C20 验证：永远不卖）。"""

    def test_disabled_never_sells(self):
        from etf_quant.alpha.strategy_c21 import C21ExitConditions
        exit_cond = C21ExitConditions(enabled=False, max_hold_days=99999)
        # 即使持仓 100 年，也不卖
        assert exit_cond.max_hold_days == 99999
        # should_sell 在 disabled 时永远 false（业务逻辑在 C21Strategy.should_sell）

    def test_max_hold_days_99999(self):
        """v1 C11 修复：max_hold_days=99999（永远满仓）。"""
        from etf_quant.alpha.strategy_c21 import C21ExitConditions
        exit_cond = C21ExitConditions(enabled=False, max_hold_days=99999)
        assert exit_cond.max_hold_days == 99999


class TestC21Strategy:
    """C21-1 策略整体测试。"""

    def test_from_config_loads_real_v1_config(self):
        """从 v1 真实配置加载（L238 教训：先读真实 API）。"""
        from etf_quant.alpha.strategy_c21 import C21Strategy
        strategy = C21Strategy.from_config()
        assert strategy.entry.boll_threshold == 0.005
        assert strategy.entry.ma_period == 60
        assert strategy.exit.enabled is False  # 永远不卖
        assert strategy.exit.max_hold_days == 99999

    def test_should_buy_all_conditions(self):
        from etf_quant.alpha.strategy_c21 import C21Strategy
        strategy = C21Strategy.from_config()
        # BOLL 在条件 + MA60 上 → True
        assert strategy.should_buy(close=4.0, boll_middle=4.0, ma60=3.9) is True
        # BOLL 出条件 → False
        assert strategy.should_buy(close=4.05, boll_middle=4.0, ma60=3.9) is False
        # MA60 下 → False
        assert strategy.should_buy(close=4.0, boll_middle=4.0, ma60=4.1) is False

    def test_should_sell_always_false(self):
        """L225 教训：卖出是 alpha 拖累，C21-1 永远不卖。"""
        from etf_quant.alpha.strategy_c21 import C21Strategy
        strategy = C21Strategy.from_config()
        # 任何 hold_days → False
        for days in [0, 30, 100, 999, 9999, 99999]:
            assert strategy.should_sell(hold_days=days) is False, \
                f"hold_days={days} 不应卖"

    def test_human_nature_warning_present(self):
        """L227 教训：人性警告是策略前置条件。"""
        from etf_quant.alpha.strategy_c21 import C21Strategy
        strategy = C21Strategy.from_config()
        warning = strategy.get_human_nature_warning()
        assert warning["level"] == "high"
        assert "challenges" in warning
        assert "coping_strategies" in warning
        assert len(warning["challenges"]) >= 3
        assert len(warning["coping_strategies"]) >= 3

    def test_regression_no_sell_signal_in_5_years(self):
        """回归测试：5 年内不应有任何卖出信号。"""
        from etf_quant.alpha.strategy_c21 import C21Strategy
        strategy = C21Strategy.from_config()
        # 5 年 = 1825 天
        for day in range(0, 1825, 30):  # 每月检查
            assert strategy.should_sell(hold_days=day) is False, \
                f"day={day} 不应卖（C21-1 关键：永远不卖）"


class TestC21ConfigIntegrity:
    """C21 配置文件完整性测试（v1 真实配置）。"""

    def test_config_file_exists(self):
        config = _SRC.parent / "configs" / "c21_strategy.json"
        assert config.exists(), f"C21 配置文件不存在: {config}"

    def test_config_has_required_fields(self):
        config_path = _SRC.parent / "configs" / "c21_strategy.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        required = [
            "strategy_id", "strategy_name", "version",
            "entry_conditions", "exit_conditions", "max_hold_days",
            "human_nature_warning", "limitations",
        ]
        for field in required:
            assert field in config, f"配置缺少 {field}"

    def test_strategy_id_is_c21_1(self):
        config_path = _SRC.parent / "configs" / "c21_strategy.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert config["strategy_id"] == "C21-1"

    def test_exit_disabled_in_config(self):
        """C21-1 关键：exit_conditions.enabled = false（永远不卖）。"""
        config_path = _SRC.parent / "configs" / "c21_strategy.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert config["exit_conditions"]["enabled"] is False
