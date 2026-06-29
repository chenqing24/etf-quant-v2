# ETF 量化投资策略 v2

> **AI-Native 量化认知升级教育产品**
> 基于 v1 30 天（2026-05-18 → 06-18）调研演进

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 424/424](https://img.shields.io/badge/Tests-424%2F424-brightgreen)](tests/)
[![Sprint: 8.2](https://img.shields.io/badge/Sprint-8.2-blue)](docs/sprint-reviews/)
[![v2.0-final](https://img.shields.io/badge/version-v2.0--final-orange)](CHANGELOG.md)

> **🤖 AI Agent 必读**：本项目根目录的 [AGENTS.md](AGENTS.md) 和 [CLAUDE.md](CLAUDE.md) 是给 AI 看的协作指南，**包含 v1 → v2 迁移说明、SKILL 路由、数据访问约定、禁止事项**。新 AI 来这里请先读 AGENTS.md。

## 状态

✅ **v2.0 已发布 v2.0-final** —— Sprint-0~8.2 全部完成，**业务实现 100%（29/29 US）**

| 维度 | 数值 | 状态 |
|------|-----:|:----:|
| Sprint | 0/1/2/3/4/5/6/7/8/8.1/8.2 全完成 | ✅ |
| US（业务实现）| **29/29 = 100%** | ✅ |
| 单元测试 | **424/424 全过**（45 文件，2026-06-29 实测）| ✅ |
| 1 已知失败 | D-013.3 test_run_eval（Sprint 1.1 待修）| ⚠️ |
| 业务自评 4 维度 | 脚本待建（Sprint 0.1）| ⚠️ |
| Tag | `v2.0-final` + `sprint-7-complete` + `v1-deprecated-v2-refactor`（v1 归档）| - |

> **测试覆盖说明（L296 教训）**：所有 onboard 校验测试已重构为 fixture 隔离（不依赖生产 state.json / etf.db），新会话/新用户必过。合并跑 pytest 仍卡死（Theme 5 待修，单文件全过）。

## 触发词与 SKILL 路由

| 用户意图 | 触发词 | v2 skill |
|----------|--------|----------|
| 每日决策 | "ETF 决策" / "跑 ETF" / "ETF 每日检查" | `etf-daily` |
| 回测验证 | "ETF 回测" / "ETF 验证" / "ETF 评分" | `etf-research` |
| 量化知识 | "量化策略" / "量化教训" / "业界参考" | `quant-knowledge` |
| 个股分析 | "个股分析" / "股票 vs 板块" | `stock-analyze` |
| 持仓组合 | "持仓组合" / "再平衡" / "业绩归因" | `stock-portfolio` |

**v1 已废弃**：`etf-quant-decision` skill 已备份为 `etf-quant-decision-v1-DEPRECATED`，v1 本地仓已删除（GitHub 保留为历史归档，tag `v1-deprecated-v2-refactor`）。

**完整迁移指南**：[v1 GitHub V1_TO_V2_MIGRATION.md](https://github.com/chenqing24/etf-quant-strategy/blob/main/docs/V1_TO_V2_MIGRATION.md)（v1 仓历史归档）

**新用户上手**：

| 版本 | 适用人群 | 文档 |
|------|---------|------|
| 🗺️ **用户地图** | 不确定看哪份？看这张图 | [`docs/USER_JOURNEY_MAP.md`](docs/USER_JOURNEY_MAP.md) ⭐ |
| 👤 **散户投资者版** | 不会代码，跟 AI 说话即可 | [`docs/NEW_USER_GUIDE_INVESTOR.md`](docs/NEW_USER_GUIDE_INVESTOR.md) |
| 💻 **技术版** | 开发者，跑命令验证 | [`docs/NEW_USER_GUIDE.md`](docs/NEW_USER_GUIDE.md) |

## 核心定位

- **v1 旧代码** = 考古资料（`etf_strategy/`），不污染 v2
- **v2 设计** = 单仓 monorepo + **14 模块** + 5 skill
- **目标用户** = C 端散户"想学方"（Q1 已拍板）
- **范式** = AI-Native（非 AI-Assisted）

## 调研基础

调研汇总：`v2-roadmap/00_evolution_review.md`（23KB，12 节）
分批笔记：`v2-roadmap/notes/01~12_*.md`（1710 行，**在 workspace 根目录不在 v2 仓**）
方法论：`v2-roadmap/10_research_plan.md`

## 项目结构

```
etf_quant_v2/
├── docs/              # 文档（54 份）
│   ├── PRD.md         # 产品需求
│   ├── ARCHITECTURE.md # 架构
│   ├── INTERFACE_CONTRACT.md # 数据契约
│   ├── ROADMAP_v3.md  # v3.0 路线图（Phaal + Shape Up）
│   ├── USER_JOURNEY_MAP.md # 用户地图
│   └── SOP_*.md       # 标准流程（SOP_01~08）
├── src/etf_quant/     # 14 模块
│   ├── data_layer/    # 数据层（v1 继承，10 Repo）
│   ├── universe/      # ETF 池
│   ├── alpha/         # 因子 / 信号（29 因子 + 3 层架构）
│   ├── portfolio/     # 仓位 / 组合
│   ├── risk/          # 风控（22 字段 9 步）
│   ├── execution/     # 执行（委托 4 Repo）
│   ├── backtest/      # 回测（ComprehensiveValidator）
│   ├── performance/   # 绩效
│   ├── notify/        # 通知（钉钉）
│   ├── config/        # 配置
│   ├── monitor/       # 监控（market_mode 等）
│   ├── scheduler/     # 调度
│   ├── utils/         # 工具
│   └── rank/          # 排名
├── skills/            # 5 skill 入口
│   ├── etf-daily/
│   ├── etf-research/
│   ├── stock-analyze/
│   ├── stock-portfolio/
│   └── quant-knowledge/
├── tests/             # 测试金字塔（45 文件 / 424 用例）
├── schema/migrations/ # 数据库迁移
├── configs/           # 配置文件
├── data/              # 运行时数据（gitignore）
└── scripts/           # 工具脚本（含腐化自检 + 业务自评待建）
```

> **注**：`v2-roadmap/notes/01~12_*.md`（1710 行）等调研笔记在 workspace 根目录，不在 v2 仓内（避免仓过大）。详见 `docs/AUDIT_REPORT_20260620.md`。

## 完整文档索引

| 类别 | 文档 | 说明 |
|------|------|------|
| **变更** | [CHANGELOG.md](CHANGELOG.md) | 版本变更记录 |
| **法律** | [LICENSE](LICENSE) | MIT 协议 |
| **贡献** | [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| **行为** | [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | 行为准则 |
| **安全** | [SECURITY.md](SECURITY.md) | 漏洞报告流程 |
| **需求** | [docs/PRD.md](docs/PRD.md) | 产品需求 |
| | [docs/PRD.json](docs/PRD.json) | 结构化 29 US / 196 AC |
| **路线** | [docs/ROADMAP_v3.md](docs/ROADMAP_v3.md) | v3.0 路线图（业界标准）|
| **架构** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系统架构（v1 时代，需更新）|
| | [docs/USER_JOURNEY_MAP.md](docs/USER_JOURNEY_MAP.md) | 用户旅程 |
| **接口** | [docs/INTERFACE_CONTRACT.md](docs/INTERFACE_CONTRACT.md) | 接口契约 |
| | [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) | 数据字典 |
| **SOP** | [docs/SOP_INDEX.md](docs/SOP_INDEX.md) | SOP 索引（8 份）|
| **新用户** | [docs/NEW_USER_GUIDE.md](docs/NEW_USER_GUIDE.md) | 技术版指南 |
| | [docs/NEW_USER_GUIDE_INVESTOR.md](docs/NEW_USER_GUIDE_INVESTOR.md) | 投资者版 |
| | [docs/QUICKSTART.md](docs/QUICKSTART.md) | 5 分钟上手 |
| | [docs/FAQ.md](docs/FAQ.md) | 常见问题 |

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

## 下一步路线图

按 [docs/ROADMAP_v3.md](docs/ROADMAP_v3.md)（Phaal + Shape Up 业界标准）：

**短段 1 周**（v3.0 v1）：
1. Sprint 0.1 建 `scripts/business_check.py`
2. Sprint 1.1 修 D-013.3 test_run_eval
3. Sprint 1.2 更新 README 测试数（**本 README 已更新**）
4. Sprint 1.3 跑业务自评拿真分
5. Sprint 2.1 D-012 HOLD 落 snapshot
6. Sprint 2.2 cron 09:30 工作日
7. Sprint 2.4 decision_snapshot 散户解释

**长段 6 周**（v3.0 完整）：见 ROADMAP_v3 §"Phase 3 Follow-up"

---

> 最后更新：2026-06-29
> 启动者：月海巫师 + 福猫管家 🐱
> 路线图方法论：Phaal 2004 + Shape Up 2019
