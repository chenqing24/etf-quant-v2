"""
tests/unit/test_onboard_validation.py — L272 业务完成度校验测试（L296 教训：测试不依赖生产 state）

按 SOUL.md 规则 26：
    onboard --confirm 必须校验业务完成度（不只校验 step 文案）。
    校验失败 → 阻止 confirm。

按 L296 教训：
    测试不依赖真实 state.json / etf.db（生产脏数据导致新会话必失败）。
    用 tmp_path + fake_db fixture 隔离。

测试覆盖：
    - universe 块校验（核心池 = 14，mock db）
    - alpha 块校验（user_factors 非空 + 因子在 registry，mock state）
    - risk 块校验（risk_config.json 三键齐，mock state）
    - 校验失败时 confirm 被挡
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

_SKILL_ROOT = Path(__file__).resolve().parent.parent.parent / "skills" / "quantor-onboard"
sys.path.insert(0, str(_SKILL_ROOT / "scripts"))

from run_onboard import validate_block_completion  # noqa: E402


# ============== Fixtures（L296 教训：测试隔离） ==============

@pytest.fixture
def fake_etf_db(tmp_path, monkeypatch):
    """创建临时 etf.db + 14 条 core 记录，monkeypatch 替换 _REPO_ROOT 指向 tmp_path。"""
    import run_onboard

    fake_repo_root = tmp_path / "etf_quant_v2"
    fake_data_dir = fake_repo_root / "data"
    fake_data_dir.mkdir(parents=True)
    db_path = fake_data_dir / "etf.db"

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE etf_names (
            code TEXT PRIMARY KEY,
            pool_role TEXT NOT NULL
        )
    """)
    cur.executemany(
        "INSERT INTO etf_names (code, pool_role) VALUES (?, ?)",
        [(f"51{(i+1):04d}", "core") for i in range(14)],
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(run_onboard, "_REPO_ROOT", fake_repo_root)
    return fake_repo_root


@pytest.fixture
def fake_state_dir(tmp_path):
    """创建临时 state 目录（不预填任何文件）。"""
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True)
    return state_dir


@pytest.fixture
def fake_alpha_state_pass(fake_state_dir):
    """预填有效 alpha_state.json（user_factors 全在 FACTOR_REGISTRY）。"""
    valid_factors = ["T1_macd_bar", "T5_ma5", "M4_rsi", "V2_obv"]
    state_file = fake_state_dir / "alpha_state.json"
    state_file.write_text(json.dumps({"user_factors": valid_factors, "schema_version": 1}))
    return fake_state_dir


@pytest.fixture
def fake_alpha_state_empty(fake_state_dir):
    """预填空 user_factors。"""
    state_file = fake_state_dir / "alpha_state.json"
    state_file.write_text(json.dumps({"user_factors": [], "schema_version": 1}))
    return fake_state_dir


@pytest.fixture
def fake_alpha_state_dirty(fake_state_dir):
    """预填含脏数据 user_factor（不在 FACTOR_REGISTRY）—— 模拟生产问题。"""
    state_file = fake_state_dir / "alpha_state.json"
    state_file.write_text(json.dumps({
        "user_factors": ["T5_ma5", "user_factor"],  # user_factor 不在 registry
        "schema_version": 1,
    }))
    return fake_state_dir


@pytest.fixture
def fake_risk_config_pass(fake_state_dir):
    """预填有效 risk_config.json。"""
    state_file = fake_state_dir / "risk_config.json"
    state_file.write_text(json.dumps({
        "stop_loss": -0.08,
        "stop_profit": 0.15,
        "max_position_pct": 0.20,
    }))
    return fake_state_dir


@pytest.fixture
def fake_risk_config_missing(fake_state_dir):
    """预填残缺 risk_config.json（缺 max_position_pct）。"""
    state_file = fake_state_dir / "risk_config.json"
    state_file.write_text(json.dumps({
        "stop_loss": -0.08,
        "stop_profit": 0.15,
    }))
    return fake_state_dir


# ============== universe 块测试 ==============

