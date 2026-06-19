-- 016_alter_stock_info_add_v1_columns.sql
-- 用途: 补齐 v1 stock_info 缺失的列（v1 有 full_code/updated_at/exchange）
-- 日期: 2026-06-19
-- 原因: Sprint-5 B 调研发现 v1 stock_info (6 列) vs v2 stock_info (7 列) 差异
--       v1 有: code/name/exchange/full_code/list_date/updated_at
--       v2 有: code/name/industry/list_date/total_shares/float_shares/created_at
-- 依赖: schema/migrations/012_create_unmigrated_tables.sql

-- 1. v1 有但 v2 缺的列（migration 时补齐）
ALTER TABLE stock_info ADD COLUMN exchange TEXT;
ALTER TABLE stock_info ADD COLUMN full_code TEXT;
ALTER TABLE stock_info ADD COLUMN updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'));