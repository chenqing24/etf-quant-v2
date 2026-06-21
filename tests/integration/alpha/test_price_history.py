"""
tests/integration/alpha/test_price_history.py — US-003 验证（修正版：用 daily 表）

按规则 11：先调研再实现 — v2 仓已有 daily 表（69,480 行历史价），无需新建 etf_price_history
按规则 15：数据源统一 — 单一入口 DataSourceRouter
按规则 6.1：错了就错了，不美化 — PRD 误判纠正，US-003 实际是"验证现有 daily 表"

总计：5 测试
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


DB_PATH = Path("/home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/data/etf.db")


@pytest.fixture
def db_conn():
    if not DB_PATH.exists():
        pytest.skip(f"etf.db 不存在: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    yield conn
    conn.close()


def test_daily_table_exists(db_conn):
    """US-003 AC1: daily 表存在（v2 仓数据存储）"""
    cur = db_conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily'")
    assert cur.fetchone() is not None, "daily 表不存在"


def test_daily_table_schema(db_conn):
    """US-003 AC2: daily schema 含 OHLCV+date+code+source（规则 19 默认值）"""
    cur = db_conn.cursor()
    cur.execute("PRAGMA table_info(daily)")
    cols = {r[1] for r in cur.fetchall()}
    required = {"code", "date", "open", "high", "low", "close", "volume", "source"}
    assert required.issubset(cols), f"daily 表缺字段: {required - cols}"


def test_510300_has_2_years_data(db_conn):
    """US-003 AC3: 510300 在 daily 表有 ≥ 480 条（约 2 年交易日）"""
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM daily WHERE code=?", ("510300",))
    count = cur.fetchone()[0]
    assert count >= 480, f"510300 daily rows {count} < 480"


def test_510300_date_range_covers_2_years(db_conn):
    """US-003 AC4: 510300 数据覆盖最近 2 年"""
    cur = db_conn.cursor()
    cur.execute("SELECT MIN(date), MAX(date) FROM daily WHERE code=?", ("510300",))
    row = cur.fetchone()
    earliest, latest = row
    # 2 年 = 504 交易日
    cur.execute(
        "SELECT date FROM daily WHERE code=? ORDER BY date DESC LIMIT 504",
        ("510300",),
    )
    rows = cur.fetchall()
    assert len(rows) == 504, f"近 504 交易日: {len(rows)}"
    # 第一条（最新）应该接近今天
    assert rows[0][0] >= "2026-06-01", f"最新日期 {rows[0][0]} 晚于 2026-06-01"
    # 最后一条（2 年前）应该在 2024 年中
    assert rows[-1][0] <= "2024-06-30", f"最远日期 {rows[-1][0]} 早于 2024-06-30"


def test_daily_source_metadata(db_conn):
    """US-003 AC5: daily.source 字段记录数据来源（规则 13 调研）"""
    cur = db_conn.cursor()
    cur.execute("SELECT DISTINCT source FROM daily")
    sources = {r[0] for r in cur.fetchall()}
    # 至少有一个 source 标记
    assert len(sources) >= 1, f"daily source 字段空: {sources}"
    # 散户可以查"510300 数据从哪来"
    assert "tencent" in sources or "sina" in sources, (
        f"daily source 应是 tencent 或 sina（规则 16.3 排序），实际: {sources}"
    )
