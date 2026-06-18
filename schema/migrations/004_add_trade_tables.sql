-- 004_add_trade_tables.sql
-- 用途: TradeTracker 从 JSON 文件迁移到 SQLite（US-008）
-- 日期: 2026-06-03
-- 原因: 修复 US-005 数据层架构错误（违反规则 15"数据源统一"）
--       修复 Q-009 决策上下文 4 字段缺失
--       修复 can_buy 默认 max_holdings=1 擅自假设（实际应为 2）
-- 依赖: US-005 (状态机)
-- 调研: docs/TRADE_RECORD_SPEC.md Q-009 + docs/SOP_06_MANUAL_TRADE.md v2.0 + 业界 3 GitHub 项目

-- ============================================
-- trade_history: 交易记录（31 字段）
-- ============================================
CREATE TABLE IF NOT EXISTS trade_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                              -- 交易日期 YYYY-MM-DD
    code TEXT NOT NULL,                              -- ETF 代码
    name TEXT NOT NULL,                              -- ETF 名称
    action TEXT NOT NULL CHECK(action IN ('buy','sell')),  -- 动作
    price REAL NOT NULL,                             -- 成交价格
    quantity INTEGER NOT NULL,                       -- 数量
    amount REAL NOT NULL,                            -- 金额 = price × quantity
    reason TEXT,                                     -- 交易原因

    -- SOP-06 v2.0 情绪/时段
    emotion TEXT CHECK(emotion IN ('calm','euphoria','fear','fomo','regret') OR emotion IS NULL),
    session TEXT CHECK(session IN ('A','B','C','D','E','F') OR session IS NULL),

    -- SOP-06 v2.0 信号快照
    signal_time TEXT,
    signal_price REAL,
    signal_rsi REAL,
    signal_adx REAL,
    signal_score INTEGER,

    -- 实时快照
    realtime_price REAL,
    price_deviation REAL,
    rsi_14 REAL,
    day_change_pct REAL,
    score INTEGER,                                   -- 持仓评分

    -- 损益
    expected_return REAL DEFAULT 0,
    actual_pnl REAL DEFAULT 0,
    note TEXT,
    trade_time TEXT,                                 -- 实际成交时间

    -- US-008 新增：区分实盘 vs 模拟
    is_real INTEGER NOT NULL DEFAULT 0,              -- 0=模拟, 1=实盘
    is_paper INTEGER NOT NULL DEFAULT 0,             -- 0=非纸面, 1=纸面（回测用）

    -- Q-009 决策上下文（之前漏的）
    model TEXT,                                      -- 模型名 'ETF量化决策v8_sop'
    strategy TEXT,                                   -- 策略配置 JSON
    evaluation TEXT,                                 -- 评价指标 JSON
    snapshot_ref TEXT,                               -- 决策快照文件路径

    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (code) REFERENCES etf_names(code)
);

CREATE INDEX IF NOT EXISTS idx_trade_code ON trade_history(code);
CREATE INDEX IF NOT EXISTS idx_trade_date ON trade_history(date);
CREATE INDEX IF NOT EXISTS idx_trade_action ON trade_history(action);
CREATE INDEX IF NOT EXISTS idx_trade_is_real ON trade_history(is_real);

-- ============================================
-- positions: 当前持仓（13 字段）
-- ============================================
CREATE TABLE IF NOT EXISTS positions (
    code TEXT PRIMARY KEY,                           -- ETF 代码
    name TEXT NOT NULL,
    entry_date TEXT NOT NULL,                        -- 建仓日期
    entry_price REAL NOT NULL,                       -- 建仓价格
    quantity INTEGER NOT NULL,                       -- 持仓数量
    current_price REAL DEFAULT 0,                    -- 当前价格
    pnl_pct REAL DEFAULT 0,                          -- 盈亏百分比
    hold_days INTEGER DEFAULT 0,                     -- 持仓天数
    status TEXT DEFAULT 'EMPTY'                      -- US-005 状态机
        CHECK(status IN ('EMPTY','PENDING','HOLDING','REBALANCING','CLOSING')),
    score INTEGER DEFAULT 0,                         -- 持仓评分

    -- US-008 新增
    is_real INTEGER NOT NULL DEFAULT 0,              -- 实盘/模拟
    legacy_holding INTEGER NOT NULL DEFAULT 0,       -- 是否 legacy_holding 角色

    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (code) REFERENCES etf_names(code)
);

CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_is_real ON positions(is_real);
CREATE INDEX IF NOT EXISTS idx_positions_legacy ON positions(legacy_holding);

-- ============================================
-- audit_log: 状态机审计（7 字段）
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    action TEXT NOT NULL,                            -- 'state_change'/'record_buy'/'record_sell'/'check_stop'/'migrate'
    code TEXT,                                       -- 相关 ETF
    from_state TEXT,                                 -- US-005 状态机
    to_state TEXT,
    detail TEXT,                                     -- JSON 详情
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_code ON audit_log(code);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(timestamp);

-- ============================================
-- 验证
-- ============================================
SELECT 'trade_history: ' || (SELECT COUNT(*) FROM pragma_table_info('trade_history')) || ' columns' AS status;
SELECT 'positions: ' || (SELECT COUNT(*) FROM pragma_table_info('positions')) || ' columns' AS status;
SELECT 'audit_log: ' || (SELECT COUNT(*) FROM pragma_table_info('audit_log')) || ' columns' AS status;
