# ETF 量化 SKILL — 用户地图（User Journey Map）

> **目标读者**：产品设计者、AI Agent、新用户（先看这张图）
> **核心问题**：**"我作为一个 X 角色，应该怎么用这个 SKILL？"**
> **作者**：福猫管家 🐱
> **日期**：2026-06-20（v2.0-final 重构）
> **版本**：v2.0

---

## 一、4 类用户全景图（一张图说明白）

```
                         ┌─────────────────────────────┐
                         │     ETF 量化 SKILL 入口      │
                         │  (QwenPaw 对话 / 5 个 SKILL)  │
                         └──────────────┬──────────────┘
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            │                           │                           │
     ┌──────▼──────┐             ┌──────▼──────┐             ┌──────▼──────┐
     │  👤 散户     │             │  📚 学习者   │             │  🔬 研究者   │
     │  不懂代码    │             │  会 Python   │             │  5 年 Python │
     │  问 AI 即可  │             │  跟 AI 学    │             │  自己跑命令  │
     └──────┬──────┘             └──────┬──────┘             └──────┬──────┘
            │                           │                           │
            ▼                           ▼                           ▼
      [3 句话 80%]              [3 句话 + 学概念]              [跑命令 + 改代码]
            │                           │                           │
            └───────────────────────────┴───────────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │  🤖 AI Agent     │
                              │  集成 SKILL 到   │
                              │  自己的 Agent    │
                              └──────────────────┘
```

**关键认知**：
- 4 类用户走**不同入口**，但**共享同一个 SKILL 系统**
- 散户不需要懂"开发者路径"，开发者不需要懂"AI 集成路径"
- **每一类用户的"今天作业"不同**（不是同一份指南）

---

## 二、👤 散户投资者（最大用户群）

### 2.1 一天地图

```
┌──────────────────────────────────────────────────────────────┐
│  🌅 早上 9:00                                                  │
│  ↓                                                            │
│  跟我说："今天 ETF 决策"                                        │
│  ↓                                                            │
│  [etf-daily skill 自动跑]                                      │
│  ↓                                                            │
│  看 3 件事：                                                  │
│  • decision: BUY/HOLD/SELL → 【行动】                          │
│  • market_mode: trend_up/down/range_bound/crash → 【背景】      │
│  • warnings: 数据过期/异常 → 【风险】                           │
│  ↓                                                            │
│  决策：                                                        │
│  • BUY → 准备买（但要问 AI "为什么这只 BUY"）                  │
│  • HOLD → 不动                                                │
│  • SELL → 准备卖                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 一周地图

```
第 1 周   │ 每天说一次"今天 ETF 决策"（建立习惯）
第 2 周   │ + 周末说"ETF 验证"（看综合分）
第 3 周   │ + 持仓后说"再平衡建议"（学止损止盈）
第 4 周   │ + 主动问"为什么"（理解策略）
```

### 2.3 异常地图

```
数据过期警告    → "怎么刷新数据？"（等第二天 14:30）
AI 决策明显不对  → "为什么这个决策？"（让 AI 解释）
不知道怎么办    → "我应该怎么做"（让 AI 给散户建议）
综合分 < 0.6    → 这是正常的！说明策略不及格（避坑信号）
```

### 2.4 散户专属文档

📄 [`NEW_USER_GUIDE_INVESTOR.md`](NEW_USER_GUIDE_INVESTOR.md) ⭐ **第一份必读**

---

## 三、📚 量化学习者（想入门）

### 3.1 学习路径地图

```
阶段 1：会用（1 周）
├── "今天 ETF 决策"
├── "ETF 验证"
└── "再平衡建议"

阶段 2：看懂（2 周）
├── "什么是 C21-1 策略"
├── "什么是 Walk Forward"
├── "什么是 4 验证器"
└── "什么是市场模式"

阶段 3：懂为什么（4 周）
├── "为什么综合分 < 0.6"
├── "为什么 Walk Forward 失败"
├── "怎么改善策略"
└── "读 src/etf_quant/alpha/strategy_c21.py"

