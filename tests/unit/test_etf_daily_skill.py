"""
test_etf_daily_skill.py — etf-daily skill 单元测试

按用户原话'完整测试'。
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

_SKILL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "skills" / "etf-daily" / "scripts" / "run_daily.py"
)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = _REPO_ROOT / "src"
sys.path.insert(0, str(_SRC))


@pytest.fixture
def temp_db_with_schema(tmp_path):
    """临时 DB + 建表。"""
    db_path = tmp_path / "etf.db"
    schema_dir = _REPO_ROOT / "schema" / "migrations"
    sql_files = sorted(schema_dir.glob("00[0-9]_*.sql"))
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    for sql_path in sql_files:
        sql = sql_path.read_text(encoding="utf-8")
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError:
                    pass
    conn.commit()
    conn.close()
    return str(db_path)


class TestEtfDailySkill:
    """etf-daily skill 入口测试。"""

    def test_skill_md_exists(self):
        """SKILL.md 必须存在（6 段标准注释）。"""
        skill_md = (
            Path(__file__).resolve().parent.parent.parent
            / "skills" / "etf-daily" / "SKILL.md"
        )
        assert skill_md.exists(), f"SKILL.md 不存在: {skill_md}"
        content = skill_md.read_text(encoding="utf-8")
        # 必须有 6 段标准注释
        for section in ["用途", "被谁调用", "功能说明", "使用方式", "依赖", "注意事项"]:
            assert section in content, f"SKILL.md 缺少 '{section}' 段"

    def test_run_daily_imports(self):
        """run_daily.py 可 import。"""
        sys.path.insert(0, str(_SKILL_PATH.parent))
        try:
            import run_daily
            assert hasattr(run_daily, "main")
            assert hasattr(run_daily, "run_daily")
            assert hasattr(run_daily, "run_eval")
            assert hasattr(run_daily, "run_history")
        finally:
            sys.path.pop(0)

    def test_run_daily_empty_db(self, temp_db_with_schema):
        """空 DB 上 run_daily 成功。"""
        sys.path.insert(0, str(_SKILL_PATH.parent))
        try:
            import run_daily
            import os
            os.environ["ETF_QUANT_DB_PATH"] = temp_db_with_schema
            result = run_daily.run_daily(db_path=temp_db_with_schema)
            assert "model_name" in result
            assert "strategy_name" in result
            assert "holdings_count" in result
            assert "snapshot_id" in result
            assert result["model_name"] == "v2_sop"
        finally:
            sys.path.pop(0)

    def test_run_history_empty_db(self, temp_db_with_schema):
        """空 DB 上 run_history 成功。"""
        sys.path.insert(0, str(_SKILL_PATH.parent))
        try:
            import run_daily
            result = run_daily.run_history(db_path=temp_db_with_schema)
            assert result["trades_count"] == 0
            assert result["positions_count"] == 0
        finally:
            sys.path.pop(0)

    def test_run_eval_returns_config(self, temp_db_with_schema):
        """run_eval 返回 ComprehensiveValidator 配置。"""
        sys.path.insert(0, str(_SKILL_PATH.parent))
        try:
            import run_daily
            result = run_daily.run_eval(db_path=temp_db_with_schema)
            assert "validator_config" in result
            # 验证默认配置
            weights = result["validator_config"]["weights"]
            assert weights["walk_forward"] == 0.40
            assert weights["monte_carlo"] == 0.15
        finally:
            sys.path.pop(0)

    def test_cli_daily_mode(self, temp_db_with_schema):
        """CLI daily 模式。"""
        result = subprocess.run(
            [sys.executable, str(_SKILL_PATH), "daily"],
            capture_output=True, text=True,
            env={"ETF_QUANT_DB_PATH": temp_db_with_schema, "PATH": "/usr/bin:/bin"},
            cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0, f"daily 模式失败: {result.stderr}"
        assert "model_name" in result.stdout

    def test_cli_history_mode(self, temp_db_with_schema):
        """CLI history 模式。"""
        result = subprocess.run(
            [sys.executable, str(_SKILL_PATH), "history"],
            capture_output=True, text=True,
            env={"ETF_QUANT_DB_PATH": temp_db_with_schema, "PATH": "/usr/bin:/bin"},
            cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0, f"history 模式失败: {result.stderr}"
        assert "trades_count" in result.stdout

    def test_cli_eval_mode(self, temp_db_with_schema):
        """CLI eval 模式。"""
        result = subprocess.run(
            [sys.executable, str(_SKILL_PATH), "eval"],
            capture_output=True, text=True,
            env={"ETF_QUANT_DB_PATH": temp_db_with_schema, "PATH": "/usr/bin:/bin"},
            cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0, f"eval 模式失败: {result.stderr}"
        assert "validator_config" in result.stdout
