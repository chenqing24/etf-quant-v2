-- 005_add_is_reference.sql
-- US-014 R2: reference 池交易进 positions 表
-- 日期: 2026-06-03
-- 原因: US-008 实施时 _rebuild_positions_from_trades 只看 core 池，
--      reference 池（如 510300）即使被用户交易也不会建持仓

ALTER TABLE positions ADD COLUMN is_reference INTEGER NOT NULL DEFAULT 0;

-- 索引：加速按 is_reference 过滤
CREATE INDEX IF NOT EXISTS idx_positions_is_reference ON positions(is_reference);
