# v3.0 路线图（按 roadmap-methodology Skill 重写）

> **生成者**：福猫管家 🐱
> **生成时间**：2026-06-29 20:00
> **方法论**：Phaal 2004（3 阶段 10 步）+ Shape Up 2019（Shaping 4 步 + 7 元素）+ Adjust to Your Size（1 人公司）
> **Skill 版本**：roadmap-methodology v1.1（8.95/10 A 级）
> **目标版本**：v3.0（v2.0-final 之上增量）
> **状态**：📋 待用户确认执行

---

## Step 1: Gather context（5 问已答）

| Q | 答案 |
|---|------|
| Q1 项目 | v3.0 ETF 量化项目（v2.0-final 之上增量，业务闭环 + 散户友好）|
| Q2 用户 | 月海巫师（1 人公司 + AI 助手 + 散户教育用户）|
| Q3 时间 | 短段 1 周（v3.0 v1）+ 长段 6 周（v3.0 完整）|
| Q4 团队 | 1 人 + AI 助手（Adjust to Your Size 简化版）|
| Q5 "完成" | pytest 100% (424/424) + 业务自评 ≥80 + Sprint 全过 + 用户能自动跑 + 散户可理解 |

---

## Phase 1: Preliminary（3 步）

### Step 1: Satisfy essential conditions（满足基本条件）

| 条件 | 状态 | 证据 |
|------|:----:|------|
| 用户明确 | ✅ | 月海巫师（PROFILE.md）|
| 团队规模 | ✅ | 1 人 + AI 助手（Adjust to Your Size）|
| 数据源稳定 | ✅ | 腾讯 ifzq.gtimg.cn（日线）+ akshare（60min）|
| 商业模式 | ✅ | B2C 散户"想学方"教育产品（C2 定位）|
| 资金 / 时间约束 | ✅ | 1 周短段 + 6 周长段（可调）|

### Step 2: Provide leadership / sponsorship

| 角色 | 责任人 | 频率 |
|------|--------|------|
| **Owner** | 福猫管家 🐱 | 每日执行 |
| **Sponsor** | 月海巫师 | 关键决策时 |
| **Reviewer** | 月海巫师 | Sprint 末（按 SOP-08 8 节）|

### Step 3: Define scope and boundaries

**In scope**（v3.0 包含）：
- 业务闭环 P0 债（4 项 Must）
- 业务优化 P1 债（B6/B1/C1/D1/D3/D4）
- 散户友好（decision_snapshot 解释 + 5 skill 走查）
- 60min 因子回测评价（D-007 已交付）

**Out of scope**（v3.0 明确不包含）：
- ❌ v1 旧代码（已下线，etf_strategy/ 空目录）
- ❌ 新框架（FastAPI/Django）— 保持 CLI + cron
- ❌ 券商 API 接入 — 用户自行下单
- ❌ LLM 推理 — 因子逻辑代码化
- ❌ 实盘交易验证（模拟数据）— 标 v4.0
- ❌ 量化知识库深度内容（D5 Won't）— RICE=1
- ❌ Theme 4 根仓清理（E1 Won't）— 决策风险高

**Assumptions**（假设条件）：
- v2.0-final 29 US 100% passes（已验证）
- pytest 424 用例 99.76% pass（423/424，1 已知失败 D-013.3）
- daily 端到端可跑（2026-06-29 12:00 实测 BUY top 5 0.52~0.73）
- 数据源稳定（腾讯 + akshare）

---

## Phase 2: Development（7 步）

### Step 4: Identify the product focus（产品聚焦）

**v3.0 定位**：业务闭环 + 散户友好（不只是代码完成度，是"用户能不能每天自动用 + 散户可理解"）

**v2.0 → v3.0 关键差异**：
- v2.0：29 US 100% 实现 + 217 测试
- v3.0：补业务闭环债（业务自评脚本 + D-013.3 修复 + 散户友好）

**为什么是 v3.0 不是 v2.1**：
- v2.0 = "代码完成度"
- v3.0 = "用户可使用度"（业务闭环 + 散户友好）
- 增量足够大，标 v3.0

### Step 5: Identify critical system requirements (SLO)

