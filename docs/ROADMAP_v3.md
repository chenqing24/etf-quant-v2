# v3.0 路线图（2026-06-29 重构）

> **生成者**：福猫管家 🐱
> **生成时间**：2026-06-29 12:30
> **方法论**：RICE + MoSCoW + WSJF + 业务自评 4 维度
> **依据**：`docs/ITERATION_PLAN_20260623.md`（6 天前）+ 2026-06-29 真实盘点（pytest 424 用例、29 US/196 AC、daily 端到端跑通）
> **目标版本**：v3.0（v2.0-final 之上增量）

---

## 0. 真实基线（2026-06-29 12:30 复盘）

| 指标 | 数字 | 来源 |
|------|-----:|------|
| **模块数** | 14 | `ls src/etf_quant/` |
| **测试文件** | 45 | `find tests -name 'test_*.py'` |
| **测试用例** | **424**（不是 217）| `pytest --collect-only` |
| **测试通过** | **423/424 = 99.76%** | `pytest -q`（1 失败：D-013.3）|
| **文档 .md** | 54 | `find docs -name '*.md'` |
| **Skill** | 6 | `ls skills/` |
| **业务 reports** | 5 | `ls reports/` |
| **US 总数** | 29 | `docs/PRD.json` |
| **AC 总数** | 196（**新统计**）| `docs/PRD.json` 累加 |
| **US passes=true** | 29 (100%) | `docs/PRD.json` |
| **业务自评脚本** | ❌ **不存在** | `find scripts -name 'business_check*'` |
| **daily 端到端可跑** | ✅ | 2026-06-29 12:00 实测 BUY top 5 0.52~0.73 |
| **HEAD** | `0f5097e` | `git log` |

---

## 1. 方法论与评估

### 1.1 评分方法

| 方法 | 出处 | 用途 | 引用 |
|------|------|------|------|
| **RICE** | Intercom 2016（Reach × Impact × Confidence / Effort）| 优先级排序 | Wikipedia "RICE score" |
| **MoSCoW** | Dai Clegg 1994（UK Government）| Must/Should/Could/Won't | Wikipedia "MoSCoW method" |
| **WSJF** | Dean Leffingwell SAFe | Cost of Delay / Job Duration | Scaled Agile Framework |
| **业务自评 4 维度** | SOUL.md 规则 24 | 数据完整性/结果合理性/端到端可跑/文档对得上 | MEMORY.md §3 |
| **6 维度自评** | SOUL.md 规则 7 | 设计/调研/SOP/测试/回归/Git | SOUL.md §二 |

### 1.2 评估总览

| 类别 | 任务数 | 总人天 | 说明 |
|------|------:|------:|------|
| **Must** | 4 | 2.25 | 业务闭环 P0 |
| **Should** | 8 | 9.5 | 业务优化 + 工程债 |
| **Could** | 10 | 16.0 | 锦上添花 |
| **Won't** | 2 | 5.5 | v3.0 不做 |
| **总计** | **24** | **33.25** | v3.0 全部债 |

**RICE 前 5**：A4 (30) > A3 (20) > A2 (16) > A1 (15) > B6/D4 (10)
**WSJF 前 5**：A4 (42) > A3 (32) > A2 (26) > A1 (21) > B1/C1 (13)

---

## 2. 依赖图（DAG）

```
                        ┌─────────────────────────────┐
                        │ Phase 0: 业务自评基础设施     │
                        │  A1: 建 business_check.py   │
                        │  （0.25d 写 + 0.75d 跑分）   │
                        └──────────────┬──────────────┘
                                       │ 必须先有
                                       ↓
        ┌──────────────────────────────┴──────────────────────────────┐
        │                                                              │
        ↓                                                              ↓
┌────────────────────┐                                       ┌─────────────────┐
│ Phase 1: 业务闭环  │                                       │ Phase 1 副线    │
│ A2: 修 D-013.3     │                                       │ A3: 更新 README │
│   (test_run_eval)  │                                       │   (测试数 424)  │
│ 0.5d               │                                       │ 0.25d           │
└─────────┬──────────┘                                       └─────────────────┘
          │
          ↓ 必须先修
┌─────────────────────────┐
│ A4: 验证 4 维度跑通     │
│   （拿到真业务自评 4 维度分）│
│ 0.5d                   │
└─────────┬───────────────┘
          │
          ↓ 有了真分
          ┌───────────────────────────────────────────────┐
          │ Phase 2-3: 业务优化 + 工程债（可并行）         │
          │ B6 / B1 / C1 / C4 / C6 / D1 / D3 / D4         │
          └───────────────────────────────────────────────┘


并行任务（独立，可任何时候做）:
- C4: __init__.py API docstring（1d）
- C6: except 精确化（0.5d）
- D1: decision_snapshot 散户解释（1d）
- D3: 29 因子中文描述全检（1d）
- D4: 钉钉推送模板（0.5d）
- E2: pytest 卡死调查（1d）

不做的（Won't）:
- D5: 量化知识库深度内容
- E1: Theme 4 根仓清理
- B3: D-008 概率三元组（5d 大活，单开 Mission）
- B5: D-011 止盈止损动态化（3d 大活）
```

