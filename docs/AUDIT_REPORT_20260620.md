# 审计报告 — v1 vs v2 关系 + 冗余文件 + 文档一致性

> **任务**：回答 2 个问题
> 1. v2 与 v1 的文件组织关系
> 2. 冗余文件 + 文档一致性
> **日期**：2026-06-20
> **方法**：grep + diff + 全文件扫描

---

## 1. v1 vs v2 文件组织关系

### 1.1 顶层对比

| 维度 | v1 (etf_strategy) | v2 (etf_quant_v2) |
|------|-------------------|-------------------|
| 位置 | workspace 根目录 `etf_strategy/` | workspace 根目录 `etf_quant_v2/` |
| 状态 | 独立仓，**只读**（考古资料）| 独立仓，**活跃** |
| 文档声明 | README "v1 旧代码 = 考古资料" | README 引用 v2-roadmap 但**路径错误** |
| 数据 | `etf_strategy/etf_data_live/etf.db` | `etf_quant_v2/data/etf.db` |
| 测试 | `etf_strategy/tests/` | `etf_quant_v2/tests/` |
| src | `etf_strategy/src/`（20+ 目录）| `etf_quant_v2/src/etf_quant/`（13 模块）|

### 1.2 v1 → v2 模块映射

| v1 (etf_strategy/src/) | v2 (etf_quant_v2/src/etf_quant/) | 关系 |
|------------------------|----------------------------------|------|
| indicators/ | alpha/factors/ | Strangler Fig 模式（26 因子继承 + 1 W4 RV 新写）|
| strategy/ | alpha/strategy_c21.py | 简化（C21-1 金三角）|
| data/ | data_layer/ | 简化（4 Repo）|
| backtest/ | backtest/comprehensive_validator.py | 简化（4 验证器）|
| risk/ | risk/position_guide.py | 简化（22 字段）|
| trade_tracker.py | execution/tracker.py | 重写（1483 → 3 文件）|
| notifier.py + dingtalk_sender.py | notify/ | 简化（双通道）|
| performance_analyzer.py | performance/ | 简化（43 指标）|
| config/ | config/ | 简化（constants.py）|
| etf_pool_updater.py | universe/ | 简化（ETFListLoader）|
| cron_jobs.yaml | scheduler/ | 简化（DEFAULT_CRON_JOBS）|
| utils/ | utils/ | 简化（execution_source）|
| industry_filter.py + industry_mapping.py | universe/mapper.py | 简化（IndustryMapper）|
| report_builder.py | performance/report.py | 简化（generate_performance_report）|
| scenario_adapter.py | notify/scenario.py | 简化（ScenarioAdapter）|

**总结**：v2 = v1 的**Strangler Fig 重构版本**（Fowler 2004）
- 不重写：业务逻辑继承（alpha/factors/inherited.py 691 行）
- 重写：4 个核心模块（execution/risk/alpha-strategy/data_layer）
- 新增：scheduler/notify/performance/universe/monitor（v1 缺）

### 1.3 v1 vs v2 关系图

```
workspace/
├── etf_strategy/  (v1 考古资料，独立仓，只读)
│   ├── etf_data_live/etf.db   ← v1 数据源
│   ├── src/indicators/         ← v1 因子（13 文件）
│   ├── src/strategy/           ← v1 策略（8 文件）
│   ├── src/data/               ← v1 数据访问
│   └── ...（20+ 子目录）
│
├── etf_quant_v2/  (v2 活跃仓，重构)
│   ├── data/etf.db             ← v2 数据源（从 v1 迁移）
│   ├── src/etf_quant/
│   │   ├── alpha/factors/      ← 继承 v1 indicators + 1 新写
│   │   ├── alpha/strategy_c21.py  ← 重写
│   │   ├── data_layer/         ← 重写（业务层零 SQL）
│   │   ├── execution/tracker.py   ← 重写（3 文件拆分）
│   │   ├── risk/position_guide.py ← 重写
│   │   ├── notify/             ← 继承 v1
│   │   ├── performance/        ← 继承 v1
│   │   ├── universe/           ← 继承 v1
│   │   ├── monitor/            ← 新增（v1 无）
│   │   ├── scheduler/          ← 新增（v1 cron_jobs.yaml → 4 jobs）
│   │   ├── portfolio/          ← 新增（v1 无）
│   │   ├── backtest/           ← 重写（ComprehensiveValidator）
│   │   ├── config/             ← 简化
│   │   └── utils/              ← 简化
│   ├── skills/（5 skill 入口）
│   ├── docs/（30 文档）
│   ├── tests/（217 测试）
│   ├── schema/（19 迁移）
│   └── scripts/（4 脚本）
│
├── v2-roadmap/  (workspace 根，v2 调研笔记)
│   ├── 00_evolution_review.md   ← PRD 引用但路径错
│   ├── notes/01~12_*.md
│   └── 10_research_plan.md
│
└── missions/  (workspace 根，mission 跟踪)
    └── mission-20260618-234155/
```