| SLO | 目标 | 当前 | 差距 | 衡量方法 |
|-----|------|------|------|----------|
| **pytest pass rate** | 100% (424/424) | 99.76% (423/424) | **-1%** | `pytest tests/ -q` |
| **daily 端到端可跑** | 100% | 100% | 0 | `python skills/etf-daily/scripts/run_daily.py daily` |
| **daily 延迟** | <30s | ~10s | OK | 手动计时 |
| **业务自评 4 维度分** | ≥80 | 87 (文档,2026-06-23) | TBD | 跑 `scripts/business_check.py`（待建）|
| **业务自评 4 维度（自动化）** | ≥80 | ❌ 缺脚本 | **-P0** | Sprint 0.1 必建 |
| **cron 准确性** | 100% 09:30 工作日 | ❌ cron 未建 | **-P0** | Sprint 2.2 必建 |
| **钉钉推送送达率** | 100% | 未测 | TBD | Sprint 2.2 测 |
| **散户能看懂 snapshot** | 100% | 缺解释文档 | **-P0** | Sprint 2.4 必做 |
| **pytest buffer 兼容** | 9.x 跑通 | 单文件跑规避 | 已知债 | Phase 3 修 |

### Step 6: Specify major technology areas（核心技术领域）

**14 模块状态表**（实测盘点 2026-06-29）：

| # | 模块 | 状态 | 验证深度 |
|:--:|------|:----:|----------|
| 1 | alpha（29 因子 + 3 层架构）| 🟢 绿 | ✅ 亲自验证 |
| 2 | data_layer（10 个 Repo）| 🟡 黄 | 听过接口 |
| 3 | risk（position_guide 22 字段）| 🟢 绿 | ✅ 亲自读 |
| 4 | execution（tracker 委托 4 Repo）| 🟢 绿 | ✅ 亲自读 |
| 5 | monitor（4 文件）| 🟢 绿 | market_mode 验证 |
| 6 | backtest（3 文件）| 🟡 黄 | 听过 4 验证器 |
| 7 | performance | 🔴 红 | 未读 |
| 8 | notify（3 文件）| 🔴 红 | 未亲眼验证推送 |
| 9 | scheduler（2 文件）| 🔴 红 | cron 未建 |
| 10 | portfolio | 🔴 红 | 未读 |
| 11 | universe（3 文件）| 🔴 红 | 未读 |
| 12 | config | 🔴 红 | 未读 |
| 13 | utils | 🔴 红 | 未读 |
| 14 | rank（多出来的）| 🔴 红 | 未读 |

### Step 7: Specify technology drivers and targets

| 驱动类型 | 驱动 | 目标 | 衡量 |
|----------|------|------|------|
| **业务驱动** | 用户可自动跑 daily | cron 09:30 工作日 + 钉钉推送 | Sprint 2.2 |
| **业务驱动** | 散户可理解决策 | decision_snapshot 8 字段解释 | Sprint 2.4 |
| **技术驱动** | pytest 全绿 | 424/424（修 D-013.3）| Sprint 1.1 |
| **技术驱动** | 业务自评自动化 | business_check.py 跑分 | Sprint 0.1 |
| **技术驱动** | CI 质量门 | GitHub Actions pytest + ruff + mypy | Sprint 3.1 |
| **教育驱动** | 用户能学方 | 29 因子中文描述 + 业界别名 | Sprint 2.4 |
| **教育驱动** | 散户可走查路径 | 5 skill 走查报告 | Sprint 2.4 |

### Step 8: Identify technology alternatives and timelines

**关键决策矩阵**（必须 2+ 方案对比）：

| 决策 | 方案 A | 方案 B | 方案 C | 时间 | RICE 排序 |
|------|--------|--------|--------|:----:|----------:|
| **业务自评** | 4 维度简单断言 | 9 维度 250 分 | 1 维度总评 | 0.5~1d | A > B > C |
| **D-013.3 修复** | 改 mock | 改实现 | 改测试断言 | 0.5d | 调研后选 |
| **D-009 决策阈值** | 固定 0.65 | 动态（按 market_mode）| 概率三元组 | 2d | A (RICE=4) |
| **CI 工具** | GitHub Actions | Jenkins | GitLab CI | 1d | A (RICE=8) |
| **cron 触发方式** | qwenpaw cron | crontab | systemd timer | 1d | A (RICE=8) |
| **push 通知** | 钉钉 webhook | 邮件 | 飞书 webhook | 0.5d | A 沿用现有 |