---

## 3. 短段路线图：1 周交付（v2.1 维护版）

### Phase 0：业务自评基础设施（**1 人天**）

#### Sprint 0.1：建 `scripts/business_check.py`（0.25d 写 + 0.75d 跑分）

| # | 任务 | 内容 | 时间 | 验收 |
|:--:|------|------|:----:|------|
| 0.1.1 | 写脚本骨架 | argparse + 4 维度函数 | 1h | 文件存在 |
| 0.1.2 | 维度 1：数据完整性 | 跑 14 ETF 验证（持仓/池/价格/分数）| 1h | 自动断言 |
| 0.1.3 | 维度 2：结果合理性 | 跑 daily 决策（BUY/HOLD/SELL 比例）| 1h | 自动断言 |
| 0.1.4 | 维度 3：端到端可跑 | pytest + daily + run_eval | 1h | 全绿 |
| 0.1.5 | 维度 4：文档对得上 | README 数字 vs 实测数字 | 0.5h | 自动对比 |

**业务自评输出**（0~25 分 × 4 维度）：
- 数据完整性：14/14 ETF + 价格完整 + 分数计算无 NaN
- 结果合理性：BUY/HOLD/SELL 比例合理（不全部同一档）
- 端到端可跑：pytest 100% + daily 跑通 + run_eval 跑通
- 文档对得上：README 数字 = 实测数字

**Sprint 0.1 验收**：
- [ ] `python scripts/business_check.py` 跑出真分
- [ ] 4 维度全打印
- [ ] 总分 ≥80
- [ ] commit + push

---

### Phase 1：业务闭环 P0 债（**1.25 人天**）

#### Sprint 1.1：修 D-013.3 test_run_eval 失败（0.5d）

| # | 任务 | 内容 | 时间 | 验收 |
|:--:|------|------|:----:|------|
| 1.1.1 | 读 `tests/unit/test_run_eval.py:81` | 找 n_etfs_tested=0 根因 | 0.5h | 根因明确 |
| 1.1.2 | 读 `scripts/run_eval.py` 实际实现 | 看为什么返回 0 | 0.5h | 修复点明确 |
| 1.1.3 | 修复（mock 数据/改测试/改实现 三选一）| 选最简 | 1h | pytest 全绿 424/424 |
| 1.1.4 | 跑全量验证 | pytest -q | 0.5h | 无回归 |

**Sprint 1.1 验收**：
- [ ] pytest 424/424 全过
- [ ] `test_run_eval.py::test_eval_returns_summary` 通过
- [ ] commit + push

#### Sprint 1.2：更新 README 数字（0.25d）

| # | 任务 | 内容 | 时间 | 验收 |
|:--:|------|------|:----:|------|
| 1.2.1 | 找 README 中"217"出现处 | grep -n "217" | 0.1h | 位置清单 |
| 1.2.2 | 改为真实数字 424/424 | 替换 | 0.1h | README 改完 |
| 1.2.3 | 加 pytest 验证链接 | 跑一次确认 | 0.1h | 全绿 |

**Sprint 1.2 验收**：
- [ ] README 数字 = 424/424
- [ ] commit + push

#### Sprint 1.3：跑业务自评拿真分（0.5d）

| # | 任务 | 内容 | 时间 | 验收 |
|:--:|------|------|:----:|------|
| 1.3.1 | 跑 `python scripts/business_check.py` | 4 维度同时跑 | 0.5h | 真分出 |
| 1.3.2 | 记录到 `reports/2026-06-29_v3_baseline/SELF_EVAL.md` | 4 维度分 + 阻塞项 | 0.5h | 报告存 |
| 1.3.3 | 不合格项 → 写债 | 列下一轮该修什么 | 0.5h | 债清单 |

