# ETF 量化 v2 — 新用户完整上手指南

> **目标读者**：第一次接触 etf_quant_v2 项目的新用户（含 AI Agent / 开发者）
> **完成时间**：约 15 分钟（含测试运行）
> **覆盖范围**：5 个 Skill 全景 + 业务闭环 + 自检
> **日期**：2026-06-20（基于真实跑通验证）
>
> 👤 **如果你不会 Python**，请看 [`NEW_USER_GUIDE_INVESTOR.md`](NEW_USER_GUIDE_INVESTOR.md)（散户投资者版），本指南是技术版。

---

## 📋 总览：6 步走完 v2 全景

| 步 | 动作 | 触发词 | 命令 | 验证点 |
|:--:|------|--------|------|--------|
| **0** | 环境检查 | - | `python3 scripts/...` 见下文 | 软链接 + DB + Python 就绪 |
| **1** | 跑测试基线 | "跑测试" | `pytest tests/ --ignore=tests/benchmark` | **217 passed** |
| **2** | 量化知识库 | "量化策略" / "教训" | `quant-knowledge skill` | 1 策略 + 123 教训 + 12 参考 |
| **3** | ETF 每日决策 | "ETF 决策" / "跑 ETF" | `etf-daily daily` | 11 字段决策报告 |
| **4** | ETF 深度研究 | "ETF 验证" / "评分" | `etf-research validate` | 4 验证器分数 |
| **5** | 个股 + 持仓 | "个股分析" / "再平衡" | `stock-analyze` + `stock-portfolio` | 业务闭环 |
| **+** | 8 维腐化自检 | "自检" | `腐化自检.py` | **100/100** |

---

## Step 0：环境就绪检查（30 秒）

### 动作

```bash
cd /home/qwenpaw/.qwenpaw/workspaces/default
```

### 验证 4 项

#### 0.1 软链接齐全

```bash
ls -la skills/etf-{daily,research} skills/quant-knowledge skills/stock-{analyze,portfolio}
```

**期望输出**（每行 `-> /home/qwenpaw/.../etf_quant_v2/skills/...`）：

```
skills/etf-daily         -> /home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/skills/etf-daily
skills/etf-research      -> /home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/skills/etf-research
skills/quant-knowledge   -> /home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/skills/quant-knowledge
skills/stock-analyze     -> /home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/skills/stock-analyze
skills/stock-portfolio   -> /home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/skills/stock-portfolio
```

**教学点（L259 教训）**：QwenPaw 只扫描 `~/.qwenpaw/workspaces/default/skills/`，
不扫描项目仓子目录——所以必须软链接。

#### 0.2 数据库存在

```bash
ls -la etf_quant_v2/data/etf.db
```

**期望**：约 12.8MB 的 SQLite 文件。

#### 0.3 Python + 核心模块

```python
import sys
sys.path.insert(0, "etf_quant_v2/src")
from etf_quant.data_layer.loader import DataLoader
from etf_quant.data_layer.writer import DataWriter
```

**期望**：无 ImportError。Python ≥ 3.11。

#### 0.4 数据库表清单（14 张）

| 表 | 行数 | 用途 |
|---|---:|------|
| `daily` | 69,480 | 日线行情（OHLCV） |
| `etf_names` | 1,486 | ETF 元数据（14 核心 + 40 参考） |
| `stock_info` | 66 | 个股基本信息 |
| `trade_history` | 3 | 交易记录（is_real 区分真假盘） |
| `decision_snapshot` | 4 | 决策快照 |
| `positions` | 1 | 当前持仓 |
| `etf_name_metrics` | 0 | ETF 名称指标（待填充） |
| `etf_name_retry_queue` | 0 | 名称获取重试队列 |
| `realtime_cache` | 0 | 实时行情缓存 |
| `execution_log` | 0 | 执行日志 |
| `performance_metrics` | 0 | 绩效指标 |
| `audit_log` | 1 | 审计日志 |
| `schema_version` | 1 | schema 版本号 |
| `sqlite_sequence` | 2 | SQLite 自增序列 |

---

## Step 1：跑测试基线（3 分钟）

### 触发词
> "跑测试"

### 命令

```bash
cd etf_quant_v2
python3 -m pytest tests/ --ignore=tests/benchmark --tb=no
```

### 期望输出
```
........................................................................ [ 33%]
........................................................................ [ 66%]
........................................................................ [ 99%]
.                                                                        [100%]
217 passed in 138.13s (0:02:18)
```

### 教学点
- **217 个测试 = 100% 通过**（unit 159 + integration 32 + regression 26）
- **不跑 benchmark**：5 个 pytest-benchmark 用例需要额外依赖
- **2 分 18 秒**：可接受范围

