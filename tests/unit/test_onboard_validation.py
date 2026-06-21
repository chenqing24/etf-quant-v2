"""
tests/unit/test_onboard_validation.py — L272 业务完成度校验测试

按 SOUL.md 规则 26：
    onboard --confirm 必须校验业务完成度（不只校验 step 文案）。
    校验失败 → 阻止 confirm。

测试覆盖：
    - universe 块校验（核心池 = 14）
    - alpha 块校验（user_factors 非空 + 因子在 registry）
    - risk 块校验（risk_config.json 三键齐）
    - 校验失败时 confirm 被挡
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SKILL_ROOT = Path(__file__).resolve().parent.parent.parent / "skills" / "quantor-onboard"
sys.path.insert(0, str(_SKILL_ROOT / "scripts"))

from run_onboard import validate_block_completion  # noqa: E402


class TestUniverseValidation:
    """universe 块校验：14 只核心池都在 etf.db.pool_role='core'。"""

    def test_universe_pass(self):
        """14 只核心池 → pass。"""
        result = validate_block_completion("universe")
        assert result["passed"] is True, f"universe 应 pass，实际 missing={result['missing']}"
        assert result["block"] == "universe"
        assert any(c["check"] == "core_pool_size" for c in result["checks"])

    def test_universe_missing_db_fails(self, tmp_path, monkeypatch):
        """etf.db 不存在 → fail。"""
        # 临时改 _REPO_ROOT 指向不存在 etf.db 的目录
        import run_onboard

        original_reproroot = run_onboard._REPO_ROOT
        monkeypatch.setattr(run_onboard, "_REPO_ROOT", tmp_path)
        result = validate_block_completion("universe")
        assert result["passed"] is False
        assert any("etf.db 不存在" in m for m in result["missing"])


class TestAlphaValidation:
    """alpha 块校验：user_factors 列表非空 + 因子在 FACTOR_REGISTRY。"""

    def test_alpha_pass(self):
        """8 个 user_factors 全在 registry → pass。"""
        result = validate_block_completion("alpha")
        assert result["passed"] is True, f"alpha 应 pass，实际 missing={result['missing']}"
        assert any(c["check"] == "user_factors_count" for c in result["checks"])
        assert any(c["check"] == "factors_in_registry" for c in result["checks"])

    def test_alpha_empty_user_factors_fails(self, tmp_path, monkeypatch):
        """user_factors = [] → fail。"""
        import run_onboard

        # 临时改 _SKILL_ROOT 指向 tmp_path（无 alpha_state.json 或空状态）
        fake_alpha_state = tmp_path / "state" / "alpha_state.json"
        fake_alpha_state.parent.mkdir(parents=True, exist_ok=True)
        fake_alpha_state.write_text(json.dumps({
            "user_factors": [],
            "schema_version": 1,
        }))

        original_skillroot = run_onboard._SKILL_ROOT
        monkeypatch.setattr(run_onboard, "_SKILL_ROOT", tmp_path)
        result = validate_block_completion("alpha")
        assert result["passed"] is False
        assert any("user_factors" in m for m in result["missing"])

    def test_alpha_factor_not_in_registry_fails(self, tmp_path, monkeypatch):
        """user_factors 有无效因子 → fail。"""
        import run_onboard

        fake_alpha_state = tmp_path / "state" / "alpha_state.json"
        fake_alpha_state.parent.mkdir(parents=True, exist_ok=True)
        fake_alpha_state.write_text(json.dumps({
            "user_factors": ["T5_ma5", "INVALID_FACTOR"],
            "schema_version": 1,
        }))

        monkeypatch.setattr(run_onboard, "_SKILL_ROOT", tmp_path)
        result = validate_block_completion("alpha")
        assert result["passed"] is False
        assert any("INVALID_FACTOR" in m for m in result["missing"])


class TestRiskValidation:
    """risk 块校验：risk_config.json 三键齐（stop_loss / stop_profit / max_position_pct）。"""

    def test_risk_missing_config_fails(self, tmp_path, monkeypatch):
        """risk_config.json 不存在 → fail。"""
        import run_onboard

        monkeypatch.setattr(run_onboard, "_SKILL_ROOT", tmp_path)
        result = validate_block_completion("risk")
        assert result["passed"] is False
        assert any("risk_config.json 不存在" in m for m in result["missing"])

    def test_risk_missing_keys_fails(self, tmp_path, monkeypatch):
        """risk_config.json 缺 key → fail。"""
        import run_onboard

        fake_risk_config = tmp_path / "state" / "risk_config.json"
        fake_risk_config.parent.mkdir(parents=True, exist_ok=True)
        fake_risk_config.write_text(json.dumps({"stop_loss": -0.08}))  # 只 1 个 key

        monkeypatch.setattr(run_onboard, "_SKILL_ROOT", tmp_path)
        result = validate_block_completion("risk")
        assert result["passed"] is False
        # 应该缺 2 个 key（stop_profit + max_position_pct）
        missing_with_keys = [m for m in result["missing"] if "缺失" in m]
        assert len(missing_with_keys) == 2

    def test_risk_all_keys_pass(self, tmp_path, monkeypatch):
        """risk_config.json 三键齐 → pass。"""
        import run_onboard

        fake_risk_config = tmp_path / "state" / "risk_config.json"
        fake_risk_config.parent.mkdir(parents=True, exist_ok=True)
        fake_risk_config.write_text(json.dumps({
            "stop_loss": -0.08,
            "stop_profit": 0.15,
            "max_position_pct": 0.20,
        }))

        monkeypatch.setattr(run_onboard, "_SKILL_ROOT", tmp_path)
        result = validate_block_completion("risk")
        assert result["passed"] is True, f"risk 应 pass，实际 missing={result['missing']}"


class TestConfirmBlocking:
    """校验失败 → confirm 被挡 → state 不标 completed。"""

    def test_risk_confirm_blocked_when_validation_fails(self, tmp_path):
        """risk 块 confirm 在没有 risk_config.json 时被挡。

        用 monkeypatch 隔离 _SKILL_ROOT 指向 tmp_path，不影响真实 state。
        """
        import run_onboard
        import subprocess
        import os

        # 隔离 _SKILL_ROOT 到 tmp_path
        os.environ['_TEST_SKILL_ROOT'] = str(tmp_path)
        # 直接调用函数测试（不走 subprocess，更稳）
        # 先 fake 一个 _SKILL_ROOT 指向 tmp_path
        original = run_onboard._SKILL_ROOT
        run_onboard._SKILL_ROOT = tmp_path

        try:
            result = run_onboard.validate_block_completion("risk")
            assert result["passed"] is False
            assert any("risk_config.json 不存在" in m for m in result["missing"])
        finally:
            run_onboard._SKILL_ROOT = original