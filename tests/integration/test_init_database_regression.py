"""
test_init_database_regression.py — init database 回归测试

按用户原话"不跑通测试不算完成"+ 包含回归测试。
P0-6：验证 init_database.py 幂等性（重跑不报错）+ 数据一致性。
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))


def run_init_db(db_path: Path) -> int:
    """运行 init_database.py 创建 DB。

    用 ETF_QUANT_DB_PATH 环境变量覆盖（subprocess 继承 env，
    不继承父进程 monkey-patch）。
    """
    env = os.environ.copy()
    env["ETF_QUANT_DB_PATH"] = str(db_path)
    result = subprocess.run(
        [sys.executable, "scripts/init_database.py"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    return result.returncode


class TestInitDatabaseRegression:
    """init_database.py 回归测试。"""

    def test_first_run_creates_all_tables(self, tmp_path):
        """首次运行：建 10 张表（v1 7 + v2 3 + 1 sqlite_sequence）。"""
        db_path = tmp_path / "etf.db"
        returncode = run_init_db(db_path)
        assert returncode == 0, f"首次 init 失败: {returncode}"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        required = {
            "daily", "etf_names", "trade_history", "positions", "audit_log",
            "decision_snapshot", "schema_version", "execution_log",
            "performance_metrics",
        }
        missing = required - set(tables)
        assert not missing, f"缺少表: {missing}"

    def test_second_run_is_idempotent(self, tmp_path):
        """第二次运行：不应报错（幂等性）。"""
        db_path = tmp_path / "etf.db"
        assert run_init_db(db_path) == 0
        returncode = run_init_db(db_path)
        assert returncode == 0, f"第二次 init 应幂等，实际失败: {returncode}"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM schema_version")
        count = cursor.fetchone()[0]
        conn.close()
        assert count >= 1, "schema_version 应保留"

    def test_wal_mode_enabled(self, tmp_path):
        """WAL 模式必须启用（v1 6/1 教训：database locked 修复）。"""
        db_path = tmp_path / "etf.db"
        assert run_init_db(db_path) == 0

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        conn.close()
        assert journal_mode.lower() == "wal", f"WAL 模式应启用，实际: {journal_mode}"

    def test_data_consistency_basic(self, tmp_path):
        """基础数据一致性：写 daily → 读 daily 应一致。"""
        db_path = tmp_path / "etf.db"
        assert run_init_db(db_path) == 0

        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO daily (code, date, open, high, low, close, volume) "
            "VALUES ('510300', '2026-06-19', 4.0, 4.1, 3.9, 4.05, 1000000)"
        )
        conn.commit()

        cursor = conn.execute(
            "SELECT code, date, close, volume FROM daily WHERE code='510300'"
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "数据应能读出"
        assert row[0] == "510300"
        assert row[2] == 4.05
        assert row[3] == 1000000

    def test_schema_version_records_current(self, tmp_path):
        """schema_version 表应记录当前版本。"""
        db_path = tmp_path / "etf.db"
        assert run_init_db(db_path) == 0

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT version, description, applied_at FROM schema_version"
        )
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) >= 1, "schema_version 应至少有 1 条记录"
        versions = [r[0] for r in rows]
        assert "008" in versions, f"应记录 v2 启动版本 008，实际: {versions}"