### 如果失败
```bash
# 看错误详情
python3 -m pytest tests/unit/alpha/test_factors.py -v --tb=short

# 常见原因：Python 版本 < 3.11
python3 --version
```

---

## Step 2：量化知识库（先查再答）⭐

### 触发词
> "量化策略" / "教训" / "业界参考"

### 为什么先做这步？
**L228 教训**：**先查再答**。在动手前先了解项目沉淀，避免重复踩坑。

### 命令 3 件套

#### [a] 策略列表
```bash
python3 ../skills/quant-knowledge/scripts/run_knowledge.py strategy
```
**输出**：
```json
{
  "strategies": [{
    "strategy_id": "C21-1",
    "strategy_name": "BOLL_strict_middle+MA60 (无卖出)",
    "version": "1.0"
  }],
  "total": 1
}
```

#### [b] 教训列表
```bash
python3 ../skills/quant-knowledge/scripts/run_knowledge.py lesson
```
**输出**：`{"lessons": [103, 104, ..., 247], "total": 123}`

#### [c] 单条教训详情
```bash
python3 ../skills/quant-knowledge/scripts/run_knowledge.py lesson 211
```
**输出**：`{"lesson_id": 211, "title": "...", "content": "...前 500 字..."}`

#### [d] 业界参考（12 篇）
```bash
python3 ../skills/quant-knowledge/scripts/run_knowledge.py reference
```
**输出**：12 篇 v2-roadmap notes（01_v1_origin ~ 12_git_history）

### 教学点
- 教训文件位置：`memory/lessons/L103_*.md ~ L247_*.md`
- 业界参考位置：`v2-roadmap/notes/01_*.md ~ 12_*.md`（在 workspace 根目录）
- **C21-1 策略**：v1 颠覆性发现的"金三角"（BOLL+MA60，无卖出信号）

---

## Step 3：ETF 每日决策（核心）

### 触发词
> "ETF 决策" / "跑 ETF" / "ETF 每日检查"

### 命令

```bash
python3 ../skills/etf-daily/scripts/run_daily.py daily
```

### 完整输出示例（真实跑通）

```json
{
  "model_name": "v2_sop",
  "strategy_name": "C21Strategy",
  "timestamp": "2026-06-20T22:29:22",
  "market_mode": "range_bound",
  "decision": "HOLD",
  "buy_candidates": [],
  "sell_candidates": [],
  "holdings_count": 1,
  "holdings_detail": [
    {"code": "512170"}
  ],
  "data_freshness": "距最新数据 4229 分钟",
  "warnings": [
    "数据已过期 4229 分钟（阈值 80）"
  ],
  "snapshot_id": "snap_etf_2026-06-20T22:29:22"
}
```

### 11 字段含义

| 字段 | 含义 | 取值 |
|------|------|------|
| `model_name` | 模型标识 | `v2_sop` |
| `strategy_name` | 策略名 | `C21Strategy` |
| `timestamp` | 决策时间 | ISO 8601 |
| `market_mode` | 市场模式 | `range_bound`（震荡）/ `trend_up` / `trend_down` / `crash` |
| `decision` | 决策动作 | `BUY` / `HOLD` / `SELL` |
| `buy_candidates` | 买入候选 | `[{code, score}]` |
| `sell_candidates` | 卖出候选 | `[{code, reason}]` |
| `holdings_count` | 持仓数 | 0~N |
| `holdings_detail` | 持仓明细 | `[{code, ...}]` |
| `data_freshness` | 数据新鲜度 | "距最新数据 X 分钟" |
| `warnings` | 警告信息 | `["数据已过期 X 分钟..."]` |

### 教学点
- **决策快照**会写入 `decision_snapshot` 表（`snapshot_id` 可追溯）
- **数据过期**会触发 warning（阈值 80 分钟 = 1.3 小时）
- **HOLD**：当前 1 持仓（512170），策略未触发买/卖

### 其他模式

```bash
python3 ../skills/etf-daily/scripts/run_daily.py eval     # 完整评估
python3 ../skills/etf-daily/scripts/run_daily.py history  # 历史查询
```

---

## Step 4：ETF 深度研究（4 验证器）

### 触发词
> "ETF 验证" / "ETF 评分" / "ETF 回测"

### 命令

```bash
python3 ../skills/etf-research/scripts/run_validate.py validate
```

### 完整输出示例