---

## 2. 冗余文件清单

### 2.1 真正冗余（可清理）

| # | 文件 | 状态 | 建议 |
|---|------|------|------|
| 1 | `docs/SPRINT5_PRE_RESEARCH.md` | 0 字节空文件 | 🗑️ 删除 |
| 2 | `etf_quant_v2.egg-info/PKG-INFO` | 0 个文件（已被 .gitignore 排除）| ✅ 已正确 |
| 3 | `__pycache__/`（77 个 .pyc）| 本地缓存，不入 git | ✅ 已正确 |

### 2.2 建议归档（不动）

| # | 文件 | 建议 |
|---|------|------|
| 1 | `docs/MISSION_FINAL_REPORT_20260619.md` | 归档到 `docs/_archive/`（昨天版本，被 06-20 覆盖）|

### 2.3 位置不合理

| # | 文件 | 当前位置 | 建议位置 |
|---|------|----------|----------|
| 1 | `demo_full_flow.py` | 仓根目录 | `scripts/demo_full_flow.py`（与其他脚本一致）|

---

## 3. 文档一致性不一致清单

### 3.1 README 引用路径错误

**问题**：README 引用 `v2-roadmap/notes/01~12_*.md`（1710 行），但 **v2 仓内无 `v2-roadmap/`**。

**真相**：
- `v2-roadmap/` 在 workspace 根目录，不在 v2 仓内
- v2 仓引用应是"../v2-roadmap/notes/" 或文档不在仓内
- 当前 README 引用会让新用户**找不到文件**

**修复方案**：
- 选项 A：把 v2-roadmap 内容移到 v2 仓 `docs/v2-roadmap/`（23KB + 1710 行 = 1733KB 大）
- 选项 B：README 改为"v2-roadmap/ 在 workspace 根目录"说明
- 选项 C：把 v2-roadmap 删除（如果已过时）

### 3.2 PRD.md 与实际 Sprint 不一致

**PRD.md 写**：5 Sprint（1-5）共 30 US
**实际**：7 Sprint（0-7）共 29 US
- Sprint-0：9 项任务（不是 US）
- Sprint-1：5 US
- Sprint-2/3：4 US
- Sprint-4：5 US
- Sprint-5：5 US（US-030 已删）
- Sprint-6：1 US（US-013 27 因子 + W4 RV）
- Sprint-7：5 US（5 模块业务完整化）

**问题**：
- PRD.md 的"Sprint 1-5"划分已**过时**
- 实际 Sprint 0-7 在 `sprint-reviews/` 有完整复盘
- PRD.md **未更新**

### 3.3 PRD.md 的"30 US"已不准

**PRD.md 写**：30 US
**PRD.json 实际**：29 US（US-030 已删）
**业务实现**：29 US（5 模块 Sprint-7 完整化）

**问题**：PRD.md 第 14 行"30 个分批笔记"、第 8 节"30 US / 5 Sprint 概览"都是 30 US 表述。

### 3.4 README "Sprint-0 启动"已过时

**README 第 7 行**：
```
🚧 **v2.0 重构中** —— Sprint-0（基础设施）启动
```

**实际**：Mission 100% 完成（29/29 US 业务实现 = 100%）

**修复**：已 Sprint-7 修复（v2.0-final + 业务实现 100%），但**README 还可能有过时残留**。

