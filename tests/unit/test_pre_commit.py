"""
test_pre_commit.py — pre-commit 钩子 4 条拦截验证

按用户原话"不跑通测试不算完成"。
P0-5：pre-commit 必须实际验证（不只是"写完"）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))


class TestPreCommitHook:
    """pre-commit 4 条拦截测试。"""

    def test_hook_file_exists(self):
        hook = _REPO_ROOT / "scripts" / "git-hooks" / "pre-commit"
        assert hook.exists(), f"pre-commit 钩子不存在: {hook}"
        assert hook.stat().st_mode & 0o111, "pre-commit 必须可执行"

    def test_hook_is_configured(self):
        """git config core.hooksPath 应指向 scripts/git-hooks"""
        result = subprocess.run(
            ["git", "config", "core.hooksPath"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "scripts/git-hooks", \
            f"core.hooksPath 应为 scripts/git-hooks，实际: {result.stdout.strip()}"

    def test_hook_runs_clean_when_no_staged_files(self):
        """无暂存文件时钩子应通过（exit 0）。"""
        result = subprocess.run(
            ["git", "stash", "--keep-index", "--include-untracked"],
            cwd=_REPO_ROOT,
            capture_output=True,
        )
        try:
            result = subprocess.run(
                [sys.executable, "scripts/git-hooks/pre-commit"],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            # 无 staged .py 时，钩子返回 0
            assert result.returncode == 0, \
                f"无 staged 时应通过，实际 returncode={result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        finally:
            subprocess.run(
                ["git", "stash", "pop"],
                cwd=_REPO_ROOT,
                capture_output=True,
            )

    def test_hook_blocks_sqlite3_in_business_code(self, tmp_path):
        """规则 15：业务代码禁止 sqlite3.connect。"""
        # 创建临时业务文件
        business_file = _REPO_ROOT / "src" / "etf_quant" / "alpha" / "_test_business.py"
        business_file.write_text(
            "# 测试文件：违反规则 15\n"
            "import sqlite3\n"
            "conn = sqlite3.connect('test.db')\n"
        )
        try:
            # 模拟 git add
            subprocess.run(
                ["git", "add", str(business_file.relative_to(_REPO_ROOT))],
                cwd=_REPO_ROOT,
                capture_output=True,
            )
            # 跑 pre-commit
            result = subprocess.run(
                [sys.executable, "scripts/git-hooks/pre-commit"],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode != 0, \
                f"应拦截 sqlite3.connect，实际通过\nstdout: {result.stdout}"
            assert "sqlite3" in result.stdout or "规则 15" in result.stdout, \
                f"应提示规则 15 违规，实际: {result.stdout[:500]}"
        finally:
            # 清理
            subprocess.run(
                ["git", "restore", "--staged", str(business_file.relative_to(_REPO_ROOT))],
                cwd=_REPO_ROOT,
                capture_output=True,
            )
            if business_file.exists():
                business_file.unlink()

    def test_hook_allows_data_layer_sqlite3(self, tmp_path):
        """豁免：data_layer 允许 sqlite3.connect。"""
        # 创建 data_layer 业务文件
        dl_file = _REPO_ROOT / "src" / "etf_quant" / "data_layer" / "_test_dl.py"
        dl_file.write_text(
            "# 测试文件：data_layer 豁免\n"
            "import sqlite3\n"
            "conn = sqlite3.connect('test.db')\n"
        )
        try:
            subprocess.run(
                ["git", "add", str(dl_file.relative_to(_REPO_ROOT))],
                cwd=_REPO_ROOT,
                capture_output=True,
            )
            result = subprocess.run(
                [sys.executable, "scripts/git-hooks/pre-commit"],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            # data_layer 豁免，应通过（只有警告级问题）
            output = result.stdout + result.stderr
            # 不应有 "❌ [规则 15]" 错误（警告级 test 缺失可能）
            assert "[规则 15]" not in output or "data_layer" not in output, \
                f"data_layer 应豁免规则 15\nstdout: {result.stdout[:500]}"
        finally:
            subprocess.run(
                ["git", "restore", "--staged", str(dl_file.relative_to(_REPO_ROOT))],
                cwd=_REPO_ROOT,
                capture_output=True,
            )
            if dl_file.exists():
                dl_file.unlink()