```json
{
  "composite_score": 0.4260022447261703,
  "pass_": false,
  "confidence": "LOW",
  "walk_forward_score": 0.3333333333333333,
  "monte_carlo_score": 0.8,
  "cross_etf_score": 0.3333333333333333,
  "consistency": 0.5600224472617032,
  "warnings": [
    "Cross ETF 泛化能力不足",
    "Walk Forward 时序验证失败"
  ]
}
```

### 4 验证器 + 综合分

| 验证器 | 权重 | 分数 | 含义 |
|--------|:---:|:---:|------|
| **Walk Forward** | 0.40 | 0.33 | 时序外推（避免未来函数） |
| **Monte Carlo** | 0.15 | 0.80 | 路径扰动稳健性 |
| **Cross ETF** | 0.35 | 0.33 | 跨 ETF 泛化能力 |
| **Consistency** | 0.10 | 0.56 | 子时段一致性 |

**综合分 = 0.426**（未通过 0.6 阈值）

### 教学点
- **4 验证器**是 US-021 设计，每个验证器独立打分再加权
- **未通过（pass=false）**说明策略当前不及格——**这正是研究价值**（识别弱点）
- **Walk Forward 0.33** = 时序验证失败 → 数据/特征可能泄漏
- **Cross ETF 0.33** = 泛化能力差 → 可能在过拟合个别 ETF

### 因子分解 + 回测样本

```bash
python3 ../skills/etf-research/scripts/run_validate.py factor    # 因子权重 + 分数
python3 ../skills/etf-research/scripts/run_validate.py backtest  # 最近 10 个样本
```

---

## Step 5：个股 + 持仓业务闭环

### 5.1 个股深度分析

#### 命令

```bash
python3 ../skills/stock-analyze/scripts/run_analyze.py info 159338
```

#### 输出
```json
{
  "code": "159338",
  "name": "中证A500ETF国泰",
  "exchange": null,
  "full_code": null,
  "list_date": null,
  "updated_at": "2026-05-30 04:40:18"
}
```

#### 错误友好化（新功能）

如果查询不在 stock_info 表的 code（如 600519）：

```bash
python3 ../skills/stock-analyze/scripts/run_analyze.py info 600519
```

**输出**：
```json
{
  "error": "未找到",
  "code": "600519",
  "reason": "stock_info 表无 code=600519",
  "available_examples": [
    {"code": "159338", "name": "中证A500ETF国泰"},
    {"code": "159577", "name": "美国50ETF汇添富"},
    {"code": "159611", "name": "电力ETF广发"},
    ...
  ],
  "total_stocks_in_db": 5,
  "suggestion": "可用示例 code 之一，或检查是否需要先迁移数据"
}
```

#### 对比（vs 板块/大盘）

```bash
python3 ../skills/stock-analyze/scripts/run_analyze.py compare 159338
```
**输出**：`{"stock": {...}, "sector_avg": 4.188, "market_avg": 4.188}`

### 5.2 持仓组合

#### status（当前持仓）
```bash
python3 ../skills/stock-portfolio/scripts/run_portfolio.py status
```
**输出**：
```json
{
  "holdings_count": 1,
  "guides": [{
    "code": "512170",
    "action": "HOLD",
    "reason": "default hold",
    "should_stop_loss": false,
    "should_take_profit": false
  }]
}
```

#### rebalance（再平衡建议）
```bash
python3 ../skills/stock-portfolio/scripts/run_portfolio.py rebalance
```
**输出**：`{"actions": []}`（无需再平衡）

#### attribution（业绩归因）
```bash
python3 ../skills/stock-portfolio/scripts/run_portfolio.py attribution
```
**输出**：`{"total_trades": 3, "real_trades": 2, "paper_trades": 0}`

### 教学点
- **22 字段 PositionGuide**：每只持仓的止损/止盈/到期/持仓天数等
- **is_real 字段**（规则 23）：实盘 = is_real=1，模拟/测试 = is_real=0
- **max_holdings=2**（v8 + 用户 B 决策）：最大持仓数限制

---

## Step +：8 维腐化自检

### 触发词
> "自检" / "跑腐化自检"

### 命令

```bash
python3 scripts/腐化自检.py --non-interactive --sprint=7
```

### 输出
```
维度 1 (Hallucination): 100/100  ✅ 通过
维度 2 (Context Loss): 100/100   ✅ 通过
维度 3 (Task Drift): 100/100     ✅ 通过
维度 4 (Capability Drift): 100/100 ✅ 通过
维度 5 (因果倒置): 100/100       ✅ 通过
维度 6 (过度概括): 100/100       ✅ 通过
维度 7 (重复犯错): 100/100       ✅ 通过
维度 8 (文档脱节): 100/100       ✅ 通过

加权平均: 100.0/100
判定: ✅ 优秀
```