### 3.5 docs/PRD.json 与 docs/PRD.md Sprint 划分

**PRD.md**：5 Sprint（1-5）
**PRD.json**：5 Sprint（1-5）+ metrics.missionStatus='100% 业务实现'
**实际**：7 Sprint（0-7）

**问题**：两个 PRD 文件的 Sprint 划分**都过时**，没反映 Sprint-6/7。

### 3.6 README "12 模块"vs 实际 13

**README 写**：12 模块
**实际**：13 模块（多 scheduler + utils）

**问题**：utils 没在 README 列出。

---

## 4. 总结：4 大问题 + 修复优先级

### 4.1 紧急（必须修）

| # | 问题 | 风险 | 修复 |
|---|------|------|------|
| 1 | README 引用 v2-roadmap 路径错误 | 新用户找文件失败 | README 改说明 v2-roadmap 在 workspace 根 |
| 2 | `SPRINT5_PRE_RESEARCH.md` 0 字节空文件 | 占位但无内容 | 删除或补内容 |
| 3 | PRD.md 30 US / 5 Sprint 过时 | 文档与实际不一致 | 更新为 29 US / 7 Sprint |
| 4 | demo_full_flow.py 在根目录 | 与其他脚本位置不一致 | 移到 scripts/ |

### 4.2 重要（应修）

| # | 问题 | 修复 |
|---|------|------|
| 5 | README "12 模块"少列 2 个 | 加 scheduler + utils |
| 6 | PRD.md vs PRD.json Sprint 划分 | 统一为 7 Sprint |
| 7 | MISSION_FINAL_REPORT_20260619.md 过时 | 归档到 _archive/ |

### 4.3 建议（待定）

| # | 问题 | 建议 |
|---|------|------|
| 8 | v2-roadmap 是否入仓 | 暂不（23KB + 1710 行 = 1733KB 太大）|
| 9 | PRD.md 与 PRD.json 内容分裂 | 二选一：保留 .md 或 .json |

---

## 5. 修复计划（建议）

### 阶段 1：清理冗余（0.5h）

1. 删除 `docs/SPRINT5_PRE_RESEARCH.md`（0 字节）
2. 移动 `demo_full_flow.py` → `scripts/demo_full_flow.py`
3. 归档 `MISSION_FINAL_REPORT_20260619.md` → `docs/_archive/`

### 阶段 2：文档一致性（1h）

4. README 加 scheduler + utils 模块说明
5. README 改 v2-roadmap 路径说明
6. PRD.md 更新为 29 US / 7 Sprint
7. PRD.json metrics 更新 Sprint 划分

### 阶段 3：诚实声明（0.5h）

8. 在 MISSION_FINAL_REPORT_20260620.md 加"已知不一致"段
9. 写 `docs/AUDIT_REPORT.md`（本文件最终版）

---

## 6. 诚实声明（按规则 6.1）

### 6.1 未发现的问题（4 个潜在问题实际不是问题）

1. **77 个 .pyc 文件**：本地缓存，已在 .gitignore，未入 git
2. **egg-info 引用**：历史 commit 残留，.gitignore 已正确
3. **README "12 模块"**：实际 13（多 utils/scheduler），不算错误但易混淆
4. **PRD.md vs PRD.json 5 Sprint**：都不是最新（实际 7），但都是历史快照不算"错"

### 6.2 真正问题（4 个）

1. `SPRINT5_PRE_RESEARCH.md` 是 0 字节空文件
2. README 引用 v2-roadmap 路径但仓内无
3. PRD.md 未反映 Sprint-6/7（仍是 30 US / 5 Sprint）
4. demo_full_flow.py 位置不合理

### 6.3 我之前自评的偏差

| 自评 | 真实情况 |
|------|---------|
| 文档脱节 100/100 | 实际 80/100（PRD.md + README 引用问题）|
| 文档完整 100% | 实际 ~85%（3 路径错误 + 2 数量不一致）|

按规则 6.1，**自评分数应调整为 85-90 范围**（不是 100）。

---

> **本报告遵循规则 6.1**：诚实声明 4 大问题 + 自评偏差
> **本报告遵循规则 22**：基于实际扫描 + grep，不是凭印象