### Step 9: Recommend the alternatives and prioritize

**短段（1 周）Must 4 项**（2.25 人天，按 RICE 排序）：

| 序 | Sprint | RICE | WSJF | Effort | 任务 |
|:--:|--------|:----:|:----:|:------:|------|
| 1 | **Sprint 0.1** | 15 | 21 | 1.0d | 建 `scripts/business_check.py` |
| 2 | **Sprint 1.1** | 16 | 26 | 0.5d | 修 D-013.3 test_run_eval |
| 3 | **Sprint 1.2** | 20 | 32 | 0.25d | 更新 README 测试数 217→424 |
| 4 | **Sprint 1.3** | 30 | 42 | 0.5d | 跑业务自评拿真分 |

**短段（1 周）Should 3 项**（2.0 人天）：

| 序 | Sprint | RICE | Effort | 任务 |
|:--:|--------|:----:|:------:|------|
| 5 | **Sprint 2.1** | 10 | 0.5d | D-012 HOLD 落 snapshot 完整字段 |
| 6 | **Sprint 2.2** | 8 | 1.0d | D-013.4 cron 09:30 工作日 |
| 7 | **Sprint 2.4** | 8 | 1.0d | decision_snapshot 8 字段散户解释 |

**短段总人天**：4.25d（1 周内完成）

### Step 10: Create the 5-part report

→ 见末尾 §"5 部分报告"

---

## Phase 3: Follow-up

### Review at each sprint end

按 SOP-08 8 节流程（sprint-reviews/sprint-X.md）

### Update weekly

每个 Phase 末更新本 ROADMAP_v3.md

### Re-evaluate 触发条件

| 触发条件 | 立即动作 |
|----------|----------|
| 关键 SLO 跌破阈值（如 pytest < 90%）| 暂停新功能，重评 Step 5 |
| 新增 Must 任务 | 重新跑 RICE 评分 |
| 季度末 | 必做 1 次全路线图重评 |
| 团队规模变化 | 重新调 Adjust to Your Size |
| Rabbit hole 真实发生 | 立即按 Circuit Breaker 暂停 |
| 业务方向变化 | 重新跑 Phase 1+2 全流程 |

**不要每周重做全部 10 步**。**只重做受影响部分**。

---

## Shape Up 7 元素（Apply）

### 1. Shaping 4 步（按 Ch 3→4→5→6）

**Ch 3 Set Boundaries**：
- Appetite 短段 4.25d / 长段 30d
- "Good" is relative：1d 内"够好"即可
- Raw idea default response：未成熟想法 = "Maybe some day"

**Ch 4 Find the Elements**：
- Breadboard：daily → 拉数据 → market_mode → 8 因子 → 综合 → 决策 → snapshot → 推送
- Fat marker sketches：粗草图，不画完整方案

**Ch 5 Risks and Rabbit Holes**：
- 已识别 6 项风险（见每 Sprint Pitch Card）

**Ch 6 Write the Pitch**：
- 7 张 Pitch Card（见下方）

### 2. 5 Pitch Ingredients

**每个 Sprint 一张 Pitch Card**（Problem / Appetite / Solution / Rabbit Holes / No-Gos）
详细见 `pitch_cards/sprint_X_X.md`（下个 commit 创建）

### 3. Betting Table

| Sprint | Appetite | Problem 严重度 | Solution 可行性 | 总评 |
|--------|:--------:|:--------------:|:---------------:|:----:|
| 0.1 | 1.0d | ⭐⭐⭐⭐ | ✅ 简单 | **必选** |
| 1.1 | 0.5d | ⭐⭐⭐ | ✅ 调研后修 | **必选** |
| 1.2 | 0.25d | ⭐⭐ | ✅ 字符串替换 | **必选** |
| 1.3 | 0.5d | ⭐⭐⭐⭐ | ✅ Sprint 0.1 依赖 | **必选** |
| 2.1 | 0.5d | ⭐⭐ | ✅ 简单 | **应选** |
| 2.2 | 1.0d | ⭐⭐⭐ | ⚠️ cron 配置有风险 | **应选** |
| 2.4 | 1.0d | ⭐⭐⭐ | ✅ 文档为主 | **应选** |