阶段 4：能做（8 周）
├── 学 Python 基础（2 周）
├── 学 pandas/numpy（2 周）
├── 学 matplotlib（1 周）
├── 学 backtrader（2 周）
└── 改一个因子试试（1 周）
```

### 3.2 学习者的工具调用地图

```
[基础使用]
   ↓
"今天 ETF 决策" → etf-daily
   ↓
"ETF 验证" → etf-research
   ↓
"什么是 C21-1" → quant-knowledge
   ↓
[深入]
   ↓
跑 pytest → 自己看测试输出
   ↓
读 src/etf_quant/alpha/strategy_c21.py → 理解 C21-1
   ↓
读 src/etf_quant/backtest/comprehensive_validator.py → 理解 4 验证器
```

### 3.3 学习者专属文档

📄 [`NEW_USER_GUIDE_INVESTOR.md`](NEW_USER_GUIDE_INVESTOR.md)（散户版，但概念都适用）

---

## 四、🔬 量化研究者（自己改）

### 4.1 研究者地图

```
[开发环境]
   ↓
git clone etf_quant_v2
pip install -e ".[dev]"
   ↓
[验证环境]
   ↓
pytest tests/ --ignore=tests/benchmark
   ↓
[业务跑通]
   ↓
python skills/etf-daily/scripts/run_daily.py daily
python skills/etf-research/scripts/run_validate.py validate
python skills/quant-knowledge/scripts/run_knowledge.py strategy
python skills/stock-analyze/scripts/run_analyze.py info 159338
python skills/stock-portfolio/scripts/run_portfolio.py status
   ↓
[改代码]
   ↓
src/etf_quant/alpha/factors/ → 新加因子
src/etf_quant/backtest/ → 改验证器
src/etf_quant/portfolio/ → 改持仓逻辑
   ↓
[提交]
   ↓
git add -p
git commit (按 COMMIT_TEMPLATE.md)
git push origin main
```

### 4.2 研究者常用命令

| 命令 | 用途 |
|------|------|
| `pytest tests/ -v` | 跑测试 |
| `python skills/etf-daily/scripts/run_daily.py daily` | 每日决策 |
| `python skills/etf-research/scripts/run_validate.py validate` | 综合验证 |
| `python scripts/腐化自检.py` | 8 维自检 |
| `python scripts/init_database.py` | 初始化 DB |
| `python scripts/migrate_v1_to_v2.py` | 数据迁移 |

### 4.3 研究者专属文档

📄 [`NEW_USER_GUIDE.md`](NEW_USER_GUIDE.md)（技术版，6 步走通）
📄 [`../docs/PRD.md`](../etf_strategy/docs/PRD.md)（产品需求）
📄 [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)（架构）

---

## 五、🤖 AI Agent 开发者（集成 SKILL）

### 5.1 集成地图

```
[理解 SKILL]
   ↓
读 AGENTS.md（v2 仓根目录）
读 CLAUDE.md（同上）
读 5 个 SKILL.md
   ↓
[选择调用方式]
   ↓
方式 A：通过 QwenPaw 对话（最简单）
   用户说触发词 → QwenPaw 自动调用
   ↓
方式 B：直接命令行
   python skills/<name>/scripts/run_xxx.py [args]
   ↓
方式 C：Python 模块调用
   from etf_quant.alpha.strategy_c21 import C21Strategy
   ↓
[集成]
   ↓
方式 A：让用户的 AI 知道这些触发词
方式 B：写 wrapper 脚本
方式 C：把 etf_quant_v2 作为依赖引入
```

### 5.2 集成时的关键决策

| 决策点 | 选项 |
|--------|------|
| **调用方式** | QwenPaw 对话 / 命令行 / Python 模块 |
| **数据访问** | DataLoader（推荐）/ 直接 sqlite3（不推荐） |
| **错误处理** | 捕获 exceptions + 返回 dict / 让异常冒泡 |
| **凭据管理** | .env 文件 / 环境变量（不推荐入 git） |

### 5.3 AI Agent 专属文档

📄 [`../AGENTS.md`](../AGENTS.md)（v2 仓根）
📄 [`../CLAUDE.md`](../CLAUDE.md)（Claude Code 专用）
📄 [`NEW_USER_GUIDE.md`](NEW_USER_GUIDE.md)（技术版）

---

## 六、3 个最常走的关键路径（详细版）

### 路径 1：散户每天的"3 句话循环"

```
入口：QwenPaw 对话（任何支持 QwenPaw 的客户端）
  ↓
