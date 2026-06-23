# SKILL User Guide（Divio 4 类文档整合）

> **版本**：v2.0
> **日期**：2026-06-23
> **依据**：[Divio Documentation Guide](https://docs.divio.com/documentation-guide/)
> **Mission**: mission-20260623-072239

---

## 一、为什么需要 4 类文档？

技术文档的核心问题是**混淆 4 种不同目的**。一个文档同时讲"怎么用 + 为什么这么设计 + 完整 API + 新手教程" → 读者懵。

Divio 提出 **4 类文档互相不可替代**：

| 类型 | 目的 | 谁来读 | 时机 |
|------|------|-------|------|
| **Tutorial**（教程）| 0→1 入门，**纯小白** | 新用户 | 第一次用 |
| **How-to Guide**（操作指南）| 解决具体问题 | 已上手的人 | 遇到问题 |
| **Reference**（参考手册）| 查 API/参数 | 熟手 | 写代码时 |
| **Explanation**（原理说明）| 讲为什么 | 想深入的人 | 好奇时 |

**业界采用**：Read the Docs、GitBook、MkDocs、Swagger 都参考。

---

## 二、etf-quant-decision SKILL.md 怎么应用 4 类

### 2.1 Tutorial（5 分钟跑起来）
- 位置：`SKILL.md §🚀 5 分钟跑起来`
- 读者：第一次用的小白
- 目标：5 分钟跑通 daily
- 关键：每步可复制粘贴，**不解释为什么**

### 2.2 How-to（故障排查）
- 位置：`SKILL.md §🔧 故障排查`
- 读者：跑命令报错的人
- 目标：解决 6 大常见错误
- 关键：**错误原文 + 原因 + 解决** 3 段式

### 2.3 Reference（27 因子术语表）
- 位置：`SKILL.md §📖 27 因子术语表`
- 读者：想知道某个因子含义的人
- 目标：查 5 大类 27 因子
- 关键：**表格化、可查、不解释**

### 2.4 Explanation（学习目标）
- 位置：`SKILL.md §🎓 学习目标` + `§🧒 小白视角 FAQ`
- 读者：想深入理解的人
- 目标：理解为什么这么设计
- 关键：**讲故事 + 比喻 + 业界参考**

---

## 三、4 类文档的反模式

### ❌ 反模式 1：教程里讲原理
```
# 错误：第 1 步就讲为什么
"今天我们跑 daily 命令。首先，为什么要跑 daily 呢？因为 ETF 决策需要..."

# 正确：先跑通，再讲为什么
"第 1 步：跑 daily 命令。✅ 看到输出了吗？现在你知道为什么要跑 daily 了——"
```

### ❌ 反模式 2：参考手册里讲故事
```
# 错误：在 API 文档里加"这个 API 怎么来的故事"
"run_daily.py 的故事始于 2026 年 5 月..."

# 正确：参考手册只有 API
"run_daily.py daily   - 每日 ETF 决策
   参数：无
   输出：report + dingtalk + snapshot"
```

### ❌ 反模式 3：How-to 里给完整教程
```
# 错误：故障排查里从 0 开始
"要解决这个错误，先装 Python..."

# 正确：假设已入门
"ModuleNotFoundError? cd 到项目根目录 + pip install -e .[dev]"
```

### ❌ 反模式 4：原理里给操作步骤
```
# 错误：解释 27 因子时给"怎么用"
"用 M2 动量因子时，先打开 IDE..."

# 正确：只讲为什么
"M2 动量 5 日因子 = 过去 5 天涨跌幅。它能反映短期情绪，但容易被假突破骗。"
```

---

## 四、4 类文档的检查清单

写完每类文档后，问自己：

| 类型 | 检查问题 |
|------|---------|
| **Tutorial** | 1. 小白能跟着跑通吗？2. 每步 < 2 分钟？3. 没讲"为什么"？|
| **How-to** | 1. 错误原文完整吗？2. 给了原因吗？3. 给了具体命令吗？|
| **Reference** | 1. 表格化？2. 可独立查询？3. 没说"看下面"？|
| **Explanation** | 1. 讲了"为什么"吗？2. 用了比喻？3. 引用了业界理论？|

---

## 五、为什么 v1 SKILL.md 不及格？

v1 SKILL.md 的问题（v1 评估 6.5/10）：

| 维度 | v1 现状 | v2 改造 |
|------|--------|--------|
| 教程 | ❌ 缺（直接给命令）| ✅ 5 分钟跑起来 |
| 操作指南 | ⚠️ 故障排查 0 个 | ✅ 6 个场景 |
| 参考手册 | ❌ 7 因子术语表缺失 | ✅ 27 因子术语表 |
| 原理说明 | ⚠️ 策略参数有但无解释 | ✅ 学习目标 + FAQ |

**结论**：v1 只有"如何使用"（How-to 雏形），**缺 3 类**。v2 完整 4 类齐备。

---

## 六、参考来源

- [Divio Documentation Guide](https://docs.divio.com/documentation-guide/)
- [Daniele Procida 演讲: What nobody tells you about documentation](https://www.youtube.com/watch?v=t4vKPhjcTdg)
- [Read the Docs 文档分类](https://docs.readthedocs.io/en/stable/intro.html)

---

**最后更新**: 2026-06-23
**作者**: 福猫管家 🐱
**Mission**: mission-20260623-072239
