# SOP-08: 复盘流程（Review Process）

> **file**: SOP_08_REVIEW.md
> **purpose**: 把"复盘"从动词（口语化）升级为流程（结构化）
> **used_by**: 所有 Sprint/Mission 结束、所有 P0/P1 bug 修复后
> **status**: active
> **created**: 2026-06-28（由 D-013 复盘发现"复盘没 SOP"创建）
> **关联**: SPRINT_REVIEW_TEMPLATE.md / SOUL 规则 6.1（禁止美化）

---

## 一、为什么需要这个 SOP

### 1.1 触发问题（2026-06-28 D-013 复盘发现）

我在 D-013 完成后做"复盘"，但**没按 SPRINT_REVIEW_TEMPLATE.md 8 节**填：
- 没工时统计
- 没对照 v1 教训（L1/L101/L117/L211/L228/L229）
- 没腐化自检
- 工时/计划数据缺失（任务中没建 CHECKPOINT.md）

**结果**：自评 97/100，但只覆盖 8 节中的 5 节 = **真实完成度 62.5%**。

### 1.2 核心原则

> **复盘不是"我感觉做得怎么样"，是"按 8 节填数据"**。

参考业界：
- **Atlassian Sprint Retrospective**（4 步：Set the stage / Gather data / Generate insights / Decide actions）
- **Scrum Guide 2020** §5.3 Sprint Retrospective
- **Spotify Squad Health Check** 模型
- **L91 v1 教训**："看起来 OK"假完成 → 必须按节填

---

## 二、流程概览

```
┌──────────────────────────────────────────────────────────────┐
│  Trigger: Sprint/Mission 结束 或 P0 bug 修复后                 │
│                                                              │
│  Phase 1: 准备（5min）                                       │
│    1. 确认有 CHECKPOINT.md（任务中跟踪工时/计划）              │
│    2. 没有 → 立即补建（用现有 commit log 反推）                │
│                                                              │
│  Phase 2: 按 8 节填（30-60min）                              │
│    1. Sprint 信息                                            │
│    2. 做了什么（US/任务 + commit + 工时）                    │
│    3. 学到了什么（v1 教训映射）                               │
│    4. 对比计划（CHECKPOINT.md）                              │
│    5. 下一步（明确到命令）                                    │
│    6. 新增教训（写入 MEMORY.md）                              │
│    7. 风险（影响下个 Sprint + 分级）                          │
│    8. 工时统计 + 自评分数（4 维度腐化自检）                   │
│                                                              │
│  Phase 3: 提交 + 引用（5min）                                │
│    1. git add + commit + push                                │
│    2. 在 MEMORY.md "最后更新"加日期                           │
│    3. 在 SOUL.md 末尾关联教训（如有 L 编号更新）              │
└──────────────────────────────────────────────────────────────┘
```

---

## 三、8 节填写规则（每节必填，不允许空）

### 3.1 节 1: Sprint 信息

| 字段 | 来源 | 必填？ |
|---|---|:---:|
| Sprint 编号 | 当前 Sprint | ✅ |
| 开始/结束日期 | git log first/last commit | ✅ |
| 计划 US 数 | prd.json 或 CHECKPOINT.md | ✅ |
| 实际 US 数 | git log `feat:` 数量 | ✅ |
| 计划工时 | CHECKPOINT.md（不存在则标注 N/A）| ⚠️ |
| 实际工时 | 节 7 工时统计 | ✅ |

### 3.2 节 2: 做了什么

**每行**：US/任务 | 状态 | commit sha | 工时 | 实际 vs 计划

```markdown
| US | 标题 | 状态 | Commit | 工时 | 实际 vs 计划 |
|----|------|:---:|--------|:---:|:---:|
| D-013 | daily 8 因子综合打分 | ✅ | 181ed93 | 4.5h | 符合 |
```

### 3.3 节 3: 学到了什么（v1 教训映射）

**对照 v1 教训表**（从 MEMORY 顶部抄）：

| v1 教训 | 本 Sprint 是否相关 | 处理方式 |
|---------|:---:|---------|
| L1（不要凭记忆）| ✅ | 节 4 引用 git log 反推 |
| L91（看起来 OK）| ✅ | 节 8 腐化自检强制 |
| L101（多执行源无标识）| ❌ | 不涉及 |
| ... | | |

### 3.4 节 4: 对比计划

**引用 CHECKPOINT.md**（如果不存在则说明"未建"是教训）。

| 任务 | 计划 | 实际 | 偏差 | 原因 |
|------|------|------|------|------|
| P0 修复 | 2h | 1.5h | -0.5h | 一次到位 |
| 3 抽象设计 | 1h | 2h | +1h | 设计 v1 自创根因被用户纠正 |