09:00 "今天 ETF 决策"
  ↓
[etf-daily skill]
  ↓
输出 JSON（11 字段）
  ↓
用户看 3 个关键字段
  ↓
做决定（BUY/HOLD/SELL）
  ↓
有持仓？
  ├── 否 → 准备买（问 AI "为什么这只 BUY"）
  └── 是 → 09:30 "再平衡建议"
              ↓
         [stock-portfolio skill]
              ↓
         输出：持仓状态 + 行动建议
              ↓
         需要操作？
         ├── 是 → 按建议执行
         └── 否 → 结束当天流程
```

**总耗时**：5-10 分钟/天
**需要技能**：会打字即可

### 路径 2：研究者的一次完整实验

```
入口：开发者本地终端
  ↓
00:00 git status（看上次实验进度）
  ↓
00:05 跑 pytest（验证基线）
  ↓
00:10 跑 5 个 skill（业务跑通）
  ↓
00:15 跑 8 维自检（腐化检查）
  ↓
00:20 读 AGENTS.md / PRD.md（理解项目）
  ↓
00:30 修改 src/etf_quant/xxx（改代码）
  ↓
01:00 跑测试（验证改动）
  ↓
01:10 8 维自检（再确认）
  ↓
01:20 git add -p + commit（按 COMMIT_TEMPLATE）
  ↓
01:30 git push origin main
```

**总耗时**：1-2 小时/次实验
**需要技能**：Python + git + pytest + 量化基础

### 路径 3：AI Agent 的第一次集成

```
入口：AI Agent 配置文件
  ↓
读 5 个 SKILL.md（理解每个 SKILL 干什么）
  ↓
读 SOUL.md / AGENTS.md（理解系统约束）
  ↓
选择集成方式：
  ├── A：让 Agent 知道触发词（最小集成）
  ├── B：写 wrapper 脚本（中等集成）
  └── C：作为 Python 依赖（深度集成）
  ↓
小流量测试（3-5 个场景）
  ↓
看输出格式是否符合预期
  ↓
扩展到完整场景
```

**总耗时**：2-4 小时/次集成
**需要技能**：Python + Agent 框架

---

## 七、异常处理地图

### 7.1 散户异常路径

```
[散户] 看到 "未找到"
   ↓
   └── 跟我（AI）说："我输入 X 报错了"
                    ↓
              [AI 解释]
                    ↓
              "stock_info 表无此股票"
                    ↓
              "可试试 159338/159577/159611"
                    ↓
              [散户按建议试]
```

### 7.2 研究者异常路径

```
[研究者] pytest 失败
   ↓
   ├── 看 traceback
   ├── pytest tests/xxx -v --tb=short
   └── git diff HEAD 看最近改动
```

### 7.3 AI Agent 异常路径

```
[AI Agent] 调 SKILL 出错
   ↓
   ├── 看 SKILL.md 触发词是否对
   ├── 看 SOUL.md 数据访问规则
   └── 跟我（AI）说："我调 X 失败了，输出 Y"
