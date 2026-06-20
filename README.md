# ETF 量化投资策略 v2

> AI-Native 量化认知升级教育产品
> 基于 v1 30 天（2026-05-18 → 06-18）调研演进

> **🤖 AI Agent 必读**：本项目根目录的 [AGENTS.md](AGENTS.md) 和 [CLAUDE.md](CLAUDE.md) 是给 AI 看的协作指南，**包含 v1 → v2 迁移说明、SKILL 路由、数据访问约定、禁止事项**。新 AI 来这里请先读 AGENTS.md。

## 状态

✅ **v2.0 已发布 v2.0-final** —— Sprint-0~7 全部完成，**业务实现 100%（29/29 US）**

| 维度 | 数值 |
|------|-----:|
| Sprint | 0/1/2/3/4/5/6/7 全完成 |
| US（业务实现）| **29/29 = 100%** |
| 测试 | 217/217 全过 + 5 benchmark |
| 8 维自检 | 100/100 |
| Tag | `v2.0-final` + `sprint-7-complete` + `v1-deprecated-v2-refactor`（v1 归档） |

## 触发词与 SKILL 路由

| 用户意图 | 触发词 | v2 skill |
|----------|--------|----------|
| 每日决策 | "ETF 决策" / "跑 ETF" / "ETF 每日检查" | `etf-daily` |
| 回测验证 | "ETF 回测" / "ETF 验证" / "ETF 评分" | `etf-research` |
| 量化知识 | "量化策略" / "量化教训" / "业界参考" | `quant-knowledge` |
| 个股分析 | "个股分析" / "股票 vs 板块" | `stock-analyze` |
| 持仓组合 | "持仓组合" / "再平衡" / "业绩归因" | `stock-portfolio` |

**v1 已废弃**：`etf-quant-decision` skill 已备份为 `etf-quant-decision-v1-DEPRECATED`，v1 本地仓已删除（GitHub 保留为历史归档，tag `v1-deprecated-v2-refactor`）。

**完整迁移指南**：[v1 GitHub V1_TO_V2_MIGRATION.md](https://github.com/chenqing24/etf-quant-strategy/blob/main/docs/V1_TO_V2_MIGRATION.md)

**新用户上手**：

| 版本 | 适用人群 | 文档 |
|------|---------|------|
| 👤 **散户投资者版** | 不会代码，跟 AI 说话即可 | [`docs/NEW_USER_GUIDE_INVESTOR.md`](docs/NEW_USER_GUIDE_INVESTOR.md) ⭐ |
| 💻 **技术版** | 开发者，跑命令验证 | [`docs/NEW_USER_GUIDE.md`](docs/NEW_USER_GUIDE.md) |

## 核心定位

- **v1 旧代码** = 考古资料（`etf_strategy/`），不污染 v2
- **v2 设计** = 单仓 monorepo + 12 模块 + 5 skill
- **目标用户** = C 端散户"想学方"（Q1 已拍板）
- **范式** = AI-Native（非 AI-Assisted）

## 调研基础

调研汇总：`v2-roadmap/00_evolution_review.md`（23KB，12 节）
分批笔记：`v2-roadmap/notes/01~12_*.md`（1710 行）
方法论：`v2-roadmap/10_research_plan.md`

## 项目结构

```
etf_quant_v2/
├── docs/              # 文档
│   ├── PRD.md         # 产品需求
│   ├── ARCHITECTURE.md # 架构
│   ├── INTERFACE_CONTRACT.md # 数据契约
│   └── SOP_*.md       # 标准流程
├── src/etf_quant/     # 13 模块（含 2 个工具）
│   ├── data_layer/    # 数据层（v1 继承）
│   ├── universe/      # 股票池
│   ├── alpha/         # 因子 / 信号
│   ├── portfolio/     # 仓位 / 组合
│   ├── risk/          # 风控
│   ├── execution/     # 执行
│   ├── backtest/      # 回测
│   ├── performance/   # 绩效
│   ├── notify/        # 通知
│   ├── config/        # 配置
│   ├── monitor/       # 监控
│   ├── scheduler/     # 调度
│   └── utils/         # 工具（含 execution_source）
├── skills/            # 5 skill 入口
│   ├── etf-daily/
│   ├── etf-research/
│   ├── stock-analyze/
│   ├── stock-portfolio/
│   └── quant-knowledge/
├── tests/             # 测试金字塔
├── schema/migrations/ # 数据库迁移
├── configs/           # 配置文件
├── data/              # 运行时数据（gitignore）
└── scripts/           # 工具脚本（含腐化自检）
```

> **注**：`v2-roadmap/notes/01~12_*.md`（1710 行）等调研笔记在 workspace 根目录，不在 v2 仓内（避免仓过大）。详见 `docs/AUDIT_REPORT_20260620.md`。

## 执行规范

按 **SOP-02 重构与修复开发流程**（来自 v1）：
1. Phase 1: 问题发现
2. Phase 2: 根因分析
3. Phase 3: 方案设计
4. **Phase 4: 小步提交（每个 US 一个 commit）**
5. Phase 5: 验证测试
6. Phase 6: 复盘交付

每次 commit 必带：
1. **背景**：解决什么问题
2. **改动**：改了哪些文件
3. **对比计划**：与 CHECKPOINT.md 对比
4. **自评**：6 维自检（规则 6.2）
5. **下一步**：明确行动

## 关键教训（v1 沉淀）

详见 `v2-roadmap/notes/10_lessons_curated.md`

**金 5 教训**：
- L211：机制层 > AI 自觉
- L225：alpha 真实来源（不是 4 因子，是入场过滤 + 永远满仓）
- L222：cron 推送分流（target-session=WoXtGw==）
- L101：多执行源无标识
- L209：8 维度腐化自检

## 进度

详见 `missions/mission-20260618-234155/progress.txt`

---

> 最后更新：2026-06-18
> 启动者：月海巫师 + 福猫管家 🐱