-- 001_add_updated_at.sql
-- 用途: daily 表增加 updated_at 字段，记录数据最后入库时间
-- 日期: 2026-06-01
-- 原因: 分钟级监控需要精确入库时间

-- 1. 添加 updated_at 列（如果不存在）
ALTER TABLE daily ADD COLUMN updated_at TEXT DEFAULT (datetime('now', 'localtime'));

-- 2. 验证
SELECT 'updated_at added' AS status;
PRAGMA table_info(daily);
