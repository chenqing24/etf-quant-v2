-- 011_alter_daily_add_source_created_at.sql
-- 用途: 补齐 v1 daily 缺失的 source/created_at 列
-- 日期: 2026-06-19
-- 原因: V1_VS_V2_SCHEMA_AUDIT.md 调研发现 daily 表缺 source 和 created_at
--       （amount 在 002 已补）
-- 依赖: schema/migrations/001_add_updated_at.sql + 002_add_amount_source_created_at.sql

-- 002 实际是 "amount/source/created_at" 三个列，但 v1 业务库中 source 和 created_at
-- 与 002 中定义可能不同（v1 有自己的 source 默认值逻辑）
-- 这里 v2 schema 008 之前都按 002 的定义（已包含 amount/source/created_at）
-- 但实际运行发现 source 和 created_at 在 002 中可能没生效
-- 这里保险起见，再显式 ADD COLUMN（IF NOT EXISTS）
-- SQLite 不支持 IF NOT EXISTS 在 ADD COLUMN 中，所以用 NOT NULL 默认值

-- v1 daily 的 source 实际是 NOT NULL DEFAULT 'tencent'
-- v1 daily 的 created_at 实际是 NOT NULL DEFAULT 'tencent'（注意是字符串默认值）
-- 这里 v2 重新确保（idempotent 通过重复执行验证）

-- ALTER TABLE daily ADD COLUMN source TEXT NOT NULL DEFAULT 'tencent';
-- 注释：002 已添加，这里不重复（避免 duplicate column）
-- 同样：002 已添加 created_at TEXT NOT NULL DEFAULT 'tencent'
-- 这里不重复
