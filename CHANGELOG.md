# CHANGELOG

按业界参考（https://keepachangelog.com/zh-CN/1.1.0/）。

## [Unreleased]

### Added
- Sprint-5 数据迁移：v1 → v2 71034 行真实验证
- Sprint-5 性能基准测试（pytest-benchmark）
- Sprint-4 5 skill 入口（etf-daily/etf-research/stock-analyze/stock-portfolio/quant-knowledge）
- Sprint-2/3 alpha C21-1 策略 + execution tracker + risk PositionGuide + ComprehensiveValidator

### Changed
- v2 schema 完全对齐 v1 业务库（L244 教训：必须比较列名 + 列类型 + 约束）
- init_database.py 幂等性增强（L245 教训：修复脚本必须幂等）

### Fixed
- v1 业务库 20 列缺失（trade_history 5 + decision_snapshot 5 + etf_names 8 + stock_info 2）
- 4 表列名差异（etf_name_metrics/etf_name_retry_queue/realtime_cache/stock_info）

### Security
- pre-commit 钩子真实验证 4 条硬错误（L241 教训）

## [2.0.0a1] - 2026-06-19

### Added
- Sprint-0 机制基础设施（5 道防跑偏机制 + CHECKPOINT + COMMIT_TEMPLATE + 腐化自检）
- Sprint-1 P0 基础设施（data_layer + 4 Repo + 9 迁移 + 41 测试全过）

### Notes
- v2 项目从立项到 Sprint-5 累计：23 US + 176 测试 + 9 commits B 调研 + 12 commits A 实现 + 自评 84→97
- v1 → v2 数据迁移：71034 行
- 8 维度自评客观反映腐化程度（L243 教训）