-- 014_alter_etf_name_retry_queue_fix_columns.sql
-- 用途: 修正 etf_name_retry_queue 表列名
-- 日期: 2026-06-19
-- 原因: Sprint-4 B 调研发现 v2 schema 012 与 v1 业务库列名不一致
--       v1 业务库：code/attempt_count/last_error/status/priority/created_at/next_retry_at/finished_at
--       v2 schema 012：id/code/source/retry_count/max_retry/next_retry_at/last_error/created_at
-- 依赖: schema/migrations/012_create_unmigrated_tables.sql

-- 1. 重命名：retry_count → attempt_count
ALTER TABLE etf_name_retry_queue RENAME COLUMN retry_count TO attempt_count;

-- 2. 删除 v2 schema 012 多余的列（id/source/max_retry）
ALTER TABLE etf_name_retry_queue DROP COLUMN source;
ALTER TABLE etf_name_retry_queue DROP COLUMN max_retry;

-- 3. 添加 v1 业务库有但 v2 缺的列（status/priority/finished_at）
ALTER TABLE etf_name_retry_queue ADD COLUMN status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE etf_name_retry_queue ADD COLUMN priority INTEGER NOT NULL DEFAULT 0;
ALTER TABLE etf_name_retry_queue ADD COLUMN finished_at TEXT NOT NULL DEFAULT '';