```

---

## 八、用户地图的设计原则

### 8.1 我遵循的 4 条原则

1. **按角色分流**——散户/学习者/研究者/AI 各走各的入口
2. **行动优先**——每张图先画"今天能做什么"，再画"未来能做什么"
3. **触发词统一**——一句话能说清，绝不用两句话
4. **诚实标注**——不确定的地方明确说"不确定"

### 8.2 我**没有**做的事

1. ❌ 没有把 4 类用户混在一起写一份"通用指南"
2. ❌ 没有用技术语言给散户（"跑 pytest" "导入 DataLoader"）
3. ❌ 没有假设所有人都懂 Python
4. ❌ 没有"我会替你跑"的演示（应该用户自己跑）

### 8.3 我**之前**犯的错（自我批评）

1. ❌ **先写技术版后写散户版**——应该是反的（散户是目标用户）
2. ❌ **触发词不统一**（README 写"ETF 决策"，指南写"今天 ETF 决策"）
3. ❌ **散户版没有"今天能做什么"清单**——让用户读完不知道干啥
4. ❌ **演示代替教学**（我说"我跑了一遍"而不是"你跑一遍"）

### 8.4 修复方案（按本地图）

| 错 | 修复 |
|---|------|
| 先写技术版后写散户版 | ✅ 已写散户版（NEW_USER_GUIDE_INVESTOR.md） |
| 触发词不统一 | 本地图统一为"今天 ETF 决策"等 |
| 散户版没"今天能做什么" | 散户版加了"今天作业"4 件 |
| 演示代替教学 | 散户版改成"你跟 AI 说 X" |

---

## 九、用户地图与现有文档的对应关系

| 角色 | 主入口文档 | 辅助文档 |
|------|-----------|---------|
| 👤 散户 | [`NEW_USER_GUIDE_INVESTOR.md`](NEW_USER_GUIDE_INVESTOR.md) | 本地图 + [NEW_USER_FEEDBACK_REPORT.md](NEW_USER_FEEDBACK_REPORT.md) |
| 📚 学习者 | [`NEW_USER_GUIDE_INVESTOR.md`](NEW_USER_GUIDE_INVESTOR.md) | 本地图 + 散户版 + [QUICKSTART.md](../QUICKSTART.md) |
| 🔬 研究者 | [`NEW_USER_GUIDE.md`](NEW_USER_GUIDE.md) | 本地图 + [PRD.md](../docs/PRD.md) + [ARCHITECTURE.md](../docs/ARCHITECTURE.md) |
| 🤖 AI Agent | [`../AGENTS.md`](../AGENTS.md) + [`../CLAUDE.md`](../CLAUDE.md) | 本地图 + [NEW_USER_GUIDE.md](NEW_USER_GUIDE.md) |

---

## 十、给用户的"30 秒找到入口"

```
你是谁？                  →  你该看什么？
─────────────────────────────────────────
不会代码 / 只想看信号       →  散户版（NEW_USER_GUIDE_INVESTOR.md）
会 Python / 想入门          →  散户版 + 学习路径
5 年 Python / 自己改        →  技术版（NEW_USER_GUIDE.md）
AI Agent / 集成 SKILL       →  AGENTS.md
不确定 / 随便看看           →  本地图（USER_JOURNEY_MAP.md）
```

---

## 附录 A：流程图速查（贴给你看）

### A.1 散户日常决策流

```
   [每天早上]
       │
       ▼
 ┌──────────────┐    跟我说
 │  今天 ETF 决策 │ ──────────► [etf-daily]
 └──────────────┘                  │
       ▲                            ▼
       │                     ┌─────────────┐
       │                     │ decision = ? │
       └─────[问 AI]─────────┴─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
            BUY               HOLD               SELL
              │                  │                  │
              ▼                  ▼                  ▼
         准备买                不动              准备卖
         (问 AI 为什么)        (结束)            (问 AI 为什么)
```

### A.2 数据流（统一入口）

```
   [5 个 SKILL]
        │
        ▼
 ┌──────────────┐
 │ DataLoader   │ ←── 唯一读取入口
 │ DataWriter   │ ←── 唯一写入入口
 └──────┬───────┘
        │
        ▼
   ┌─────────┐
   │ etf.db  │ ←── 唯一数据源（SQLite）
   └─────────┘
