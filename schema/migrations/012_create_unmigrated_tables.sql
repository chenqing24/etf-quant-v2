-- 012_create_unmigrated_tables.sql
-- 用途: 新增 4 个 v1 业务库存在但 v2 未迁移的表
-- 日期: 2026-06-19
-- 原因: V1_VS_V2_SCHEMA_AUDIT.md 调研发现 4 个表完全未迁移
-- 依赖: 无

-- ============================================
-- stock_info: 股票信息（v1 有 66 行，v2 ETF 不需要但保留兼容）
-- ============================================
CREATE TABLE IF NOT EXISTS stock_info (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    list_date TEXT,
    total_shares REAL,
    float_shares REAL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ============================================
-- etf_name_metrics: ETF 名称采集指标
-- ============================================
CREATE TABLE IF NOT EXISTS etf_name_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    source TEXT NOT NULL,
    code TEXT,
    success INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_etf_name_metrics_time ON etf_name_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_etf_name_metrics_source ON etf_name_metrics(source);

-- ============================================
-- etf_name_retry_queue: ETF 名称重试队列
-- ============================================
CREATE TABLE IF NOT EXISTS etf_name_retry_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    source TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retry INTEGER NOT NULL DEFAULT 3,
    next_retry_at TEXT NOT NULL,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_retry_queue_next_retry ON etf_name_retry_queue(next_retry_at);

-- ============================================
-- realtime_cache: 实时价格缓存
-- ============================================
CREATE TABLE IF NOT EXISTS realtime_cache (
    code TEXT PRIMARY KEY,
    price REAL NOT NULL,
    change_pct REAL,
    volume INTEGER,
    source TEXT NOT NULL,
    cached_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    expires_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_realtime_cached_at ON realtime_cache(cached_at);
