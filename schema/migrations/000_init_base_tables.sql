-- 000_init_base_tables.sql
-- 用途: v2 启动建基础表（daily / etf_names）
-- 日期: 2026-06-19
-- 原因: v1 001-007 假设 daily/etf_names 已存在（v1 有独立的 init_db 脚本）
--       v2 必须有 000 迁移建基础表
-- 依赖: 无（最优先）
-- 触发事件: v2 init_database.py 实际跑迁移时发现 3/8 失败（按 L228 教训）
--
-- 来源：
-- - v1 src/data/database.py: CREATE TABLE daily / etf_names
-- - 业界参考：Flyway / Liquibase / Alembic（基础表必须在依赖表前）

-- ============================================
-- daily: 日线数据表（v1 主数据表）
-- ============================================
CREATE TABLE IF NOT EXISTS daily (
    code TEXT NOT NULL,                  -- ETF 代码（无前缀）
    date TEXT NOT NULL,                  -- 日期 YYYY-MM-DD
    open REAL NOT NULL,                  -- 开盘价
    high REAL NOT NULL,                  -- 最高价
    low REAL NOT NULL,                   -- 最低价
    close REAL NOT NULL,                 -- 收盘价
    volume INTEGER NOT NULL,             -- 成交量
    amount REAL,                         -- 成交额（v1 002 补）
    source TEXT DEFAULT 'tencent',       -- 数据源（v1 002 补）
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT,                     -- 分钟级监控（v1 001）
    PRIMARY KEY (code, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_date ON daily(date);
CREATE INDEX IF NOT EXISTS idx_daily_code ON daily(code);

-- ============================================
-- etf_names: ETF 元数据 + 池角色
-- ============================================
CREATE TABLE IF NOT EXISTS etf_names (
    code TEXT PRIMARY KEY,               -- ETF 代码（无前缀）
    name TEXT NOT NULL,                  -- ETF 名称
    type TEXT,                           -- 类型（宽基/行业/主题）
    scale REAL,                          -- 规模（亿元）
    list_date TEXT,                      -- 上市日期
    tradable INTEGER DEFAULT 0,          -- 是否可交易（v1 003）
    pool_role TEXT DEFAULT 'unclassified', -- 池角色（v1 003）
    is_reference INTEGER DEFAULT 0,      -- 300ETF 参考标记（v1 005）
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_etf_names_pool ON etf_names(pool_role);
CREATE INDEX IF NOT EXISTS idx_etf_names_tradable ON etf_names(tradable);