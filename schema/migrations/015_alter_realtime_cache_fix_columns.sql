-- 015_alter_realtime_cache_fix_columns.sql
-- 用途: 修正 realtime_cache 表列名
-- 日期: 2026-06-19
-- 原因: Sprint-4 B 调研发现 v2 schema 012 与 v1 业务库列名不一致
--       v1 业务库：code/name/price/change/change_pct/volume/amount/timestamp/updated_at（9 列）
--       v2 schema 012：code/price/change_pct/volume/source/cached_at/expires_at（7 列）
-- 依赖: schema/migrations/012_create_unmigrated_tables.sql

-- 1. 重命名：cached_at → updated_at（v1 用 updated_at）
ALTER TABLE realtime_cache RENAME COLUMN cached_at TO updated_at;

-- 2. 删除 v2 schema 012 多余的列（source/expires_at）
ALTER TABLE realtime_cache DROP COLUMN source;
ALTER TABLE realtime_cache DROP COLUMN expires_at;

-- 3. 添加 v1 业务库有但 v2 缺的列（name/change/volume/amount/timestamp）
ALTER TABLE realtime_cache ADD COLUMN name TEXT NOT NULL DEFAULT '';
ALTER TABLE realtime_cache ADD COLUMN change REAL NOT NULL DEFAULT 0;
ALTER TABLE realtime_cache ADD COLUMN volume REAL NOT NULL DEFAULT 0;
ALTER TABLE realtime_cache ADD COLUMN amount REAL NOT NULL DEFAULT 0;
ALTER TABLE realtime_cache ADD COLUMN timestamp TEXT NOT NULL DEFAULT '';