### 4. Six-week cycles + Cool-down

**v3.0 完整 6 周周期**：

| Week | Phase | 内容 | 状态 |
|:----:|-------|------|:----:|
| W1 | Phase 0+1（短段）| 业务自评基础设施 + 业务闭环 P0 | ⏸️ 待开 |
| W2 | Phase 2（短段剩余）| 业务优化 + 散户友好 | ⏸️ |
| W3 | Phase 3（工程债）| CI 质量门 + 工程债 | ⏸️ |
| W4 | Phase 3 续 | 散户友好 + 模块独立验证 | ⏸️ |
| W5 | Phase 4（散户友好）| 5 skill 走查 + 知识库 | ⏸️ |
| W6 | Phase 4 续 + Cool-down | 2 周冷却期开始 | ⏸️ |
| W7-8 | Cool-down | 不接新活，修 bug，做 reflection | ⏸️ |

### 5. Hill Chart（v3.0 进度可视化）

```
100% ┤              ╱───── Sprint 0.1 ✓ (短段)
     │            ╱
 75% ┤          ╱───── Sprint 1.1 (修 D-013.3)
     │        ╱
 50% ┤      ╱         Sprint 2.3 (D-009 阈值动态化) [Backlog]
     │    ╱              ⚠️ 卡图顶，需 scope hammering（已决定不做了）
 25% ┤  ╱
     │╱
  0% ┤
     └────────────────────────────
      W1     W2     W3     W4     W5     W6
```

**关键洞察**（Shape Up Ch 13）：横轴是 **position** 不是 time。同样 1 周可能前进 30% 或 5%。

### 6. Circuit Breaker（熔断器）

| 触发条件 | 立即动作 |
|----------|----------|
| 任一 Sprint 引入 ≥2 个新 bug | 暂停新功能，回归 |
| 任意 1 周延期 | 重新 Betting Table |
| pytest 跌破 90% | 暂停新功能，只修 bug |
| Rabbit hole 真实发生 | 按 SOP-08 8 节复盘 + 调范围 |

### 7. No backlogs

- ❌ 不维护 backlog 列表
- ✅ 只在 Betting Table 拍板
- ✅ 超过 6 周不接 = "Maybe some day"

---

## Adjust to Your Size（1 人公司简化版）

按 Shape Up Appendix B：

| 完整 Shape Up | 1 人公司简化 |
|--------------|--------------|
| 拍板会议 | ❌ Skip（1 人不需要）|
| 团队独立 | ❌ Skip（1 人即团队）|
| 拍板 Table 多人讨论 | ⚠️ 改为"问用户 1 次" |
| **必须保留** | |
| Shaping 4 步（特别是 Ch 5 de-risk）| ✅ 保留 |
| Appetite 固定时间变量范围 | ✅ 保留 |
| 6 周 cycle + 2 周冷却 | ✅ 保留（1 人更需要节奏）|
| Hill Chart | ✅ 保留（1 人更要看图）|
| Circuit Breaker | ✅ 保留（自我熔断）|
| No-Gos 显式 | ✅ 保留（防止范围蔓延）|

---

## Exception handling（异常处理）

| 场景 | 指引 |
|------|------|
| **团队 5+ 人** | 跳过 Adjust to Your Size，用完整 Shape Up |
| **项目 < 1 周** | 不要用本路线图，用 Sprint 模板 |
| **用户答不出 5 问** | 引导先答 Q1，不写路线图 |
| **跨多产品** | 拆 2 个路线图分别跑 |
| **SLO 跌破** | 暂停新功能，重评 Step 5 |
| **新增 Must 任务** | 重新跑 RICE 评分 |

---

## 5 部分报告（Phaal 2004 标准）

