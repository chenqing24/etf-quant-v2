-- 002_add_amount_source_created_at.sql
-- 用途: daily 表补齐 amount/source/created_at 字段
-- 日期: 2026-06-01
-- 原因: DataWriter.write_daily() 需要这些列，但历史数据库没有

-- 1. 添加 amount 列（如果不存在）
-- SQLite 不支持 IF NOT EXISTS for ADD COLUMN，需手动判断
ALTER TABLE daily ADD COLUMN amount REAL;

-- 2. 添加 source 列（如果不存在）
ALTER TABLE daily ADD COLUMN source TEXT DEFAULT 'tencent';

-- 3. 添加 created_at 列（如果不存在）
ALTER TABLE daily ADD COLUMN created_at TEXT DEFAULT (datetime('now', 'localtime'));

-- 4. 验证
SELECT 'columns added' AS status;
PRAGMA table_info(daily);
