-- 006_add_trade_target_stop.sql
-- US-002: trade_history 加 5 决策目标价字段
-- 日期: 2026-06-10
-- 原因: 决策快照 v1.1 升级（TRADE_RECORD_SPEC），trade_history 缺 target/stop 价格字段
-- 业界参考: MiFID II / QuantConnect Lean Insight / Backtrader
-- 依赖: 004_add_trade_tables.sql

-- 默认值策略（规则 19 黑名单模式）：新加列默认 NULL
-- NULL 语义 = "该交易无目标价"（历史数据 + 未来非决策性交易）
-- 显式录入后才会有值

ALTER TABLE trade_history ADD COLUMN target_price REAL;
ALTER TABLE trade_history ADD COLUMN stop_loss_price REAL;
ALTER TABLE trade_history ADD COLUMN stop_profit_price REAL;
ALTER TABLE trade_history ADD COLUMN risk_reward_ratio REAL;
ALTER TABLE trade_history ADD COLUMN max_hold_days INTEGER;

-- 索引：加速按 target_price 查询
CREATE INDEX IF NOT EXISTS idx_trade_target_price ON trade_history(target_price);