**Sprint 1.3 验收**：
- [ ] 真分 ≥80
- [ ] SELF_EVAL.md 入库
- [ ] commit + push

**Phase 1 总计**：1.25 人天（0.5+0.25+0.5）

---

### Phase 2：业务优化 P1 债（**2 人天**）

#### Sprint 2.1：D-012 HOLD 落 snapshot 完整字段（0.5d）

| # | 任务 | 内容 | 时间 | 验收 |
|:--:|------|------|:----:|------|
| 2.1.1 | 读 HOLD 路径代码 | `run_daily.py` HOLD 分支 | 0.5h | 现状明确 |
| 2.1.2 | 补 8 字段 | decision_snapshot | 1h | 全字段落库 |
| 2.1.3 | 测试 | 跑一次 HOLD 决策 | 0.5h | snapshot 落库 |

**Sprint 2.1 验收**：
- [ ] HOLD 时 snapshot 8 字段全
- [ ] commit + push

#### Sprint 2.2：D-013.4 v2 daily cron 09:30 工作日（1d）

| # | 任务 | 内容 | 时间 | 验收 |
|:--:|------|------|:----:|------|
| 2.2.1 | 用 `qwenpaw cron create` 建 cron | 09:30 工作日 | 0.5h | cron 创建 |
| 2.2.2 | 测试（手动触发 + 验证日志）| bash run_and_log.sh daily | 1h | 跑通 |
| 2.2.3 | 加 L326 检查（升级后重检 enabled）| MEMORY 教训 | 0.5h | 文档化 |

**Sprint 2.2 验收**：
- [ ] cron 创建并 enabled
- [ ] 手动触发跑通
- [ ] MEMORY.md 记录 L326
- [ ] commit + push

#### Sprint 2.3：D-009 决策阈值动态化（**2d 大活**，可拆）

| # | 任务 | 内容 | 时间 | 验收 |
|:--:|------|------|:----:|------|
| 2.3.1 | PRD + 设计 | 3 档阈值 vs 动态阈值 | 1h | 设计文档 |
| 2.3.2 | 跑回测对比 4 验证器 | 静态 vs 动态 | 1.5h | 报告 |
| 2.3.3 | 选优 + 改代码 | 改 WeightScheme | 1.5h | 阈值类落地 |
| 2.3.4 | 测试 | daily 跑通 | 1h | 无回归 |

**Sprint 2.3 验收**：
- [ ] 动态阈值类
- [ ] 回测对比报告
- [ ] commit + push

**Phase 2 总计**：2 人天（0.5+1+2=3.5）→ **Phase 2 重排为 3.5d**

---

### 短段总人天

| Phase | 人天 |
|------:|----:|
| Phase 0 | 1.0 |
| Phase 1 | 1.25 |
| Phase 2 | 3.5 |
| **小计** | **5.75 人天** |

按每天 2h 开发节奏 = **3 天**可完成（1 周内完成）

---

## 4. 长段路线图：v3.0 完整版（30 人天 / 6 周）

### Phase 3：工程债（业务依赖时做）

| Sprint | 任务 | 人天 | RICE | 触发条件 |
|:------:|------|:----:|-----:|----------|
| 3.1 | C1: GitHub Actions CI | 1.0 | 8 | Phase 1 后必做 |
| 3.2 | C4: 6 个空 `__init__.py` 补 API | 1.0 | 3 | API 用户需要时 |
| 3.3 | C6: 4 个 except 精确化 | 0.5 | 6 | 任何修改前 |
| 3.4 | E2: pytest 卡死调查 | 1.0 | 1.5 | CI 跑通后做 |

### Phase 4：散户友好（v3.0 用户体验）

| Sprint | 任务 | 人天 | RICE | 触发条件 |
|:------:|------|:----:|-----:|----------|
| 4.1 | D1: decision_snapshot 8 字段散户解释 | 1.0 | 8 | Phase 2 后 |
| 4.2 | D3: 29 因子中文描述全检 | 1.0 | 5 | 任何时候 |
| 4.3 | D4: 钉钉推送模板 | 0.5 | 10 | B1 cron 跑通后 |
| 4.4 | D2: 5 skill 散户视角走查 | 1.5 | 1.67 | v3.0 验收前 |

### Phase 5：业务进阶（v3.0+ 增量）