```

---

## 附录 B：本地图的诚实声明（按规则 6.1）

**这张地图不是完整设计**，有 3 个已知不足：

1. **"AI Agent 集成"路径只画了框架**，实际集成时需要更多细节
2. **异常处理不完整**，只画了 3 类常见异常
3. **学习路径时间估算偏乐观**（学习者通常会更慢）

**修复方向**：
- 等真实用户反馈后再迭代
- 在 `NEW_USER_FEEDBACK_REPORT.md` 中追加新发现

---

> **本地图遵循规则 6**：结论先行（4 类用户 + 一张图）
> **本地图遵循规则 13**：所有路径都有具体入口（不空谈"业界最佳实践"）
> **本地图遵循规则 8**：移动端友好（短段落 + ASCII 图 + 表格）

---

**最后更新**：2026-06-20
**维护人**：福猫管家 🐱
**相关文档**：
- [`NEW_USER_GUIDE_INVESTOR.md`](NEW_USER_GUIDE_INVESTOR.md) ⭐ 散户版
- [`NEW_USER_GUIDE.md`](NEW_USER_GUIDE.md) 技术版
- [`NEW_USER_FEEDBACK_REPORT.md`](NEW_USER_FEEDBACK_REPORT.md) 12 不足清单
- [`../AGENTS.md`](../AGENTS.md) AI 协作指南
- [`../CLAUDE.md`](../CLAUDE.md) Claude Code 指南

---

# 📌 业务核心场景：从 0 到 1 建立第一个量化模型

> **场景**：散户想建立自己的量化模型（不是看 BUY 信号）
> **日期**：2026-06-21
> **基于**：Mission quantor-onboard（mission-20260620-235022）
> **作者**：福猫管家 🐱

---

## 一、为什么这一章是必须的

之前的地图（第二、三、四、五章）都在讲**用户怎么用现成 SKILL**——
但 v2 产品的核心目标（PRD）：**"C2 散户'想学方'"** + **"AI-Native 而非 AI-Assisted"**。

**翻译**：散户要的不是"看 BUY 信号"，是"能建立自己的模型"。

这才是 v2 的核心交付价值。**前面章节补充**这一章是必经路径。

---

## 二、3 块定义（按用户原话）

```
量化投资模型 = 择股 + 择时 + 仓位管理
                  │     │        │
                  │     │        └─ 多种交易纪律的决策树
                  │     └───────── 多因子组合（入场 + 过滤）
                  └──────────────── 股票池（条件筛选）
```

**3 块的依赖关系**：
1. **先有池**（择股）—— 不然不知道在哪找信号
2. **再有时**（择时）—— 在池里找买卖点
3. **最后管仓**（仓位管理）—— 买了之后怎么管

---

## 三、3 阶段详细路径

### 阶段 1：择股（建立 ETF 池）

**4 步引导**：

```
第 1 步：原理（≥100 字）
   散户问 "什么是择股"
   AI 解释：从 1486 只 ETF 筛选 → 4 个条件（流动性/盘子/跟踪误差/年限）
   ↓
第 2 步：v2 默认
   散户问 "什么是我的 ETF 池"
   AI 展示：14 核心 + 40 参考
   ↓
第 3 步：调整
   散户说 "加 X / 去 Y"
   AI 解释为什么这么改合理（≥100 字 + 数据点）
   ↓
第 4 步：验证
   AI 跑池子统计（核心/参考分布 + 4 条件覆盖）
```

**v2 已支持**：
- ✅ `src/etf_quant/universe/loader.py`（ETFListLoader）
- ✅ pool_role 字段（core/reference/excluded）
- ✅ 14 核心 + 40 参考真实加载

**v2 还缺**：
- ⏳ 散户对话式编辑接口（**Mission 正在补** → US-001~003）

---

### 阶段 2：择时（多因子组合）

**4 步引导**：

```
第 1 步：什么是因子
   散户问 "什么是因子"
   AI 解释：3 类（入场/过滤/出场）
   ↓
第 2 步：C21-1 + 27 因子
   散户问 "什么是 C21-1"
   AI 解释：BOLL 中轨 + MA60（v1 金三角）
   ↓
第 3 步：加自己的因子
   散户说 "我想加 RSI<30"
   AI 实现 + 注册 + 跑 4 验证器
   ↓
第 4 步：看综合分
   AI 跑 ComprehensiveValidator
   解释分数变化的根因（Walk Forward / Monte Carlo / Cross ETF / Consistency）
```

**v2 已支持**：
- ✅ 27 因子 + W4 RV（Sprint-6）
- ✅ C21-1 策略
- ✅ ComprehensiveValidator 4 验证器

**v2 还缺**：
- ⏳ 散户对话式加因子（**Mission 正在补** → US-004~006）

---

### 阶段 3：仓位管理（交易纪律）

**4 步引导**：

```
第 1 步：3 大铁律
   散户问 "什么是仓位管理"
   AI 解释：止损 / 不重仓 / 不死扛
   ↓