### 8 维度含义

| # | 维度 | 含义 |
|---|------|------|
| 1 | Hallucination | 编造不存在的事实 |
| 2 | Context Loss | 上下文丢失 |
| 3 | Task Drift | 任务跑偏 |
| 4 | Capability Drift | 能力漂移 |
| 5 | 因果倒置 | 输出反推输入 |
| 6 | 过度概括 | 一概而论 |
| 7 | 重复犯错 | 同类错误重犯 |
| 8 | 文档脱节 | 文档与代码不一致 |

---

## 🗺️ 触发词速查

| 你说 | 自动调用 | Skill |
|------|---------|-------|
| "ETF 决策" / "跑 ETF" | `run_daily.py daily` | `etf-daily` |
| "ETF 验证" / "ETF 评分" | `run_validate.py validate` | `etf-research` |
| "量化策略" / "教训" | `run_knowledge.py strategy/lesson` | `quant-knowledge` |
| "个股分析" | `run_analyze.py info {code}` | `stock-analyze` |
| "再平衡" / "持仓组合" | `run_portfolio.py status/rebalance` | `stock-portfolio` |
| "跑测试" | `pytest tests/` | 测试 |
| "自检" | `腐化自检.py` | 自检 |

---

## ❌ 新用户常踩的坑（来自 NEW_USER_FEEDBACK_REPORT）

| 坑 | 现象 | 正确做法 |
|---|------|---------|
| **stock_info 表无 600519** | 报"未找到" | 用表里的 code（159338/159577/159611） |
| **数据过期警告** | warnings 提示 | 这是正常的，每天 14:30 cron 刷新 |
| **etf-research 不及格** | composite_score < 0.6 | 这是真实业务反馈，需优化策略 |
| **5 模块空壳** | 某些模块 import 失败 | Sprint-7 已修复 5 模块业务实现 |

---

## 📚 下一步学什么

### 必读（5 篇）
1. `README.md` — 项目总览
2. `QUICKSTART.md` — 5 分钟上手
3. `docs/PRD.md` — 29 US + 7 Sprint
4. `docs/ARCHITECTURE.md` — 13 模块依赖
5. `MEMORY.md` — v2 长期记忆（教训/决策）

### 选读（按角色）
- **AI Agent**：`AGENTS.md` + `CLAUDE.md` + 7 个 SOP
- **业务方**：`docs/SOP_01_DATA.md` + `SOP_03_EXPERIMENT.md`
- **开发**：`docs/INTERFACE_CONTRACT.md` + `DATA_DICTIONARY.md`

### 想学某个 Skill 的源码
```
etf_quant_v2/skills/etf-daily/scripts/run_daily.py
etf_quant_v2/skills/etf-research/scripts/run_validate.py
etf_quant_v2/skills/quant-knowledge/scripts/run_knowledge.py
etf_quant_v2/skills/stock-analyze/scripts/run_analyze.py
etf_quant_v2/skills/stock-portfolio/scripts/run_portfolio.py
```

---

## ✅ 完成检查清单

新用户跑完本指南后，应能：

- [ ] 理解 5 个 Skill 的职责分工
- [ ] 跑通 217 个测试
- [ ] 独立调用任意一个 Skill
- [ ] 看懂 11 字段决策报告
- [ ] 理解 4 验证器（Walk Forward / Monte Carlo / Cross ETF / Consistency）
- [ ] 理解 is_real 字段区分实盘/模拟
- [ ] 跑 8 维腐化自检
- [ ] 在 `memory/lessons/` 检索教训
- [ ] 在 `v2-roadmap/notes/` 检索业界参考

---

## 📝 验证记录

**作者**：福猫管家 🐱
**日期**：2026-06-20
**版本**：v2.0-final（基于 Sprint-7 业务完整化）
**验证方法**：6 步全部实跑 + 输出捕获

**实跑记录**：
- Step 0：14 表 / Python 3.11.15 / 123 教训
- Step 1：217 passed in 138.13s
- Step 2：1 策略 + 123 教训 + 12 参考
- Step 3：HOLD 1 持仓（512170）+ 数据过期警告
- Step 4：综合分 0.426（未通过）— Walk Forward 0.33 + Cross ETF 0.33 是弱点
- Step 5：业务闭环 OK（3 trades / 2 real）
- Step +：8 维自检 100/100

---

> **本指南遵循规则 6**：结论先行（每步先说"做什么 + 触发词 + 命令 + 期望输出"）
> **本指南遵循规则 13**：所有命令均有真实跑通证据（不是"业界最佳实践"）
> **本指南遵循规则 23**：stock_info 查询看 is_real 区分真假