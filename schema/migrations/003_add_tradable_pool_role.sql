-- 003_add_tradable_pool_role.sql
-- 用途: etf_names 加 tradable + pool_role 字段
-- 日期: 2026-06-03
-- 原因: US-002 让代码识别"核心/参考/排除"三类 ETF
-- 依赖: US-001（池单一数据源）
--
-- 设计决策（US-002 修正版）：
-- 默认值采用保守策略：tradable=0, pool_role='unclassified'
-- 这意味着新字段后所有 ETF 默认为"未分类、不可交易"
-- 然后由 migrate_pool_roles.py 显式标注 14 core + 1 reference + ~30 excluded
-- 其余 1431 只保持 unclassified（保守默认）

-- 1. 添加 tradable 列（默认 0 = 不可交易，保守）
ALTER TABLE etf_names ADD COLUMN tradable INTEGER DEFAULT 0;

-- 2. 添加 pool_role 列（默认 'unclassified' = 未分类）
ALTER TABLE etf_names ADD COLUMN pool_role TEXT DEFAULT 'unclassified';

-- 3. 创建索引（加速按 role 过滤）
CREATE INDEX IF NOT EXISTS idx_etf_names_pool_role ON etf_names(pool_role);
CREATE INDEX IF NOT EXISTS idx_etf_names_tradable ON etf_names(tradable);

-- 4. 验证
SELECT 'tradable + pool_role added (defaults: tradable=0, pool_role=unclassified)' AS status;