| Sprint | 任务 | 人天 | RICE | 触发条件 |
|:------:|------|:----:|-----:|----------|
| 5.1 | B6: D-012 HOLD 落 snapshot | 0.5 | 10 | Phase 2 |
| 5.2 | B4: D-010 HOLD 触发细化 | 1.0 | 4 | D-009 后 |
| 5.3 | E4: D-013.5 IC 季度重跑 | 2.0 | 4 | 每季度 |
| 5.4 | C2/C3: Dockerfile + Makefile | 1.0 | 6 | CI 后 |

### Phase 6：v3.0+ 大活（不并发，单 Mission 跑）

| Sprint | 任务 | 人天 | 优先级 | 备注 |
|:------:|------|:----:|:------:|------|
| 6.1 | D-008 概率三元组 | 5 | Could | 架构升级 |
| 6.2 | D-011 止盈止损动态化 | 3 | Could | 持仓管理 |
| 6.3 | D-013.5 IC 巡检自动化 | 2 | Should | 月度自动跑 |

**长段总人天**：~30 人天

---

## 5. 不做的事（明确边界）

按 Shape Up 反模式 + 防止范围蔓延：

1. ❌ **不重写 v1 脚本** — 物理删除完成
2. ❌ **不引入新框架**（FastAPI / Django 等）
3. ❌ **不接 LLM 推理** — 因子逻辑代码化
4. ❌ **不接券商 API** — 用户自行下单
5. ❌ **不做 Theme 4 根仓清理**（E1 Won't）— 用户已下线决策风险高
6. ❌ **不做 Theme 5 pytest 卡死调查**（E2 推到 Phase 3）— 已有单文件跑规避
7. ❌ **不做量化知识库深度内容**（D5 Won't）— 5d 大活，价值低 RICE=1
8. ❌ **不做 4 个未读模块独立跑过**（E3 Could）— 等需要时再跑

---

## 6. 风险与回滚

| 风险 | 等级 | 应对 | 回滚 |
|------|:---:|------|------|
| A1 业务自评脚本跑不出真分 | P1 | 设计时用 4 维度简单断言（不用 IC/IR）| 删脚本，回到文档自评 |
| A2 修 D-013.3 引入回归 | P1 | 跑全量 pytest + daily | revert commit |
| B1 cron 推送重复 | P2 | 加去重 + 幂等检查 | 删 cron |
| C1 CI 跑通后慢 | P2 | 加 --no-cov 提速 | 关 CI |
| D-009 阈值动态化引入过拟合 | P1 | OOS 验证 | 回滚到固定阈值 |
| 路线图方向错 | P0 | 每 Sprint 1 跑 `腐化自检` | 整体回滚到 ITERATION_PLAN_20260623 |

---

## 7. 验收标准（每 Sprint 通用）

按 SOUL.md 规则 1（交付 4 项缺一不可）：

1. ✅ **功能能跑** — pytest + 手动验证
2. ✅ **测试通过** — 至少 1 个新测试 + 全量无回归
3. ✅ **文档更新** — MEMORY.md 或 sprint-review
4. ✅ **无重复问题** — 不重复造轮子

按 SOUL.md 规则 7（6 维度自评 ≥90 优秀）：

| 维度 | 满分 | 目标 |
|------|-----:|-----:|
| 设计文档输出 | 20 | ≥18 |
| 调研参考来源 | 20 | ≥18 |
| 按 SOP Phase 执行 | 20 | ≥18 |
| 单元测试覆盖 | 15 | ≥13 |
| 回归测试通过 | 15 | ≥13 |
| Git 小步提交 | 10 | ≥9 |
| **总计** | **100** | **≥90** |

按 SOUL.md 规则 24（业务自评 4 维度 ≥80）：

| 维度 | 满分 | 目标 |
|------|-----:|-----:|
| 数据完整性 | 25 | ≥20 |
| 结果合理性 | 25 | ≥20 |
| 端到端可跑 | 25 | ≥20 |
| 文档对得上 | 25 | ≥20 |
| **总计** | **100** | **≥80** |

---

## 8. 业界参考（标来源）

