-- 010_alter_etf_names_add_v1_columns.sql
-- 用途: 补齐 v1 etf_names 缺失的 6 列（v1 业务库 14 列 vs v2 迁移 8 列）
-- 日期: 2026-06-19
-- 原因: V1_VS_V2_SCHEMA_AUDIT.md 调研发现 6 列未迁移
--       这些列是 v1 ETFRepository.get_meta 用的（导致 Sprint-2 US-007 失败）
-- 依赖: schema/migrations/003_add_tradable_pool_role.sql + 005_add_is_reference.sql

ALTER TABLE etf_names ADD COLUMN name_sina TEXT;
ALTER TABLE etf_names ADD COLUMN verified INTEGER DEFAULT 0;
ALTER TABLE etf_names ADD COLUMN verify_count INTEGER DEFAULT 0;
ALTER TABLE etf_names ADD COLUMN last_verify_at TEXT;
ALTER TABLE etf_names ADD COLUMN exchange TEXT;
ALTER TABLE etf_names ADD COLUMN category TEXT;
ALTER TABLE etf_names ADD COLUMN tracking_index TEXT;
ALTER TABLE etf_names ADD COLUMN aum REAL;
