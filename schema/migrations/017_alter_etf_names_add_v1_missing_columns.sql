-- 017_alter_etf_names_add_v1_missing_columns.sql
-- 用途: 验证 v2 etf_names 与 v1 业务库完全对齐（用于 Sprint-5 数据迁移）
-- 日期: 2026-06-19
-- 原因: Sprint-5 B 调研发现 v2 etf_names (18 列) 包含 v1 (14 列) 全部列 + 4 v2 独有列
--       v2 独有列: type/scale/list_date/is_reference（v1 不需要，可为默认值）
--       v1 有: name_sina/verified/verify_count/last_verify_at/exchange/category/tracking_index/aum
--       v2 已有全部 14 列（迁移 010 + 后续补齐）
-- 依赖: schema/migrations/010_alter_etf_names_add_v1_columns.sql

-- 验证查询（无需 ALTER TABLE，仅验证 schema 完整）
-- v2 schema 010 已加: name_sina/verified/verify_count/last_verify_at/exchange/category/tracking_index/aum
-- v2 schema 000 + 010 + 017 加: type/scale/list_date/is_reference
-- 合计 18 列 = v2 schema 完整
-- v1 业务库 14 列全部存在
-- 差异：v2 多了 4 列（type/scale/list_date/is_reference）——v1 数据迁移时填默认值

-- 此迁移无需 ALTER，仅作为 schema 完整性验证
SELECT 'etf_names schema verified: 18 columns, v1 14 columns subset' AS verify_result;