### 3.5 节 5: 下一步（明确到命令）

```markdown
1. `git checkout -b d013-1` (DMA/FIB 因子化)
2. `cd etf_quant_v2 && /home/qwenpaw/ENV/bin/python3 -m pytest tests/unit/alpha/test_dma.py`
3. `bash scripts/run_and_log.sh daily` 验证
```

**禁止**："接下来做 D-013.1"（不明确）

### 3.6 节 6: 新增教训（写入 MEMORY.md）

| 编号 | 标题 | 引用 |
|------|------|------|
| L328 | 测试要验业务语义 | test_e2e 没断言 score 区分度 |
| L329 | 占位符用 None 而非 0.5 | 占位符污染生产 |
| L330 | 写 AC ≠ 完成 AC | US-020 AC 写"调用 alpha"但实现只 import |

**强制**：新增教训要立刻 commit 到 MEMORY.md，不要"等下再补"。

### 3.7 节 7: 风险（影响下个 Sprint + 分级）

| 风险 | 等级 | 缓解 | 触发条件 |
|------|:---:|------|---------|
| DMA/FIB 未注册 | P0 | D-013.1 因子化 | 8 因子真参与评分 |
| market_mode 漂移 | P0 | D-013.2 排查 | daily 输出稳定 |
| MEMORY 教训分散 | P1 | 升级 memory/lessons/ 目录 | 教训独立搜索 |

### 3.8 节 8: 工时统计 + 自评分数

**工时统计**（按节 2 汇总）：

| 类别 | 计划 | 实际 | 偏差 |
|------|------|------|------|
| 编码 | | | |
| 测试 | | | |
| 文档 | | | |
| 调试 | | | |
| **合计** | | | |

**自评分数**（4 维度腐化自检，按 SOUL 规则 7 + 规则 24）：

| 维度 | 满分 | 实际 | 说明 |
|---|---|---|---|
| 设计文档输出 | 25 | | |
| 测试覆盖 | 25 | | |
| 文档对得上 | 25 | | |
| 业务可跑 | 25 | | |
| **合计** | 100 | | |

---

## 四、复盘触发条件

| 触发事件 | 复盘粒度 | 模板 |
|---|---|---|
| Sprint 结束 | Sprint 级 | SPRINT_REVIEW_TEMPLATE.md |
| Mission 结束 | Mission 级 | SOP_07_MISSION.md（待补 Mission review 模板）|
| P0 bug 修复后 | Bug 级 | SPRINT_REVIEW_TEMPLATE.md 第 1-3 节 |
| 任务超过 4h | 任务级 | DECISIONS.md（任务中持续填）|

---

## 五、反模式（按规则 5 标记）

| 反模式 | 案例（D-013）| 修正 |
|---|---|---|
| 用"我感觉"代替数据 | "我觉得做完了" | 强制填 8 节 |
| 工时凭记忆估算 | "大概 4 小时" | git log `git log --since` 反推 |
| 跳过节 8 自评 | "反正过了" | 腐化自检 4 维度强制 |
| 教训不 commit | "下次再说" | 立刻 commit MEMORY.md |
| 下一步模糊 | "接下来优化" | 必须含具体命令 |

---

## 六、与现有 SOP 的关系

| 现有 SOP | 关系 |
|---|---|
| SOP_02 重构与修复开发 | 上游：开发过程 |
| **SOP_08 复盘流程**（本文件）| **下游：任务结束后** |
| SOP_07 Mission 流程 | Mission 结束后也走 SOP_08 |
| SPRINT_REVIEW_TEMPLATE.md | SOP_08 的具体模板 |

---

## 七、改进追踪

- [ ] Sprint-8 review 按本 SOP 验证
- [ ] Mission review 模板（如需要）合并到 SOP_07
- [ ] 自动化工时统计（git log → CSV）
- [ ] 腐化自检脚本化（避免手工打分）

---

## 八、业界参考（按规则 13）

| 来源 | 借鉴 |
|---|---|
| **Atlassian Sprint Retrospective** | 4 步流程（Set stage → Gather data → Generate insights → Decide actions）|
| **Scrum Guide 2020 §5.3** | 强制 Sprint 末尾复盘 |
| **Spotify Squad Health Check** | 健康指标分级（红/黄/绿）|
| **L91 v1 教训** | "看起来 OK" 假完成必须按节填 |
| **SOUL 规则 6.1** | 禁止美化（工时/数据必须真实）|

---

**最后更新**：2026-06-28（D-013 复盘发现"复盘没 SOP"创建）
**维护人**：福猫管家 🐱
**触发本 SOP 创建的教训**：复盘口语化 → 自评 97/100 但只覆盖 62.5% 节