class TestUniverseValidation:
    """universe 块校验：14 只核心池都在 etf.db.pool_role='core'。"""

    def test_universe_pass(self, fake_etf_db, fake_state_dir):
        """14 只核心池 + tmp db → pass。"""
        result = validate_block_completion("universe", state_dir=fake_state_dir)
        assert result["passed"] is True, f"universe 应 pass，实际 missing={result['missing']}"
        assert result["block"] == "universe"
        assert any(c["check"] == "core_pool_size" and c["actual"] == 14 for c in result["checks"])

    def test_universe_wrong_count_fails(self, tmp_path, monkeypatch, fake_state_dir):
        """核心池 = 10 → fail。"""
        import run_onboard

        fake_repo_root = tmp_path / "etf_quant_v2"
        fake_data_dir = fake_repo_root / "data"
        fake_data_dir.mkdir(parents=True)
        db_path = fake_data_dir / "etf.db"

        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE etf_names (code TEXT, pool_role TEXT)")
        conn.executemany(
            "INSERT INTO etf_names VALUES (?, ?)",
            [(f"51{(i+1):04d}", "core") for i in range(10)],
        )
        conn.commit()
        conn.close()

        monkeypatch.setattr(run_onboard, "_REPO_ROOT", fake_repo_root)
        result = validate_block_completion("universe", state_dir=fake_state_dir)
        assert result["passed"] is False
        assert any("核心池 10 只 ≠ 14 只" in m for m in result["missing"])

    def test_universe_missing_db_fails(self, tmp_path, monkeypatch, fake_state_dir):
        """etf.db 不存在 → fail。"""
        import run_onboard

        monkeypatch.setattr(run_onboard, "_REPO_ROOT", tmp_path / "no_such_repo")
        result = validate_block_completion("universe", state_dir=fake_state_dir)
        assert result["passed"] is False
        assert any("etf.db 不存在" in m for m in result["missing"])


# ============== alpha 块测试（L296 教训：必须 mock state） ==============

class TestAlphaValidation:
    """alpha 块校验：user_factors 列表非空 + 因子在 FACTOR_REGISTRY。"""

    def test_alpha_pass(self, fake_alpha_state_pass, fake_state_dir):
        """user_factors 全在 registry → pass。"""
        result = validate_block_completion("alpha", state_dir=fake_state_dir)
        assert result["passed"] is True, f"alpha 应 pass，实际 missing={result['missing']}"
        assert any(c["check"] == "user_factors_count" for c in result["checks"])
        assert any(c["check"] == "factors_in_registry" for c in result["checks"])

    def test_alpha_empty_user_factors_fails(self, fake_alpha_state_empty, fake_state_dir):
        """user_factors = [] → fail。"""
        result = validate_block_completion("alpha", state_dir=fake_state_dir)
        assert result["passed"] is False
        assert any("user_factors" in m for m in result["missing"])

    def test_alpha_dirty_user_factors_fails(self, fake_alpha_state_dirty, fake_state_dir):
        """user_factors 含 'user_factor'（不在 registry）→ fail（L296 教训场景）。"""
        result = validate_block_completion("alpha", state_dir=fake_state_dir)
        assert result["passed"] is False
        assert any("不在 FACTOR_REGISTRY" in m for m in result["missing"])

    def test_alpha_missing_state_fails(self, fake_state_dir):
        """alpha_state.json 不存在 → fail。"""
        result = validate_block_completion("alpha", state_dir=fake_state_dir)
        assert result["passed"] is False
        assert any("alpha_state.json 不存在" in m for m in result["missing"])


# ============== risk 块测试 ==============

class TestRiskValidation:
    """risk 块校验：risk_config.json 三键齐。"""

    def test_risk_pass(self, fake_risk_config_pass, fake_state_dir):
        """risk_config 三键齐 → pass。"""
        result = validate_block_completion("risk", state_dir=fake_state_dir)
        assert result["passed"] is True, f"risk 应 pass，实际 missing={result['missing']}"
        for key in ["stop_loss", "stop_profit", "max_position_pct"]:
            assert any(c["check"] == f"risk_config.{key}" for c in result["checks"])

    def test_risk_missing_key_fails(self, fake_risk_config_missing, fake_state_dir):
        """缺 max_position_pct → fail。"""
        result = validate_block_completion("risk", state_dir=fake_state_dir)
        assert result["passed"] is False
        assert any("max_position_pct" in m for m in result["missing"])

    def test_risk_missing_file_fails(self, fake_state_dir):
        """risk_config.json 不存在 → fail。"""
        result = validate_block_completion("risk", state_dir=fake_state_dir)
        assert result["passed"] is False
        assert any("risk_config.json 不存在" in m for m in result["missing"])


# ============== 集成场景 ==============

class TestBlockCompletionIntegration:
    """3 块同时校验（onboard --confirm 场景）。"""

    def test_all_three_blocks_pass(self, fake_etf_db, fake_alpha_state_pass, fake_risk_config_pass, fake_state_dir):
        """3 块都通过 → pass。"""
        for block in ["universe", "alpha", "risk"]:
            result = validate_block_completion(block, state_dir=fake_state_dir)
            assert result["passed"] is True, f"{block} 应 pass，实际 missing={result['missing']}"

    def test_alpha_block_prevents_confirm(self, fake_etf_db, fake_alpha_state_dirty, fake_risk_config_pass, fake_state_dir):
        """alpha 块脏数据 → 阻止 confirm（L272 规则 26 场景）。"""
        result = validate_block_completion("alpha", state_dir=fake_state_dir)
        assert result["passed"] is False
        # 模拟 --confirm 校验：失败则抛错
        with pytest.raises(AssertionError, match="alpha"):
            assert result["passed"], f"alpha 校验失败应阻止 confirm: {result['missing']}"
