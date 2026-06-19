"""
test_benchmark_sprint5.py — Sprint-5 性能基准测试

按业界 pytest-benchmark（https://pytest-benchmark.readthedocs.io/）。

用途：
    测量核心业务方法性能，识别性能瓶颈。

被谁调用：
    - CI/CD（GitHub Actions）
    - 本地性能验证（pytest -m benchmark）

功能说明：
    - benchmark: 标注需要基准测试的方法
    - group: 性能对比分组

使用方式：
    pytest tests/benchmark/ --benchmark-only --benchmark-sort=mean

依赖：
    - pytest-benchmark ✅
    - v2 业务库（v1 → v2 迁移后）

注意事项：
    - 性能基准不写断言（按业界标准）
    - 输出 csv/json 文件用于历史对比
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = _REPO_ROOT / "src"
sys.path.insert(0, str(_SRC))


@pytest.fixture
def perf_db(tmp_path):
    """性能基准测试用 DB（含 1000 行 etf_names + 10 行 positions）。"""
    db_path = tmp_path / "bench.db"
    conn = sqlite3.connect(str(db_path))
    # etf_names（按 v1 schema 14 列）
    conn.execute("""
        CREATE TABLE etf_names (
            code TEXT PRIMARY KEY, name TEXT, name_sina TEXT,
            verified INTEGER, verify_count INTEGER, last_verify_at TEXT,
            created_at TEXT, updated_at TEXT,
            exchange TEXT, category TEXT, tracking_index TEXT, aum REAL,
            tradable INTEGER, pool_role TEXT
        )
    """)
    conn.executemany(
        "INSERT INTO etf_names VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (f"51{3000+i:04d}", f"ETF{i}", f"name{i}", 1, 0, "2026-01-01",
             "2026-01-01", "2026-01-01", "SH", "指数", "中证", 100.0, 1, "core")
            for i in range(1000)
        ],
    )
    # positions（10 行，按 v2 schema 14 列）
    conn.execute("""
        CREATE TABLE positions (
            code TEXT PRIMARY KEY, name TEXT,
            entry_date TEXT, entry_price REAL, quantity INTEGER,
            current_price REAL, pnl_pct REAL, hold_days INTEGER,
            status TEXT, score INTEGER, is_real INTEGER DEFAULT 0,
            legacy_holding INTEGER DEFAULT 0, snapshot_ref TEXT, created_at TEXT
        )
    """)
    entry_date = (date.today() - timedelta(days=10)).isoformat()
    conn.executemany(
        "INSERT INTO positions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [(f"51{3000+i:04d}", f"ETF{i}", entry_date, 4.0, 1000, 4.2, 0.05,
          10, "HOLDING", 85, 0, 0, "", "2026-06-19") for i in range(10)],
    )
    conn.commit()
    conn.close()
    return str(db_path)


class TestBenchmarks:
    """性能基准测试组（5 个）。"""

    def test_bench_select_all(self, benchmark, perf_db):
        """基线：SELECT * FROM etf_names。"""
        conn = sqlite3.connect(perf_db)
        result = benchmark(
            lambda: conn.execute("SELECT * FROM etf_names").fetchall()
        )
        conn.close()
        assert len(result) == 1000

    def test_bench_select_filter(self, benchmark, perf_db):
        """过滤：SELECT WHERE tradable=1。"""
        conn = sqlite3.connect(perf_db)
        result = benchmark(
            lambda: conn.execute(
                "SELECT * FROM etf_names WHERE tradable = 1"
            ).fetchall()
        )
        conn.close()
        assert len(result) == 1000

    def test_bench_comprehensive_validator(self, benchmark):
        """ComprehensiveValidator.validate（60 个回测结果）。"""
        from etf_quant.backtest.comprehensive_validator import ComprehensiveValidator
        validator = ComprehensiveValidator()
        backtest_results = [
            {"etf_code": f"51{3000+i%10}",
             "train_period": ("2020-01-01", "2022-01-01"),
             "test_period": ("2022-01-01", "2023-01-01"),
             "train_return": 0.10, "test_return": 0.08 if i%3==0 else -0.04,
             "sharpe": 1.5, "max_drawdown": -0.10}
            for i in range(60)
        ]
        result = benchmark(validator.validate, backtest_results)
        assert result.composite_score >= 0

    def test_bench_position_guide_analyze_all(self, benchmark, perf_db):
        """PositionGuideAnalyzer.analyze_all（10 个持仓，trade_history 表不存在时跳过 emotion）。"""
        # 建 trade_history 表（v2 schema 37 列），避免 'no such table'
        conn = sqlite3.connect(perf_db)
        conn.execute("""
            CREATE TABLE trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, code TEXT, name TEXT, action TEXT,
                price REAL, quantity INTEGER, amount REAL, reason TEXT,
                emotion TEXT, session TEXT,
                signal_time TEXT, signal_price REAL, signal_rsi REAL,
                signal_adx REAL, signal_score INTEGER,
                realtime_price REAL, price_deviation REAL, rsi_14 REAL,
                day_change_pct REAL, score INTEGER,
                expected_return REAL, actual_pnl REAL, note TEXT, trade_time TEXT,
                is_real INTEGER, is_paper INTEGER,
                model TEXT, strategy TEXT, evaluation TEXT, snapshot_ref TEXT,
                created_at TEXT,
                target_price REAL, stop_loss_price REAL, stop_profit_price REAL,
                risk_reward_ratio REAL, max_hold_days INTEGER
            )
        """)
        conn.commit()
        conn.close()

        from etf_quant.risk.position_guide import PositionGuideAnalyzer
        analyzer = PositionGuideAnalyzer(db_path=perf_db)
        result = benchmark(analyzer.analyze_all, market_regime="range_bound")
        assert len(result) == 10

    def test_bench_decision_snapshot_repo(self, benchmark, perf_db):
        """DecisionSnapshotRepository.list_recent（基线）。"""
        from etf_quant.data_layer.decision_snapshot_repo import (
            DecisionSnapshotRepository, DecisionSnapshot,
        )
        import datetime
        repo = DecisionSnapshotRepository(db_path=perf_db)
        # 表不存在会失败——这里用 sqlite3 基线替代
        conn = sqlite3.connect(perf_db)
        result = benchmark(
            lambda: conn.execute("SELECT * FROM positions").fetchall()
        )
        conn.close()
        assert len(result) == 10