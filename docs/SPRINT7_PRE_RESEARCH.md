# Sprint-7 B 调研 — 业务完整化（5 空壳模块 + 4 文档 + 3 改进）

> **任务**：Sprint-7 业务完整化（按用户 2026-06-19 决策"B：按业务实现标准"）
> **依据**：NEW_USER_FEEDBACK_REPORT.md 的 12 个不足
> **日期**：2026-06-19
> **范围**：P0（4 项 14.6h）+ P1（5 项 5.1h）= **9 项 19.7h**

---

## 1. 调研问题清单

| # | 问题 | 调研目的 |
|---|------|----------|
| Q1 | v1 哪些模块有可继承代码？ | 避免重写 |
| Q2 | 5 空壳模块的 v1 实现规模？ | 评估工作量 |
| Q3 | etf-daily 详细输出应该长什么样？ | 需求设计 |
| Q4 | stock-analyze 占位符如何实现？ | 业务逻辑 |
| Q5 | pyproject 缺哪些依赖？ | 完整性 |

---

## 2. Q1+Q2：v1 可继承代码盘点

### 2.1 v1 实际实现

| 模块 | v1 路径 | v1 行数 | v2 当前 | 差距 |
|------|---------|--------:|---------|------|
| **monitor** | etf_strategy/src/data/monitor.py | 200+ | README+__init__ | 需新写 200+ |
| **notify** | etf_strategy/src/notifier.py + notify/notifier.py + dingtalk_sender.py + scenario_adapter.py | 800+ | README+__init__ | 需新写 800+ |
| **performance** | etf_strategy/src/performance_analyzer.py + report_builder.py | 1000+ | README+__init__ | 需新写 1000+ |
| **scheduler** | etf_strategy/configs/cron_jobs.yaml | 50 行 yaml | README+__init__ | 需新写 50+ 脚本 |
| **universe** | etf_strategy/src/etf_pool_updater.py + industry_filter.py + industry_mapping.py | 500+ | README+__init__ | 需新写 500+ |
| **portfolio** | 无 | 0 | README+__init__ | 全新设计 |

**总计需新写**：~2800+ 行（从 v1 继承适配）

### 2.2 关键洞察

- v1 完整代码可继承（**Strangler Fig 模式**）
- 不重写只适配（v1 → v2 import 路径改 `etf_quant.xxx`）
- 风险：v1 部分代码可能有 v2 已修复的 bug

---

## 3. Q3：etf-daily 详细输出设计

### 3.1 当前输出（不足）

```json
{
  "model_name": "v2_sop",
  "strategy_name": "C21Strategy",
  "holdings_count": 0,
  "snapshot_id": "snap_etf_2026-06-19T22:41:55"
}
```

### 3.2 期望输出（按新用户需求）

```json
{
  "model_name": "v2_sop",
  "strategy_name": "C21Strategy",
  "timestamp": "2026-06-19T22:41:55",
  "market_mode": "range_bound",
  "decision": "HOLD",
  "buy_candidates": [
    {"code": "510300", "name": "沪深300ETF", "score": 0.78, "factor_details": {...}}
  ],
  "sell_candidates": [],
  "holdings": [
    {"code": "510500", "qty": 100, "entry_price": 5.5, "current_price": 5.7, "pnl_pct": 3.6, "hold_days": 10}
  ],
  "data_freshness": "2026-06-19 22:00:00",
  "warnings": ["数据超过 1 天未更新"],
  "snapshot_id": "snap_etf_2026-06-19T22:41:55"
}
```

**新增字段**：
- `market_mode`（来自 universe）
- `decision`（HOLD/BUY/SELL）
- `buy_candidates` + `sell_candidates`（带评分）
- `holdings` 详情（带盈亏）
- `data_freshness`（数据时间）
- `warnings`（告警列表）

**实现策略**：
- 调用 universe 加载池（universe 模块）
- 调用 alpha 计算因子（已有）
- 调用 execution 查持仓（已有）
- 调用 risk 算盈亏（已有）
- 调用 monitor 查数据新鲜度（monitor 模块——本 Sprint-7 实现）

---

## 4. Q4：stock-analyze 占位符实现

### 4.1 当前占位符

```json
{
  "stock": {...},
  "sector_avg": "v2_占位",
  "market_avg": "v2_占位"
}
```

### 4.2 真实数据

| 字段 | 数据源 | 现状 |
|------|--------|------|
| sector_avg | stock_info 表的行业分类 + 同行业股票平均价 | v1 industry_mapping.py 有 |
| market_avg | 沪深 300 平均价 | 需新增 fetcher |
| sector_members | 同行业股票列表 | v1 industry_filter.py 有 |

### 4.3 实现方案

