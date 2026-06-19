-- 008_alter_trade_history_add_target_stop.sql
-- 用途: 补齐 v1 trade_history 缺失的 5 列（v1 业务库 37 列 vs v2 迁移 31 列）
-- 日期: 2026-06-19
-- 原因: V1_VS_V2_SCHEMA_AUDIT.md 调研发现 5 个 NOT NULL 列未迁移
-- 依赖: schema/migrations/004_add_trade_tables.sql

ALTER TABLE trade_history ADD COLUMN target_price REAL NOT NULL DEFAULT 0;
ALTER TABLE trade_history ADD COLUMN stop_loss_price REAL NOT NULL DEFAULT 0;
ALTER TABLE trade_history ADD COLUMN stop_profit_price REAL NOT NULL DEFAULT 0;
ALTER TABLE trade_history ADD COLUMN risk_reward_ratio REAL NOT NULL DEFAULT 0;
ALTER TABLE trade_history ADD COLUMN max_hold_days INTEGER NOT NULL DEFAULT 99999;
