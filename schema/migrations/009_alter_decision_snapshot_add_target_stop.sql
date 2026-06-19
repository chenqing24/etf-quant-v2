-- 009_alter_decision_snapshot_add_target_stop.sql
-- 用途: 补齐 v1 decision_snapshot 缺失的 5 列（v1 业务库 19 列 vs v2 迁移 14 列）
-- 日期: 2026-06-19
-- 原因: V1_VS_V2_SCHEMA_AUDIT.md 调研发现 5 列未迁移
-- 依赖: schema/migrations/007_add_decision_snapshot_table.sql

ALTER TABLE decision_snapshot ADD COLUMN target_price REAL NOT NULL DEFAULT 0;
ALTER TABLE decision_snapshot ADD COLUMN stop_loss_price REAL NOT NULL DEFAULT 0;
ALTER TABLE decision_snapshot ADD COLUMN stop_profit_price REAL NOT NULL DEFAULT 0;
ALTER TABLE decision_snapshot ADD COLUMN risk_reward_ratio REAL NOT NULL DEFAULT 0;
ALTER TABLE decision_snapshot ADD COLUMN expected_hold_days INTEGER NOT NULL DEFAULT 0;
