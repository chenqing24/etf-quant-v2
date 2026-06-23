# 教学框架（Bloom 6 层 + Kirkpatrick 4 层 + Fogg B=MAT）

> **版本**：v2.0
> **日期**：2026-06-23
> **适用**：etf-quant-decision skill + 所有量化教学
> **Mission**: mission-20260623-072239

---

## 一、3 大教学理论

### 1.1 Bloom's Taxonomy（布鲁姆分类学，1956）

> **来源**：[en.wikipedia.org/wiki/Bloom%27s_taxonomy](https://en.wikipedia.org/wiki/Bloom%27s_taxonomy)
> **作者**：Benjamin Bloom（教育心理学家）
> **地位**：教育界 70 年标准，Coursera/Khan Academy 都用

| 层 | 名称 | 含义 | 验证方法 | 量化教学应用 |
|---|------|------|----------|------------|
| L1 | **Remember** | 记忆 | 复述 | 复述 27 因子 5 大类 |
| L2 | **Understand** | 理解 | 用比喻解释 | 给小白讲 7 因子 vs 27 因子 |
| L3 | **Apply** | **应用** | **真跑命令** | 跑通 daily 不报错 |
| L4 | **Analyze** | 分析 | 给出 3 个理由 | 解释为什么买/卖 |
| L5 | **Evaluate** | 评价 | 打分 + 理由 | 评估策略好坏 |
| L6 | **Create** | 创造 | 设计新东西 | 加 1 个新因子 |

**关键约束**：
- 6 层**逐层递进**（L3 必须 L1+L2 过关才能学）
- **L3 Apply 是关键门槛**——不实跑不算学

### 1.2 Kirkpatrick Model（柯氏四级评估，1959）

> **来源**：[en.wikipedia.org/wiki/Kirkpatrick_model](https://en.wikipedia.org/wiki/Kirkpatrick_model)
> **作者**：Donald Kirkpatrick（培训专家）
> **地位**：70% 500 强企业在用

| Level | 名称 | 含义 | 我们对应 |
|-------|------|------|---------|
| L1 | **Reaction** | 反应（觉得有用吗）| 学完打分 1-10 |
| L2 | **Learning** | 学习（学到啥）| 复述 27 因子 |
| L3 | **Behavior** | **行为变化**（真用没用）| **真用 1 次 daily** |
| L4 | **Results** | 业务结果 | 1 月后看收益 |

**关键约束**：
- **L3 Behavior 是真用**（不是"我觉得我会"）
- L4 Results 最难衡量（投资是长期事）

### 1.3 Fogg Behavior Model（福格行为模型，2009）

> **来源**：[en.wikipedia.org/wiki/Fogg_behavior_model](https://en.wikipedia.org/wiki/Fogg_behavior_model)
> **作者**：BJ Fogg（斯坦福行为科学家）
> **公式**：**B（行为）= M（动机）+ A（能力）+ T（触发器）**

| 元素 | 含义 | 真人痛点 | 我们的方案 |
|------|------|---------|----------|
| **Motivation 动机** | 想不想做 | 不知道能赚多少 | 展示"我能赚多少"举例 |
| **Ability 能力** | 能不能做 | 跑命令**报错就放弃** | 5 分钟跑起来（降低门槛）|
| **Trigger 触发器** | 什么时候做 | 不知道"什么时候用" | 决策点导航（mermaid）|

**关键洞察**：
- **能力不足，动机再强也不行动**
- 真人跑命令报错就放弃 = 能力问题（不是动机问题）
- **改造重点 = 提升能力**（不是加鸡汤）

---

## 二、3 大理论的整合（量化教学）

### 2.1 4 周学习路径（整合 Bloom + Kirkpatrick）

| 周 | Bloom 层 | Kirkpatrick | 任务 | 验收 |
|---|---------|------------|------|------|
| 第 1 周 | L1+L2+L3 Apply | L2 Learning | 跑通 daily | 命令不报错 |
| 第 2 周 | L3 Apply | L2 Learning | 跑通 validate | 回测有结果 |
| 第 4 周 | L3 Behavior | **L3 Behavior** | **实盘 1 次** | 真买/卖 1 单 |
| 第 8 周 | L5 Evaluate | L4 Results | 复盘 | 收益 vs 基准 |

**关键约束**：
- **L3 Behavior 必须真用 1 次**（哪怕 1000 元）
- 没实盘 = 整个学习路径失败

### 2.2 Fogg B=MAT 在 SKILL.md 中的应用

| 元素 | 在 SKILL.md 的体现 |
|------|-------------------|
| **Motivation 动机** | "我能赚多少"举例、风险评分、历史收益曲线 |
| **Ability 能力** | 5 分钟跑起来、6 步流程、错误 FAQ |
| **Trigger 触发器** | 决策点导航（mermaid 图）|

---

## 三、为什么 3 理论选这 3 个？

| 候选理论 | 选/不选 | 原因 |
|---------|--------|------|
| **Bloom** | ✅ 选 | 认知层覆盖完整（L1-L6），教育界金标准 |
| **Kirkpatrick** | ✅ 选 | 培训效果评估完整（L1-L4），企业金标准 |
| **Fogg B=MAT** | ✅ 选 | 行为科学，可操作性强（3 元素）|
| ADDIE（教学设计）| ❌ 不选 | 太重（5 阶段），不适合 SKILL 这种轻量教学 |
| Mastery Learning | ❌ 不选 | 单一维度（掌握度），不如 Bloom 全面 |
| Kolb 体验学习圈 | ❌ 不选 | 偏哲学（4 阶段循环），不如 Fogg 可操作 |

---

## 四、3 理论的检查清单

### 4.1 Bloom 检查清单

- [ ] 每个教学目标都标注 Bloom 层
- [ ] **L3 Apply 必须真跑成功**才算通过
- [ ] L1/L2 用"复述 + 比喻"验证
- [ ] L4-L6 在 4 周后开始

### 4.2 Kirkpatrick 检查清单

- [ ] L1 Reaction：学完打分 1-10
- [ ] L2 Learning：能复述核心概念
- [ ] **L3 Behavior：真用 1 次**（最关键）
- [ ] L4 Results：1 月后看（长期，不强求）

### 4.3 Fogg B=MAT 检查清单

- [ ] **M 动机**：SKILL.md 里有"动机"段落吗？
- [ ] **A 能力**：5 分钟跑起来能跑通吗？
- [ ] **T 触发器**：决策点导航清晰吗？

---

## 五、etf-quant-decision 教学实例

### 5.1 第 1 周教学目标（BLOOM L1-L3）

```yaml
目标: 跑通 daily
Bloom: L1 Remember + L2 Understand + L3 Apply
Kirkpatrick: L2 Learning
Fogg: A 能力（降低门槛）

任务:
  L1: 复述"5 分钟跑起来"4 步
  L2: 用比喻解释"5 分钟跑起来 = 给手机装新 App"
  L3: 真跑 daily 命令，看到输出

验收:
  - 命令不报错 ✅
  - 输出符合预期 ✅
  - 能解释每步 ✅
```

### 5.2 第 4 周教学目标（BLOOM L3 BEHAVIOR）

```yaml
目标: 真用 1 次
Bloom: L3 Apply + L3 Behavior
Kirkpatrick: L3 Behavior ⭐
Fogg: M 动机 + A 能力 + T 触发器

任务:
  - 用 SKILL 输出**真的**下 1 单
  - 资金：建议 1000 元（最小可承受损失）
  - 记录：为什么买/卖/不动

验收:
  - 有 1 条实盘记录（哪怕 1000 元）✅
  - 记录"为什么" ✅
  - 5 大类 27 因子能复述 ✅
```

---

## 六、常见误区

### ❌ 误区 1：只看文档 = 学
```
"我读了 SKILL.md，我学会了"
❌ 错。L1 Remember ≠ L3 Apply
✅ 真跑 = L3 Apply
```

### ❌ 误区 2：理解 = 会用
```
"我理解了 27 因子怎么算的，我会用了"
❌ 错。L2 Understand ≠ L3 Apply
✅ 真买/卖 1 次 = L3 Behavior
```

### ❌ 误区 3：1 次 = 永远会
```
"我跑过 1 次 daily，我以后都会了"
❌ 错。1 次 = L3 Behavior 通过
✅ 持续用 = L4 Results（1 月后看）
```

---

## 七、参考来源

| # | 理论 | 链接 | 备注 |
|---|------|------|------|
| 1 | Bloom's Taxonomy | [en.wikipedia.org](https://en.wikipedia.org/wiki/Bloom%27s_taxonomy) | 教育界 70 年标准 |
| 2 | Kirkpatrick Model | [en.wikipedia.org](https://en.wikipedia.org/wiki/Kirkpatrick_model) | 70% 500 强企业在用 |
| 3 | Fogg Behavior Model | [en.wikipedia.org](https://en.wikipedia.org/wiki/Fogg_behavior_model) | Stanford BJ Fogg |
| 4 | Formative Assessment | [en.wikipedia.org](https://en.wikipedia.org/wiki/Formative_assessment) | 反馈用，不打分用 |
| 5 | Twelve-Factor App | [12factor.net](https://12factor.net/) | 第 2 条依赖声明 |

---

**最后更新**: 2026-06-23
**作者**: 福猫管家 🐱
**Mission**: mission-20260623-072239
