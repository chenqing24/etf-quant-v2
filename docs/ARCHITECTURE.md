# ARCHITECTURE — v2 架构

> **版本**：v2.0
> **日期**：2026-06-20
> **依据**：Sprint-0 调研 + Sprint-7 业务完整化
> **状态**：核心 3 文档（ARCHITECTURE/INTERFACE_CONTRACT/DATA_DICTIONARY）+ 5 SOP（按 12 不足 Sprint-7 P0）

---

## 1. 12 模块依赖图

```
                 ┌─────────────────────────┐
                 │   Skills (5 entry)      │
                 │  etf-daily/research/    │
                 │  stock-analyze/         │
                 │  stock-portfolio/       │
                 │  quant-knowledge        │
                 └────────┬────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   ┌─────────┐     ┌──────────┐      ┌──────────┐
   │ alpha   │     │ universe │      │ portfolio│
   │ 因子/信号│     │ ETF 池   │      │ 组合管理  │
   └────┬────┘     └────┬─────┘      └─────┬────┘
        │               │                  │
        └───────────────┼──────────────────┘
                        ↓
            ┌───────────────────────┐
            │  data_layer (唯一入口) │
            │  SQLite etf.db         │
            └───────────────────────┘
                        ↑
        ┌───────────────┼──────────────────┐
        │               │                  │
   ┌────┴────┐    ┌─────┴─────┐     ┌─────┴────┐
   │execution│    │  risk     │     │ monitor  │
   │ 交易    │    │  风控      │     │  监控    │
   └─────────┘    └───────────┘     └──────────┘
                                          │
                        ┌─────────────────┼──────────────────┐
                        ↓                 ↓                  ↓
                  ┌──────────┐    ┌──────────┐       ┌──────────┐
                  │ notify   │    │performance│       │scheduler │
                  │ 推送     │    │ 绩效     │       │ 调度     │
                  └──────────┘    └──────────┘       └──────────┘
```

## 2. 12 模块职责

| # | 模块 | 路径 | 职责 | 依赖 |
|---|------|------|------|------|
| 1 | alpha | src/etf_quant/alpha/ | 27 因子 + C21-1 策略 | universe, data_layer |
| 2 | universe | src/etf_quant/universe/ | ETF 池动态加载 | data_layer |
| 3 | data_layer | src/etf_quant/data_layer/ | 唯一数据入口（SQLite）| - |
| 4 | execution | src/etf_quant/execution/ | TradeTracker 委托模式 | data_layer, risk |
| 5 | risk | src/etf_quant/risk/ | PositionGuide 22 字段 | data_layer, execution |
| 6 | monitor | src/etf_quant/monitor/ | 三层监控（数据/系统/业务）| data_layer, universe |
| 7 | performance | src/etf_quant/performance/ | 8 大类 43 指标 | universe |
| 8 | notify | src/etf_quant/notify/ | 钉钉推送（双通道）| - |
| 9 | portfolio | src/etf_quant/portfolio/ | 组合管理 | - |
| 10 | backtest | src/etf_quant/backtest/ | ComprehensiveValidator 4 验证器 | alpha, risk, performance |
| 11 | scheduler | src/etf_quant/scheduler/ | QwenPaw cron 封装 | - |
| 12 | config | src/etf_quant/config/ | 配置 + 常量 | - |
| 13 | utils | src/etf_quant/utils/ | 工具函数 | - |

## 3. 5 Skill 入口

| Skill | 路径 | 触发词 | 调用 |
|-------|------|--------|------|
| etf-daily | skills/etf-daily/ | ETF 决策 | universe + alpha + execution + risk + monitor + notify |
| etf-research | skills/etf-research/ | ETF 深度研究 | backtest.ComprehensiveValidator |
| stock-analyze | skills/stock-analyze/ | 个股分析 | data_layer + universe |
| stock-portfolio | skills/stock-portfolio/ | 组合回测 | portfolio + backtest |
| quant-knowledge | skills/quant-knowledge/ | 量化知识 | configs/ + memory/lessons/ |

## 4. 数据流（典型路径）

```
1. etf-daily skill 入口
2. 加载 ETF 池（universe.ETFListLoader）
3. 数据健康检查（monitor.DataHealthMonitor）
4. 加载策略（alpha.C21Strategy）
5. 计算因子（alpha.factors.27）
6. 评估持仓（risk.PositionGuide）
7. 决策快照（data_layer.decision_snapshot）
8. 推送通知（notify.SignalNotifier + ScenarioAdapter）
```

## 5. 关键设计原则

1. **数据层唯一入口**（规则 15）：业务层零 SQL，所有数据访问通过 data_layer
2. **Repository 模式**：每个表对应一个 Repository
3. **Protocol 接口契约**：5 个 Protocol（DataLoader/Indicator/Selector/Report/Fetcher）
4. **配置外置**（12-Factor）：constants.py + configs/*.json/yaml
5. **测试金字塔**：unit + integration + regression + benchmark

## 6. 业界参考

| 实践 | 来源 | v2 应用 |
|------|------|---------|
| Strangler Fig | Fowler 2004 | 5 模块从 v1 继承 |
| Repository Pattern | Evans 2003 | 4 Repo（trade_history/position/decision_snapshot/etf_names）|
| 12-Factor | Heroku 2011 | config 外置 + 声明式 |
| WFO | López de Prado 2018 | ComprehensiveValidator |
| 27 因子库 | WorldQuant 101 Alphas (Kakushadze 2016) | alpha/factors/ |

## 7. Sprint 演进

| Sprint | 模块完成度 |
|--------|:---:|
| Sprint-0/1 | 机制 + 接口契约 |
| Sprint-2/3 | alpha + execution + risk + backtest |
| Sprint-4 | 5 skill 入口 |
| Sprint-5 | 文档 + 迁移 + CI |
| Sprint-6 | 27 因子（alpha 完整化）|
| **Sprint-7** | **5 模块业务完整化**（universe/scheduler/monitor/performance/notify）+ portfolio |
