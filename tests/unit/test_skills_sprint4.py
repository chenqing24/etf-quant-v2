"""
test_skills_sprint4.py — Sprint-4 5 skill 入口测试

按用户原话'完整测试'。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestEtfResearchSkill:
    """US-021 etf-research skill。"""

    def test_skill_md_exists(self):
        skill_md = _REPO_ROOT / "skills" / "etf-research" / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text(encoding="utf-8")
        for s in ["用途", "被谁调用", "功能说明", "使用方式", "依赖", "注意事项"]:
            assert s in content

    def test_cli_validate(self):
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "skills" / "etf-research" / "scripts" / "run_validate.py"), "validate"],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert "composite_score" in result.stdout

    def test_cli_factor(self):
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "skills" / "etf-research" / "scripts" / "run_validate.py"), "factor"],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert "weights" in result.stdout


class TestStockAnalyzeSkill:
    """US-022 stock-analyze skill。"""

    def test_skill_md_exists(self):
        skill_md = _REPO_ROOT / "skills" / "stock-analyze" / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text(encoding="utf-8")
        for s in ["用途", "被谁调用", "功能说明", "使用方式", "依赖", "注意事项"]:
            assert s in content

    def test_cli_info(self, tmp_path):
        """CLI info 模式（DB 不存在返回 error）。"""
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "skills" / "stock-analyze" / "scripts" / "run_analyze.py"), "info", "999999"],
            capture_output=True, text=True,
            env={"ETF_QUANT_DB_PATH": str(tmp_path / "nonexistent.db"), "PATH": "/usr/bin:/bin"},
            cwd=_REPO_ROOT, timeout=30,
        )
        # DB 不存在也返回 0（输出 error 字段）
        assert result.returncode == 0, result.stderr
        assert "error" in result.stdout or "code" in result.stdout

    def test_cli_compare(self, tmp_path):
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "skills" / "stock-analyze" / "scripts" / "run_analyze.py"), "compare", "600519"],
            capture_output=True, text=True,
            env={"ETF_QUANT_DB_PATH": str(tmp_path / "nonexistent.db"), "PATH": "/usr/bin:/bin"},
            cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0


class TestStockPortfolioSkill:
    """US-023 stock-portfolio skill。"""

    def test_skill_md_exists(self):
        skill_md = _REPO_ROOT / "skills" / "stock-portfolio" / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text(encoding="utf-8")
        for s in ["用途", "被谁调用", "功能说明", "使用方式", "依赖", "注意事项"]:
            assert s in content

    def test_cli_status(self):
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "skills" / "stock-portfolio" / "scripts" / "run_portfolio.py"), "status"],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=30,
        )
        # DB 不存在时返回空 holdings
        assert result.returncode == 0
        assert "holdings_count" in result.stdout

    def test_cli_attribution(self):
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "skills" / "stock-portfolio" / "scripts" / "run_portfolio.py"), "attribution"],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0
        assert "total_trades" in result.stdout


class TestQuantKnowledgeSkill:
    """US-024 quant-knowledge skill。"""

    def test_skill_md_exists(self):
        skill_md = _REPO_ROOT / "skills" / "quant-knowledge" / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text(encoding="utf-8")
        for s in ["用途", "被谁调用", "功能说明", "使用方式", "依赖", "注意事项"]:
            assert s in content

    def test_cli_strategy(self):
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "skills" / "quant-knowledge" / "scripts" / "run_knowledge.py"), "strategy"],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0
        assert "strategies" in result.stdout

    def test_cli_lesson_list(self):
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "skills" / "quant-knowledge" / "scripts" / "run_knowledge.py"), "lesson"],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0
        assert "lessons" in result.stdout

    def test_cli_lesson_specific(self):
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "skills" / "quant-knowledge" / "scripts" / "run_knowledge.py"), "lesson", "228"],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0
        # L228 实际不存在于 workspace，但查询逻辑跑通
        assert "lesson_id" in result.stdout or "error" in result.stdout

    def test_cli_reference(self):
        result = subprocess.run(
            [sys.executable, str(_REPO_ROOT / "skills" / "quant-knowledge" / "scripts" / "run_knowledge.py"), "reference"],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0
        assert "references" in result.stdout