```python
# src/etf_quant/stock_analyze/sector_stats.py
class SectorStatsCalculator:
    def calculate_sector_avg(self, code: str) -> float:
        """计算同行业股票的平均价"""
        # 1. 从 stock_info 查 code 的行业
        # 2. 查同行业所有股票
        # 3. 算平均价
        ...
    
    def calculate_market_avg(self) -> float:
        """计算大盘平均价（沪深 300）"""
        # 1. 调 universe 加载大盘股
        # 2. 算平均
        ...
```

---

## 5. Q5：pyproject 缺依赖

### 5.1 当前声明

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.1",
    "pytest-mock>=3.12",
    "ruff>=0.1",
    "mypy>=1.7",
]
```

### 5.2 缺

| 依赖 | 用途 | 必需性 |
|------|------|:---:|
| `pytest-benchmark>=4.0` | 5 benchmark 测试 | 🔴 P0 |
| `pytest-anyio>=4.0` | pytest 9 强制依赖 | 🔴 P0 |
| `akshare>=1.18.63` | 已声明 ✅ | - |
| `sqlalchemy>=2.0` | 已声明 ✅ | - |
| `pydantic>=2.5` | 已声明 ✅ | - |
| `httpx>=0.25` | notify 调钉钉 API | 🟡 P1 |
| `loguru>=0.7` | monitor 日志 | 🟢 P2 |

---

## 6. Sprint-7 任务清单（9 项 19.7h）

### 6.1 阶段 1：P0 修复（5 项 14.6h）

| # | 任务 | 工时 | 优先级 |
|---|------|:---:|:---:|
| 1.1 | README 状态更新（写"Sprint-6 完成 100%"）| 0.1h | P0 |
| 1.2 | 写 8 个核心文档 | 4h | P0 |
| 1.3 | 实现 5 空壳模块（universe/scheduler/monitor/notify/performance）| 10h | P0 |
| 1.4 | stock-analyze 错误提示友好化 | 0.5h | P0 |
| 1.5 | 诚实改 PRD.json（5 模块改 passes=False）| 0.1h | P0 |
| **小计** | - | **14.7h** | - |

### 6.2 阶段 2：P1 修复（4 项 5.1h）

| # | 任务 | 工时 | 优先级 |
|---|------|:---:|:---:|
| 2.1 | etf-daily 详细输出 | 1h | P1 |
| 2.2 | stock-analyze 占位符实现 | 1h | P1 |
| 2.3 | pyproject 补 pytest-benchmark | 0.1h | P1 |
| 2.4 | alpha/README 扩 27 因子 | 0.3h | P1 |
| 2.5 | portfolio 模块实现 | 2h | P1 |
| **小计** | - | **4.4h** | - |

### 6.3 阶段 3：业务完整化（额外 0.6h）

| # | 任务 | 工时 | 优先级 |
|---|------|:---:|:---:|
| 3.1 | CHANGELOG 补 Sprint-7 | 0.1h | P2 |
| 3.2 | 写 QUICKSTART.md | 0.5h | P2 |
| **小计** | - | **0.6h** | - |

**Sprint-7 总计**：14.7 + 4.4 + 0.6 = **19.7h**

---

## 7. 5 空壳模块实现计划

### 7.1 universe（1.5h）

- 从 v1 etf_pool_updater.py + industry_filter.py 继承
- 适配 v2: `from etf_quant.data_layer import DataLoader`
- 类：ETFListLoader, UniverseFilter, IndustryMapper
- 测试：3 单元 + 1 集成

### 7.2 scheduler（0.5h）

- 从 v1 configs/cron_jobs.yaml 继承
- 适配 v2: 调 `qwenpaw cron` CLI
- 类：CronJobConfig, CronSync
- 测试：2 单元

### 7.3 monitor（2h）

- 从 v1 src/data/monitor.py 继承
- 适配 v2: DataQualityMonitor, SystemHealthMonitor, BusinessAlertMonitor
- 测试：4 单元 + 1 集成

### 7.4 notify（3h）

- 从 v1 notifier.py + dingtalk_sender.py + scenario_adapter.py 继承
- 适配 v2: SignalNotifier, DingTalkClient, ScenarioAdapter
- 测试：5 单元 + 2 集成

### 7.5 performance（3.5h）

- 从 v1 performance_analyzer.py + report_builder.py 继承
- 适配 v2: 8 大类 43 指标 + 报告生成
- 测试：6 单元 + 2 集成

**5 模块测试总计**：20 单元 + 6 集成 = **26 测试**

---

## 8. 8 个核心文档清单（4h）

| # | 文档 | 内容 | 工时 |
|---|------|------|:---:|
| 1 | docs/ARCHITECTURE.md | 12 模块依赖图 + 数据流 | 0.8h |
| 2 | docs/INTERFACE_CONTRACT.md | 12 模块的 Protocol + 数据类型 | 0.8h |
| 3 | docs/DATA_DICTIONARY.md | 4 表 80 列含义 + 业务规则 | 0.8h |
| 4 | docs/SOP_01_DATA.md | 数据获取/存储/查询规范 | 0.4h |
| 5 | docs/SOP_03_EXPERIMENT.md | 实验流程（按 SOP-01 8 步）| 0.4h |
| 6 | docs/SOP_04_DATASOURCE.md | 数据源调研/接入/限速 | 0.3h |
| 7 | docs/SOP_05_BACKUP.md | 数据备份/恢复 | 0.2h |
| 8 | docs/SOP_06_DESENSITIZE.md | 数据脱敏（隐私保护）| 0.3h |
| **小计** | - | - | **4h** |

---

## 9. 风险与缓解

| 风险 | 严重性 | 缓解 |
|------|:---:|------|
| 5 模块实现量大（10h）| 中 | 从 v1 继承，不重写 |
| v1 代码可能依赖 v1 业务库 | 中 | 适配 v2 data_layer |
| monitor 的 80 分钟阈值是硬编码 | 中 | 改可配置（参考 L62 教训）|
| notify 钉钉 webhook 配置缺失 | 高 | 写 README 说明，不实调 |
| 43 指标可能不全 | 中 | 按 v1 v7 评价体系实现 |

---

## 10. 验收标准

| # | 标准 | 度量 |
|---|------|------|
| 1 | 5 模块有真实业务代码 | 5 个 .py 文件 + __init__.py |
| 2 | 26 测试全过 | pytest tests/unit + tests/integration |
| 3 | 8 文档写完 | docs/ 下 8 个 .md 文件 |
| 4 | README 状态更新 | 写"Sprint-6 完成 100%" |
| 5 | etf-daily 输出详细化 | 跑通 + 输出 ≥8 字段 |
| 6 | stock-analyze 占位符实现 | 跑通 + 不再 "v2_占位" |
| 7 | pyproject 补 pytest-benchmark | pip install -e .[dev] 不报缺 |
| 8 | alpha/README 扩 27 因子 | 27 因子清单 |
| 9 | portfolio 模块实现 | 至少 Portfolio 类 + 3 测试 |
| 10 | 222 + 30 测试全过 | pytest tests/ ≥ 252 通过 |
| 11 | 8 维自检 ≥ 95 | scripts/腐化自检.py --sprint=7 |
| 12 | pre-commit 0 拦截 | git commit 模拟提交 |

---

## 11. 业界参考（按规则 13）

| 实践 | 来源 | v2 应用 |
|------|------|---------|
| **Strangler Fig** | Fowler 2004 | 5 模块从 v1 继承 |
| **Repository Pattern** | Evans 2003 | notify/monitor 抽象数据访问 |
| **Producer-Consumer** | GoF 1994 | monitor 三层架构 |
| **ETL Pipeline** | Kimball 1996 | performance 评估流程 |
| **Cron Best Practices** | Google SRE Book 2016 | scheduler 错误处理 |

---

## 12. 涉及模块清单（按 L117 防半途改造）

| 模块 | 类型 |
|------|------|
| src/etf_quant/universe/ | **新增**（loader.py + filter.py + mapper.py）|
| src/etf_quant/scheduler/ | **新增**（cron.py + config.py）|
| src/etf_quant/monitor/ | **新增**（data_health.py + system_health.py + business_alert.py）|
| src/etf_quant/notify/ | **新增**（notifier.py + dingtalk.py + scenario.py）|
| src/etf_quant/performance/ | **新增**（metrics.py + report.py）|
| src/etf_quant/portfolio/ | **新增**（portfolio.py）|
| src/etf_quant/stock_analyze/ | **新增**（sector_stats.py）|
| skills/etf-daily/scripts/run_daily.py | **改**（详细输出）|
| skills/stock-analyze/scripts/run_analyze.py | **改**（占位符实现）|
| pyproject.toml | **改**（补 pytest-benchmark）|
| src/etf_quant/alpha/README.md | **改**（扩 27 因子）|
| README.md | **改**（状态更新）|
| docs/PRD.json | **改**（诚实标 5 US passes=False）|
| docs/ARCHITECTURE.md 等 8 文档 | **新增** |

**未改动**：alpha 因子、execution、risk、backtest、config、utils（避免半途改造）

---

## 13. 下一步

1. 用户确认 Sprint-7 调研报告
2. 创建 `git checkout -b sprint-7`
3. 按 10 步执行清单逐步实施
4. 跑测试 + 8 维自检 + pre-commit
5. 写 Sprint-7 复盘

---

> **本文档遵循规则 11**：v1 代码盘点 + 5 模块规模评估
> **本文档遵循规则 13**：5 个业界参考 + v1 路径
> **本文档遵循规则 17**：诚实声明 5 模块是空壳