第 2 步：22 字段中 6 个关键
   散户问 "什么是 PositionGuide"
   AI 解释：stop_loss / take_profit / min_hold_days / max_hold_days / max_holdings / max_position_pct
   ↓
第 3 步：调纪律
   散户说 "我止损 5%"
   AI 走 DataLoader/DataWriter 更新配置
   ↓
第 4 步：跑持仓验证
   AI 跑 portfolio rebalance
   解释改动对持仓的影响
```

**v2 已支持**：
- ✅ PositionGuide 22 字段
- ✅ max_holdings=2 / max_position_pct 等参数化
- ✅ portfolio.rebalance

**v2 还缺**：
- ⏳ 散户对话式调纪律（**Mission 正在补** → US-007~009）

---

## 四、整合路径（US-010）

```
散户说 "帮我从 0 建立模型"
   ↓
[quantor-onboard skill]
   ↓
自动按 择股 → 择时 → 仓位 顺序引导
   ↓
每块结束后有 checkpoint（"你确定要进入下一块吗？"）
   ↓
支持：中断 / 跳过 / 回头改（state 持久化到 state.json）
```

**v2 整合**：
- ✅ `skills/quantor-onboard/scripts/run_onboard.py`（已实现）
- ✅ state.json 管理（已完成/跳过/回头）
- ✅ 串联 3 个 block

---

## 五、v2 已支持 vs 还缺什么（诚实清单）

| 块 | v2 已支持 | Mission 正在补 |
|---|----------|---------------|
| **择股** | universe/loader.py（14+40） | US-001~003 对话式引导 |
| **择时** | 27 因子 + C21-1 + 4 验证器 | US-004~006 对话式加因子 |
| **仓位** | PositionGuide 22 字段 + portfolio | US-007~009 对话式调纪律 |
| **整合** | 5 个 skill + 1 个 quantor-onboard skill | US-010 已完成 |
| **散户叙事** | NEW_USER_GUIDE_INVESTOR.md | US-011 已重写（3 块） |
| **用户地图** | USER_JOURNEY_MAP.md | US-012 已新增本章 |

---

## 六、用户的"成功标准"

按用户 3 块定义 + Mission 目标，**用户入门 = 能讲清楚下面 3 件事**：

1. **我的池怎么选？**（4 个条件？我加了/去了什么？）
2. **我的因子是什么？**（C21-1？加了什么？为什么？）
3. **我的纪律是什么？**（止损 %？单只 %？最大持仓天数？）

**3 件都能讲清楚 = 用户已入门量化**。

**讲不清楚 = 回去看今天作业**（US-011 散户版指南）。

---

## 七、与之前章节的关系

| 之前章节 | 关系 |
|---------|------|
| 二、散户投资者（一天地图） | **本章是它的"长期版"**（4 周 vs 1 天）|
| 三、量化学习者 | 本章是**学习者路径的具体化** |
| 四、量化研究者 | 本章是**研究者的入门版**（散户也能走） |
| 六、关键路径 | 本章是**路径 1（散户日循环）的扩展** |

---

## 八、相关文档

- [`NEW_USER_GUIDE_INVESTOR.md`](NEW_USER_GUIDE_INVESTOR.md) — 散户版指南（v2，3 块叙事）
- [`NEW_USER_FEEDBACK_REPORT.md`](NEW_USER_FEEDBACK_REPORT.md) — 12 不足清单
- [`../../missions/mission-20260620-235022/`](../../missions/mission-20260620-235022/) — Mission 详情
- [`../../skills/quantor-onboard/`](../../skills/quantor-onboard/) — 对话式引导 skill（已实现）

---

> **本章遵循规则 6**：结论先行（"为什么这一章是必须的"放最上面）
> **本章遵循规则 13**：所有建议都有具体出处（不是"业界最佳实践"）
> **本章遵循规则 23**：诚实标注 v2 已支持 vs 还缺什么
