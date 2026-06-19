"""
test_migrate_v1_to_v2.py — 数据迁移脚本测试

按 L228/L244 教训：每个测试独立 fixture，不依赖共享状态。
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MIGRATE_SCRIPT = _REPO_ROOT / "scripts" / "migrate_v1_to_v2.py"
_INIT_SCRIPT = _REPO_ROOT / "scripts" / "init_database.py"
_PYTHON = sys.executable


def _make_v1_db(v1_path: Path) -> None:
    """建临时 v1 DB + 插入测试数据（migrate 脚本循环 4 个表，全部建空表避免失败）。"""
    v1 = sqlite3.connect(str(v1_path))
    # etf_names（14 列 v1 schema）
    v1.execute("""
        CREATE TABLE etf_names (
            code TEXT PRIMARY KEY, name TEXT, name_sina TEXT,
            verified INTEGER, verify_count INTEGER, last_verify_at TEXT,
            created_at TEXT, updated_at TEXT,
            exchange TEXT, category TEXT, tracking_index TEXT, aum REAL,
            tradable INTEGER, pool_role TEXT
        )
    """)
    v1.executemany(
        "INSERT INTO etf_names VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("510300", "沪深300ETF", "hs300", 1, 5, "2026-01-01", "2020-01-01", "2026-01-01",
             "SH", "指数", "沪深300", 1000.0, 1, "core"),
            ("512170", "医疗ETF", "med", 1, 3, "2026-01-01", "2020-01-01", "2026-01-01",
             "SH", "行业", "中证医疗", 50.0, 1, "core"),
        ],
    )
    # stock_info（6 列 v1 schema，空表）
    v1.execute("""
        CREATE TABLE stock_info (
            code TEXT PRIMARY KEY, name TEXT NOT NULL,
            exchange TEXT NOT NULL, full_code TEXT NOT NULL,
            list_date TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # trade_history（37 列 v1 schema，空表）
    v1.execute("""
        CREATE TABLE trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, code TEXT, name TEXT, action TEXT,
            price REAL, quantity INTEGER, amount REAL, reason TEXT,
            emotion TEXT, session TEXT,
            signal_time TEXT, signal_price REAL, signal_rsi REAL, signal_adx REAL, signal_score INTEGER,
            realtime_price REAL, price_deviation REAL, rsi_14 REAL, day_change_pct REAL, score INTEGER,
            expected_return REAL, actual_pnl REAL, note TEXT, trade_time TEXT,
            is_real INTEGER, is_paper INTEGER,
            model TEXT, strategy TEXT, evaluation TEXT, snapshot_ref TEXT,
            created_at TEXT,
            target_price REAL, stop_loss_price REAL, stop_profit_price REAL,
            risk_reward_ratio REAL, max_hold_days INTEGER
        )
    """)
    # daily（11 列 v1 schema，空表）
    v1.execute("""
        CREATE TABLE daily (
            code TEXT, date TEXT, open REAL, high REAL, low REAL,
            close REAL, volume REAL, amount REAL,
            source TEXT, created_at TEXT,
            PRIMARY KEY (code, date)
        )
    """)
    v1.commit()
    v1.close()


def _init_v2_db(v2_path: Path) -> None:
    """初始化 v2 DB（用 subprocess + 环境变量）。"""
    env = {**os.environ, "ETF_QUANT_DB_PATH": str(v2_path), "PATH": "/usr/bin:/bin"}
    subprocess.run(
        [_PYTHON, str(_INIT_SCRIPT)],
        check=True, env=env, cwd=_REPO_ROOT,
    )


class TestMigrateV1ToV2:
    def test_dry_run_no_writes(self, tmp_path):
        """--dry-run 不写入。"""
        v1_path = tmp_path / "v1.db"
        v2_path = tmp_path / "v2.db"
        _make_v1_db(v1_path)
        _init_v2_db(v2_path)

        env = {**os.environ, "ETF_QUANT_DB_PATH": str(v2_path), "PATH": "/usr/bin:/bin"}
        result = subprocess.run(
            [_PYTHON, str(_MIGRATE_SCRIPT), "--dry-run", "--v1", str(v1_path)],
            capture_output=True, text=True, env=env, cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # 验证 v2 仍空
        v2 = sqlite3.connect(str(v2_path))
        count = v2.execute("SELECT COUNT(*) FROM etf_names").fetchone()[0]
        v2.close()
        assert count == 0

    def test_actual_migration(self, tmp_path):
        """实际迁移：2 行 etf_names。"""
        v1_path = tmp_path / "v1.db"
        v2_path = tmp_path / "v2.db"
        _make_v1_db(v1_path)
        _init_v2_db(v2_path)

        env = {**os.environ, "ETF_QUANT_DB_PATH": str(v2_path), "PATH": "/usr/bin:/bin"}
        result = subprocess.run(
            [_PYTHON, str(_MIGRATE_SCRIPT), "--v1", str(v1_path)],
            capture_output=True, text=True, env=env, cwd=_REPO_ROOT, timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        v2 = sqlite3.connect(str(v2_path))
        count = v2.execute("SELECT COUNT(*) FROM etf_names").fetchone()[0]
        v2.close()
        assert count == 2

    def test_idempotent(self, tmp_path):
        """幂等性：第二次跑不会重复插入。"""
        v1_path = tmp_path / "v1.db"
        v2_path = tmp_path / "v2.db"
        _make_v1_db(v1_path)
        _init_v2_db(v2_path)

        env = {**os.environ, "ETF_QUANT_DB_PATH": str(v2_path), "PATH": "/usr/bin:/bin"}
        for _ in range(2):
            r = subprocess.run(
                [_PYTHON, str(_MIGRATE_SCRIPT), "--v1", str(v1_path)],
                capture_output=True, text=True, env=env, cwd=_REPO_ROOT, timeout=30,
            )
            assert r.returncode == 0, f"stderr: {r.stderr}"
        v2 = sqlite3.connect(str(v2_path))
        count = v2.execute("SELECT COUNT(*) FROM etf_names").fetchone()[0]
        v2.close()
        # 仍 2 行（INSERT OR IGNORE）
        assert count == 2

    def test_v1_not_exists(self, tmp_path):
        """v1 不存在时失败。"""
        v2_path = tmp_path / "v2.db"
        _init_v2_db(v2_path)

        env = {**os.environ, "ETF_QUANT_DB_PATH": str(v2_path), "PATH": "/usr/bin:/bin"}
        result = subprocess.run(
            [_PYTHON, str(_MIGRATE_SCRIPT), "--v1", "/nonexistent/v1.db"],
            capture_output=True, text=True, env=env, cwd=_REPO_ROOT, timeout=10,
        )
        assert result.returncode != 0

    def test_v2_not_exists(self, tmp_path):
        """v2 不存在时失败。"""
        v1_path = tmp_path / "v1.db"
        _make_v1_db(v1_path)

        env = {**os.environ, "ETF_QUANT_DB_PATH": str(tmp_path / "nonexistent.db"), "PATH": "/usr/bin:/bin"}
        result = subprocess.run(
            [_PYTHON, str(_MIGRATE_SCRIPT), "--v1", str(v1_path)],
            capture_output=True, text=True, env=env, cwd=_REPO_ROOT, timeout=10,
        )
        assert result.returncode != 0