| # | 实践 | URL | 用途 |
|---|------|-----|------|
| 1 | RICE Scoring | https://en.wikipedia.org/wiki/RICE_score | 优先级评分 |
| 2 | MoSCoW Method | https://en.wikipedia.org/wiki/MoSCoW_method | Must/Should/Could/Won't |
| 3 | WSJF (SAFe) | https://scaledagileframework.com/wsjf/ | 加权最短作业优先 |
| 4 | OKR | https://en.wikipedia.org/wiki/OKR | 目标与关键结果 |
| 5 | Shape Up | https://basecamp.com/shapeup | 6 周周期 + 冷却期 |
| 6 | DORA Metrics | https://dora.dev/ | 部署效能 4 指标 |
| 7 | SRE Golden Signals | https://sre.google/sre-book/monitoring-distributed-systems/ | 监控 4 信号 |
| 8 | Kirkpatrick Model | https://en.wikipedia.org/wiki/Kirkpatrick_model | 业务自评 4 维度 |
| 9 | 12-Factor App | https://12factor.net/ | 应用 12 要素 |
| 10 | OpenSSF Best Practices | https://bestpractices.coreinfrastructure.org/ | 安全治理 |
| 11 | Atlassian Sprint Retrospective | https://www.atlassian.com/team-playbook/plays/retrospective | 复盘 4 步 |
| 12 | Scrum Guide 2020 §5.3 | https://scrumguides.org/scrum-guide.html#sprint-retrospective | Sprint 复盘 |

---

## 9. 与 ITERATION_PLAN_20260623 的差异

| 项 | ITERATION_PLAN_20260623 | ROADMAP_v3（本文）| 差异原因 |
|----|------------------------|------------------|----------|
| **方法论** | 5 大 Theme（凭直觉）| RICE + MoSCoW + WSJF | 按业界方法 |
| **优先级** | Theme 1~5 顺序固定 | RICE 评分排序 | 业务价值优先 |
| **业务债** | 散落 | 显式 P0/P1/P2 | 业务闭环优先 |
| **工程债** | 主题化（Theme 2/3）| 业务依赖时做 | 业务优先于工程 |
| **时间维度** | 单段（未来 1~2 周）| 短段（1 周）+ 长段（6 周）| 双段可调 |
| **评估** | 9 维度 250 分 | RICE/MoSCoW/WSJF + 6 维自评 + 业务 4 维 | 多维评分 |
| **不做的事** | 7 节"不做事"清单 | 5 节边界 + Won't 任务 | 显式边界 |
| **依赖图** | 无 | DAG | 强制约束 |

---

## 10. 短段执行顺序（**Sprint 0.1 必须先做**）

| 顺序 | Sprint | 估时 | 累计 | 风险 |
|:----:|--------|:----:|:----:|:----:|
| 1 | **Sprint 0.1** 建 business_check.py | 1.0d | 1.0 | 低（独立）|
| 2 | Sprint 1.1 修 D-013.3 | 0.5d | 1.5 | 中（改测试）|
| 3 | Sprint 1.2 更新 README | 0.25d | 1.75 | 极低 |
| 4 | Sprint 1.3 跑业务自评 | 0.5d | 2.25 | 低（有了工具）|
| 5 | Sprint 2.1 D-012 HOLD 落 snap | 0.5d | 2.75 | 低 |
| 6 | Sprint 2.2 cron 09:30 | 1.0d | 3.75 | 中（cron 配错）|
| 7 | Sprint 2.3 D-009 阈值动态化 | 2.0d | 5.75 | **高**（架构改）|

**短段总人天：5.75d**（按每天 2h ≈ 3 天开发 + 1 天测试 = 1 周内）

---

## 11. 立即行动

**下一个 Sprint**（Sprint 0.1）开 Sprint 任务卡：

- [ ] **任务卡 #001**：建 `scripts/business_check.py`
  - **做什么**：4 维度业务自评脚本（数据完整性/结果合理性/端到端可跑/文档对得上）
  - **为什么**：业务自评 4 维度 ≥80 是 Mission 验收的硬性条件（SOUL.md 规则 24）
  - **边界**：只跑 4 维度简单断言，不做 IC/IR 复杂评估
  - **风险**：脚本写错跑不出真分 → 加 try-except + 友好报错
  - **验收**：`python scripts/business_check.py` 输出 4 维度分 + 总分
  - **估时**：1 人天
  - **依赖**：无
  - **SOP**：SOP-02 6 阶段

---

**作者**：福猫管家 🐱
**日期**：2026-06-29 12:30
**版本**：v3.0-roadmap-draft
**状态**：📋 待用户确认
**下一步**：开 Sprint 0.1 任务卡
