-- 007_add_decision_snapshot_table.sql
-- US-002: 决策快照持久化（从文件系统迁到 SQLite）
-- 日期: 2026-06-10
-- 原因: 决策快照原本在 etf_data_live/decision_snapshot.json，
--       按规则 19 Single Source of Truth 应进 db
-- 业界参考: MiFID II / QuantConnect Lean / CQRS Event Sourcing
-- 依赖: 无（独立表）

-- PRD AC2: 14 字段（决策快照本身的元数据，不冗余 trade_history 派生列）

CREATE TABLE IF NOT EXISTS decision_snapshot (
  snapshot_id TEXT PRIMARY KEY,            -- 1
  snapshot_time TEXT NOT NULL,             -- 2
  trigger TEXT NOT NULL,                   -- 3  'daily' / 'eval' / 'manual'
  model_name TEXT,                         -- 4
  model_version TEXT,                      -- 5
  strategy_name TEXT,                      -- 6
  config_json TEXT NOT NULL,               -- 7  完整配置
  evaluation_json TEXT,                    -- 8  评价指标
  factor_breakdown_json TEXT,              -- 9  top_5_models
  today_top_10_json TEXT,                  -- 10 今日推荐
  backtest_last_10_json TEXT,              -- 11 回测最近 10 笔
  market_regime TEXT,                      -- 12 市场结构判定
  reasoning TEXT,                          -- 13 决策理由
  created_at TEXT NOT NULL                 -- 14
);

-- AC2: 2 索引
CREATE INDEX IF NOT EXISTS idx_snapshot_time ON decision_snapshot(snapshot_time);
CREATE INDEX IF NOT EXISTS idx_snapshot_model ON decision_snapshot(model_name, model_version);

-- 派生字段补丁（US-002 worker 漏写，控制器补）
-- 日期: 2026-06-10
-- 原因: 完整 PRD 要求 14 字段，含 target/stop 派生列
-- 注: 现实已存在 decision_snapshot 表（5 ALTER 需用预扫描策略保持幂等）

ALTER TABLE decision_snapshot ADD COLUMN target_price REAL;
ALTER TABLE decision_snapshot ADD COLUMN stop_loss_price REAL;
ALTER TABLE decision_snapshot ADD COLUMN stop_profit_price REAL;
ALTER TABLE decision_snapshot ADD COLUMN risk_reward_ratio REAL;
ALTER TABLE decision_snapshot ADD COLUMN expected_hold_days INTEGER;
