"""
test_run_eval.py — run_daily.run_eval() 真实回测评估测试（L321 教训 P0-3 修复）

修复前：run_eval() 只返回 validator.config（占位）
修复后：调用 RealBacktestEngine 跑全部 core 池 + ComprehensiveValidator 4 验证器
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
_SRC = _REPO / "src"
_SKILL_SCRIPTS = _REPO / "skills" / "etf-daily" / "scripts"
for p in (str(_SRC), str(_REPO)):
    if p not in sys.path:
        sys.path.insert(0, p)


class TestRunEval:
    """L321 教训 P0-3：run_eval() 必须跑真实回测 + 综合验证。"""

    @pytest.fixture
    def db_path(self):
        from etf_quant.config.constants import resolve_db_path
        return resolve_db_path()

    def test_eval_returns_real_backtest_results(self, db_path):
        """修复 P0-3 核心：必须有 real_backtest_results 字段"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_daily", _SKILL_SCRIPTS / "run_daily.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.run_eval(db_path=db_path)

        # 旧实现只有 validator_config；新实现必须有真实回测结果
        assert "real_backtest_results" in result, \
            "P0-3 修复：run_eval() 必须包含 real_backtest_results"
        assert isinstance(result["real_backtest_results"], list)
        assert len(result["real_backtest_results"]) >= 14, \
            f"应跑全部 core 池（≥14），实际: {len(result['real_backtest_results'])}"

    def test_eval_returns_validation_result(self, db_path):
        """修复 P0-3 核心：必须有 validation_result（综合验证）"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_daily", _SKILL_SCRIPTS / "run_daily.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.run_eval(db_path=db_path)

        assert "validation_result" in result
        vr = result["validation_result"]
        if vr is not None:
            # 4 验证器都应有
            assert "walk_forward_score" in vr
            assert "monte_carlo_score" in vr
            assert "cross_etf_score" in vr
            assert "consistency" in vr
            assert "composite_score" in vr
            assert "pass" in vr

    def test_eval_returns_summary(self, db_path):
        """修复 P0-3：必须有 summary（业务可读汇总）"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_daily", _SKILL_SCRIPTS / "run_daily.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.run_eval(db_path=db_path)

        assert "summary" in result
        s = result["summary"]
        assert "n_etfs_tested" in s
        assert s["n_etfs_tested"] >= 14
        assert "avg_return" in s
        assert "avg_sharpe" in s

    def test_eval_keeps_validator_config_backward_compat(self, db_path):
        """旧实现只返回 validator_config，新实现保留此字段（向后兼容）"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "run_daily", _SKILL_SCRIPTS / "run_daily.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.run_eval(db_path=db_path)
        assert "validator_config" in result
        assert "walk_forward" in result["validator_config"]
        assert "weights" in result["validator_config"]