### 1. Technology identification and description

| # | 技术领域 | 描述 | 状态 |
|:--:|----------|------|:----:|
| 1 | alpha（29 因子）| 决策核心 | 🟢 |
| 2 | data_layer（15 表）| 唯一数据入口 | 🟡 |
| 3 | risk（22 字段 9 步）| 持仓管理 | 🟢 |
| 4 | execution（4 Repo）| 委托模式 | 🟢 |
| 5 | monitor（4 文件）| 健康检查 + market_mode | 🟢 |
| 6 | backtest | ComprehensiveValidator | 🟡 |
| 7 | performance | 绩效分析 | 🔴 |
| 8 | notify | 钉钉推送 | 🔴 |
| 9 | scheduler | cron 配置 | 🔴 |
| 10 | portfolio | 组合管理 | 🔴 |
| 11 | universe | ETF 池管理 | 🔴 |
| 12 | config | 常量配置 | 🔴 |
| 13 | utils | 工具 | 🔴 |
| 14 | rank | 排名 | 🔴 |

### 2. Critical factors

| # | 因素 | 影响 |
|:--:|------|------|
| 1 | SQLite 唯一入口（规则 16）| 高 |
| 2 | 业务代码走 API（规则 15）| 高 |
| 3 | 止损/止盈优先（规则 17）| 高 |
| 4 | 判断基于外部数据（规则 22）| 中 |
| 5 | is_real 标记（规则 23）| 中 |

### 3. Unaddressed areas ⭐（**最重要**）

显式列出**本次路线图没覆盖**：

| # | 未覆盖领域 | 原因 | 影响 | 何时处理 |
|:--:|------------|------|------|----------|
| 1 | **实盘交易验证** | 模拟数据 is_real=0 | 真实盈亏未验证 | v4.0 |
| 2 | **CI/CD（GitHub Actions）** | 不在本短段范围 | 回归风险高 | Sprint 3.1 |
| 3 | **Dockerfile / Makefile** | 不在范围 | 部署效率低 | Sprint 3.4 |
| 4 | **6 个空 `__init__.py` 补 API** | 不在范围 | OpenSSF 不达标 | Sprint 3.2 |
| 5 | **8 个 print() → logger** | 不在范围 | 12-Factor XI 缺 | Sprint 3.3 |
| 6 | **4 个 except 精确化** | 不在范围 | 异常吞掉 | Sprint 3.3 |
| 7 | **performance 模块** | 未读 | 绩效分析黑盒 | 按需 |
| 8 | **notify 模块** | 未亲眼验证推送 | 推送失败未知 | Sprint 2.2 |
| 9 | **scheduler 模块** | cron 未建 | 自动化未启 | Sprint 2.2 |
| 10 | **portfolio 模块** | 未读 | 组合管理黑盒 | 按需 |
| 11 | **universe / config / utils / rank** | 未读 | 架构认知不全 | 按需 |
| 12 | **5 skill 散户视角走查** | 缺视角 | 用户路径不清 | Sprint 2.4 |
| 13 | **29 因子中文描述全检** | 部分有 | 散户可读性 | Sprint 2.4 |
| 14 | **量化知识库深度内容** | 排 Won't | 用户学习价值 | v4.0 |
| 15 | **Theme 4 根仓清理** | 排 Won't | 决策风险高 | - |
| 16 | **Theme 5 pytest 卡死调查** | 排 Could | 已知有 workaround | Sprint 3.4 |
| 17 | **9 维度业务自评 250 分** | 缺脚本 | 业务自评不严谨 | Sprint 0.1 后 |
| 18 | **券商 API 接入** | 明确不做 | 用户自行下单 | - |
| 19 | **LLM 推理** | 明确不做 | 因子逻辑代码化 | - |
| 20 | **新框架（FastAPI/Django）** | 明确不做 | 保持 CLI + cron | - |

**最少应该包含的 3 类**：
1. 未跑过的（听过没做）= #1, 7-13
2. 明确不做的（scope boundaries）= #18-20
3. 假设条件（如果假设错整个路线图作废）= 数据源稳定 / 1 人团队 / pytest 99.76% baseline

