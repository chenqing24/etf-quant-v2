-- 013_alter_etf_name_metrics_fix_columns.sql
-- 用途: 修正 etf_name_metrics 表列名（v2 schema 012 与 v1 业务库不一致）
-- 日期: 2026-06-19
-- 原因: Sprint-3 B 调研不彻底（只比较列数），Sprint-4 B 调研发现真实列名差异
--       v1 业务库：id/code/success/verified/duration_ms/sources_tried/created_at
--       v2 schema 012：id/timestamp/source/code/success/duration_ms/error_message
-- 依赖: schema/migrations/012_create_unmigrated_tables.sql

-- SQLite 不支持 DROP COLUMN 在旧版本，但支持 ALTER TABLE RENAME COLUMN
-- v2 schema 012 错误地建了 4 列：timestamp/source/error_message（多余）+ 缺 3 列（verified/sources_tried/created_at）
-- 修复策略：drop 错误列 → add 缺失列

-- 1. 先删依赖多余列的索引（v2 schema 012 创建了 idx_etf_name_metrics_source）
DROP INDEX IF EXISTS idx_etf_name_metrics_source;

-- 2. 重命名：timestamp → created_at
ALTER TABLE etf_name_metrics RENAME COLUMN timestamp TO created_at;

-- 3. 删除 v2 schema 012 多余的列（source/error_message）
ALTER TABLE etf_name_metrics DROP COLUMN source;
ALTER TABLE etf_name_metrics DROP COLUMN error_message;

-- 4. 添加 v1 业务库有但 v2 缺的列（verified/sources_tried）
ALTER TABLE etf_name_metrics ADD COLUMN verified INTEGER NOT NULL DEFAULT 0;
ALTER TABLE etf_name_metrics ADD COLUMN sources_tried TEXT NOT NULL DEFAULT '[]';

-- 4. code 字段改为 NOT NULL（v1 业务库实际）
-- 注意：SQLite 不支持直接改 NULL → NOT NULL，需重建表
-- 这里使用 v1 实际值（大多数 v1 记录 code 可能为 NULL，但 v1 schema 列上是 NULL）
-- 保留 NULL 兼容 v1
