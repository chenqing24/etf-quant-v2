-- 008_add_schema_version.sql
-- 用途: v2 启动时建立 schema 版本管理
-- 日期: 2026-06-19
-- 原因: v1 没有 schema_version 表，无法追踪当前迁移版本
--       业界参考: Flyway / Liquibase / Alembic（schema 迁移工具标准实践）
-- 依赖: 无（独立表）
-- 触发事件: v2 重构启动（mission-20260618-234155）

-- ============================================
-- schema_version: 当前 schema 版本
-- ============================================
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,         -- 版本号（如 '008'）
    description TEXT NOT NULL,        -- 版本描述
    applied_at TEXT NOT NULL,         -- 应用时间
    applied_by TEXT,                  -- 应用者（user / migration script）
    checksum TEXT                      -- SQL 校验和（防重复）
);

-- 当前版本记录
INSERT OR IGNORE INTO schema_version (version, description, applied_at, applied_by)
VALUES (
    '008',
    'v2 启动: 继承 v1 7 个迁移 + 新增 schema_version 表',
    datetime('now', 'localtime'),
    'mission-20260618-234155'
);

-- ============================================
-- execution_log: 执行审计（v2 新增）
-- ============================================
-- 来源：L101 教训（多执行源无标识 = 串扰）
-- 用途：记录所有 trade_history / positions / decision_snapshot 的写入源
-- ============================================
CREATE TABLE IF NOT EXISTS execution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,           -- 写入时间
    source TEXT NOT NULL,              -- 执行源（skill / cron / manual / cli）
    agent_id TEXT,                     -- Agent ID
    session_id TEXT,                   -- Session ID
    operation TEXT NOT NULL,           -- 操作类型（record_buy/record_sell/...）
    target_table TEXT NOT NULL,        -- 目标表
    target_id INTEGER,                 -- 目标记录 ID
    payload_json TEXT,                 -- 写入数据（JSON）
    success INTEGER NOT NULL,          -- 1=成功 0=失败
    error_message TEXT                 -- 失败原因
);

CREATE INDEX IF NOT EXISTS idx_execution_log_timestamp ON execution_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_execution_log_source ON execution_log(source);

-- ============================================
-- v2 性能指标表：performance_metrics
-- ============================================
-- 来源：v1 43 指标 8 大类
-- 用途：每日/每周绩效指标持久化（避免每次重算）
-- ============================================
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                 -- 指标日期
    period TEXT NOT NULL,               -- 周期（daily/weekly/monthly/all_time）
    metrics_json TEXT NOT NULL,         -- 43 指标 JSON
    created_at TEXT NOT NULL,
    UNIQUE(date, period)
);

CREATE INDEX IF NOT EXISTS idx_performance_date ON performance_metrics(date);