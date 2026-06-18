# PRD（产品需求文档）

> **版本**：v2.0.0-draft
> **创建**：2026-06-18
> **状态**：草案，待用户拍板

## 项目定位

**ETF 量化投资策略 v2** —— 从 v1 自用工具 → AI-Native 量化认知升级教育产品

## 调研基础

基于 2026-05-18 → 06-18 的 30 天调研：
- 12 个分批笔记（`v2-roadmap/notes/01~12_*.md`，1710 行）
- 演进复盘（`v2-roadmap/00_evolution_review.md`，23KB）
- 调研方法论（`v2-roadmap/10_research_plan.md`）

## 5 个核心转变

1. **单仓 monorepo**（`etf_quant_v2/`，独立 git）
2. **12 模块独立**（业界标准：QuantConnect LEAN / Zipline / BigQuant）
3. **5 skill 业务向**（场景驱动，不是技术模块）
4. **C2 散户"想学方"**（Q1 已拍板）
5. **AI-Native 而非 AI-Assisted**（Q1 已拍板）

## v1 关键沉淀（必须保留）

- max_hold_days=99999（持仓管理核心）
- BOLL_strict_middle+MA60 入场过滤（C21 验证）
- ComprehensiveValidator 4 验证器
- PositionGuide 22 字段决策树
- 27 因子 + W4 RV 反转因子（v9 沉淀）
- 96+ 教训库

## v1 关键陷阱（必须避免）

详见 `v2-roadmap/notes/10_lessons_curated.md`

| 陷阱 | 缓解 |
|------|------|
| 半途改造（L117）| 每个 US 列"涉及模块清单" |
| 数据架构破坏（规则 15）| pre-commit 拦截 sqlite3.connect |
| 多执行源串扰（L101）| --source 标识 |
| 假完成（L91）| progress.txt 真实 + 自评诚实 |
| 上下文漂移（L209）| 8 维度腐化自检 + CHECKPOINT.md |

## 30 US / 5 Sprint 概览

详细见 `PRD.json`（结构化数据）+ `PRD_US_breakdown.md`（人工可读）

### Sprint 划分

| Sprint | 主题 | US | 时长 |
|--------|------|:---:|:---:|
| 1 P0 基础设施 | monorepo + 契约 + DB + DataLayer + pre-commit + ETF 池 | 6 | 1 周 |
| 2 P0 核心业务 | alpha 金三角 + execution + risk + ComprehensiveValidator | 4 | 2 周 |
| 3 P1 12 模块 | performance/universe/27 因子/backtest/scheduler/notify/config/monitor/utils | 9 | 2 周 |
| 4 P2 5 skill | etf-daily/research + stock-analyze/portfolio + quant-knowledge | 5 | 1 周 |
| 5 P2 完善+发布 | 测试金字塔 + 文档 + SOP + 教训映射 + 安全审计 + v2.0 release | 6 | 1 周 |

## 执行机制（5 道防跑偏）

1. **SOP-02**（`docs/SOP_02_REFACTOR_DEV.md`）—— Phase 1-6 流程
2. **CHECKPOINT.md**（mission 目录）—— 任务对比基准
3. **COMMIT 模板**（`COMMIT_TEMPLATE.md`）—— 5 段强制
4. **8 维度腐化自检**（`scripts/腐化自检.py`）—— 每 3 US 触发
5. **Sprint 复盘模板**（`docs/SPRINT_REVIEW_TEMPLATE.md`）—— 强制 8 节

## 待您拍板

| # | 问题 | 我的建议 |
|---|------|----------|
| 1 | 30 US 全做？ | 方案 A 砍 10 → 20 US（OPC 一人公司友好）|
| 2 | v1 资产继承深度？ | 全继承 + 标记 .DEPRECATED |
| 3 | 教学层（L2）时序？ | v2.0 = L1（工具），v2.1 = L2（教学）|
| 4 | 分支策略？ | 单分支 + Sprint tag |
| 5 | 回滚策略？ | 每 Sprint 末尾 git tag + 双备份（本地 + workspace mission 跟踪）|

---

> **下一步**：您确认 PRD 后，我立即更新 loop_config.json 到 execution_confirmed，开始 Sprint-0 完成 → Sprint-1 执行。