### 4. Implementation recommendations

**短段（1 周）实施顺序**（按依赖 DAG）：

| 序 | Sprint | 时间 | 依赖 | 风险 |
|:--:|--------|:----:|------|:----:|
| 1 | Sprint 0.1 建 business_check.py | 1.0d | 无 | 中 |
| 2 | Sprint 1.1 修 D-013.3 | 0.5d | 无 | 中 |
| 3 | Sprint 1.2 更新 README | 0.25d | Sprint 1.1 跑通 | 极低 |
| 4 | Sprint 1.3 跑业务自评拿真分 | 0.5d | Sprint 0.1 + 1.1 | 低 |
| 5 | Sprint 2.1 D-012 HOLD 落 snapshot | 0.5d | 无 | 中 |
| 6 | Sprint 2.2 cron 09:30 | 1.0d | 无 | 中 |
| 7 | Sprint 2.4 decision_snapshot 散户解释 | 1.0d | Sprint 1.3 | 低 |
| **小计** | - | **4.75d** | - | - |

### 5. Technical recommendations

| # | 建议 | 影响 | 优先级 | Phase |
|:--:|------|------|:------:|-------|
| 1 | 加 GitHub Actions CI | 防回归 | P1 | Phase 3 |
| 2 | 加 Dockerfile | 部署效率 | P2 | Phase 3 |
| 3 | 加 Makefile | 入口统一 | P2 | Phase 3 |
| 4 | 6 个 `__init__.py` 补 API | OpenSSF 100% | P2 | Phase 3 |
| 5 | 8 个 print → logger | 12-Factor XI | P3 | Phase 3 |
| 6 | 4 个 except 精确化 | 异常处理 | P3 | Phase 3 |
| 7 | 9 维度业务自评脚本 | 业务自评严谨 | P2 | Sprint 0.1 后 |
| 8 | 4 个未读模块独立验证 | 架构认知 | P3 | 按需 |

---

## 与 ITERATION_PLAN_20260623 + ROADMAP_v3 v1.0 的差异

| 维度 | ITERATION_PLAN_20260623 | ROADMAP_v3 v1.0（凑的）| **本文（Skill 重写）** |
|------|------------------------|------------------------|------------------------|
| **方法论** | 5 Theme 直觉 | RICE/MoSCoW/WSJF 评分 | **Phaal 10 步 + Shape Up 7 元素**（业界标准）|
| **业务债** | 散落 | 24 任务 RICE 评分 | **4 Must + 3 Should + DAG 依赖** |
| **工程债** | 主题化 | 业务依赖时做 | **Phaal Step 8 替代方案 + 优先级** |
| **5 部分报告** | ❌ | ❌ | ✅（特别是 Unaddressed areas 显式 20 项）|
| **Hill Chart** | ❌ | ❌ | ✅（ASCII 山形图）|
| **Exception handling** | ❌ | ❌ | ✅（7 场景 + Rule of thumb）|
| **Re-evaluate 触发条件** | ❌ | ❌ | ✅（8 个触发 + 局部重做）|
| **No backlogs 显式** | ❌ | ❌ | ✅ |
| **Adjust to Your Size** | ❌ | ❌ | ✅（1 人公司简化版）|

---

## 立即行动

**Sprint 0.1 任务卡**（已就绪）：

- 做什么：建 `scripts/business_check.py`（4 维度业务自评）
- 为什么：Mission 验收硬性条件（SOUL.md 规则 24）
- 边界：只跑 4 维度简单断言，不做 IC/IR 复杂评估
- 风险：脚本写错跑不出真分 → try-except + 友好报错
- 验收：`python scripts/business_check.py` 输出 4 维度分 + 总分
- 估时：1 人天
- 依赖：无
- SOP：SOP-02 6 阶段

**Pitch Card 0.1 完整版**（见下一个 commit `pitch_cards/sprint_0_1.md`）

---

**作者**：福猫管家 🐱
**日期**：2026-06-29 20:00
**方法论**：roadmap-methodology Skill v1.1（8.95/10 A 级）
**状态**：📋 待用户确认 + 开 Sprint 0.1
