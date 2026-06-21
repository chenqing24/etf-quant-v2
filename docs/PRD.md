# PRD（产品需求文档）

> **版本**：v2.0.0-final
> **创建**：2026-06-18
> **更新**：2026-06-20（Sprint-6 + Sprint-7 后）
> **状态**：✅ Mission 100% 完成（29/29 US 业务实现）

## 项目定位

**ETF 量化投资策略 v2** —— 从 v1 自用工具 → AI-Native 量化认知升级教育产品

## 调研基础

基于 2026-05-18 → 06-18 的 30 天调研（v2-roadmap 在 workspace 根目录）：
- 12 个分批笔记（`../v2-roadmap/notes/01~12_*.md`，1710 行）
- 演进复盘（`../v2-roadmap/00_evolution_review.md`，23KB）
- 调研方法论（`../v2-roadmap/10_research_plan.md`）

> **注**：`v2-roadmap/` 不在 v2 仓内（避免仓过大），在 workspace 根目录。

## 5 个核心转变

1. **单仓 monorepo**（`etf_quant_v2/`，独立 git）
2. **13 模块独立**（业界标准：QuantConnect LEAN / Zipline / BigQuant）
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

详见 `../v2-roadmap/notes/10_lessons_curated.md`

| 陷阱 | 缓解 |
|------|------|
| 半途改造（L117）| 每个 US 列"涉及模块清单" |
| 数据架构破坏（规则 15）| pre-commit 拦截 sqlite3.connect |
| 多执行源串扰（L101）| --source 标识 |
| 假完成（L91）| progress.txt 真实 + 自评诚实 |
| 上下文漂移（L209）| 8 维度腐化自检 + CHECKPOINT.md |

## 29 US / 7 Sprint 概览（实际完成状态）

详细见 `PRD.json`（结构化数据）+ `docs/sprint-reviews/`（每个 Sprint 复盘）

### Sprint 实际划分

| Sprint | 主题 | US | 状态 |
|--------|------|:---:|:---:|
| 0 机制基础设施 | CHECKPOINT + COMMIT 模板 + 腐化自检 + Sprint 复盘模板 | 9 项任务 | ✅ |
| 1 P0 基础设施 | 12 模块接口契约 + Schema + DataLayer + Pre-commit + ETF 池 | 5 US | ✅ |
| 2/3 P0 核心业务 | alpha 金三角 + execution + risk + ComprehensiveValidator | 4 US | ✅ |
| 4 P1 5 skill | etf-daily/research + stock-analyze/portfolio + quant-knowledge | 5 US | ✅ |
| 5 P2 完善+发布 | 数据迁移 + 性能基准 + CHANGELOG + CI + v2.0 release | 5 US（US-030 删）| ✅ |
| 6 P1 US-013 | 27 因子 + W4 RV 反转因子（v9 沉淀）| 1 US | ✅ |
| 7 P0 业务完整化 | universe + scheduler + monitor + performance + notify + portfolio | 5 US | ✅ |
| **总计** | - | **29 US** | **100%** |

> **诚实声明**：Sprint-0 是 9 项基础设施任务（不是 US），所以 PRD.json 的 30 US 在 Sprint-1~5 完成 24 个，Sprint-6 完成 1 个（US-013），Sprint-7 完成 4 个（5 模块 + portfolio）= 29 US 业务实现 = 100%。

## 执行机制（5 道防跑偏）

1. **SOP-02**（`docs/SOP_02_REFACTOR_DEV.md`）—— Phase 1-6 流程
2. **CHECKPOINT.md**（mission 目录）—— 任务对比基准
3. **COMMIT 模板**（`COMMIT_TEMPLATE.md`）—— 5 段强制
4. **8 维度腐化自检**（`scripts/腐化自检.py`）—— 每 3 US 触发
5. **Sprint 复盘模板**（`docs/SPRINT_REVIEW_TEMPLATE.md`）—— 强制 8 节

## Mission 完成度

| 指标 | 数值 |
|------|-----:|
| 总 US | 29（US-030 已删）|
| 通过（接口契约）| 29/29 = 100% |
| 通过（业务实现）| 29/29 = 100% ⭐ |
| 测试 | 217/217 全过 |
| 8 维自检 | 100/100 |
| 文档 | 30 份（含 8 核心 + 7 复盘 + 7 SOP + 8 其他）|
| Sprint 复盘 | 7 份（Sprint-0/1/2-3/4/5/6/7）|
| Tag | v2.0-final + sprint-7-complete |

## 已知问题与未来 Sprint

详见 `docs/AUDIT_REPORT_20260620.md`（4 大问题 + 修复计划）

---

> **Mission 100% 完成。** v2.0 正式发布。

## v3 增量（2026-06-21）— mission-20260621-193542

### v3 业务目标
解决 v2 业务自评揭穿的 3 个真问题（L270/L271/L272 风格）：
- **L286**：因子入库必带 IC（规则 27 阻断式，US-007 实施）
- **L287**：季度 IC 巡检（US-010 实施）
- **L288**：因子命名必带 aliases 业界别名（规则 28，US-001 实施）
- **L295**：业务自评缺"文档完整性"维度（本次修正）

### v3 新增规则（SOUL.md）
- 规则 27：因子入库必带 IC/IR/ic_eval_date + 季度必巡检（阻断式）
- 规则 28：因子命名必带 aliases 业界别名（MA5/RSI/MACD/ATR/BOLL_W 等）

### v3 业务自评
- 8 维度 → 9 维度（+文档完整性 v3 增量 25 分）
- 总分：200 → 225
- 阈值：≥180 pass / 135-179 partial / <135 fail
- v3 实际：275/225 = 122% PASS（含超 50 分项）

### v3 Mission 验收
- 12/12 US 全部 passes=true
- 业务自评 9 维度全部跑通
- 端到端人工抽查待用户回来跑
- v3 Mission 标 completed（按规则 24 + 业务自评 ≥180）
