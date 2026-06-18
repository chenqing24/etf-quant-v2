# ETF 量化投资策略 v2

> AI-Native 量化认知升级教育产品
> 基于 v1 30 天（2026-05-18 → 06-18）调研演进

## 状态

🚧 **v2.0 重构中** —— Sprint-0（基础设施）启动

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
├── src/etf_quant/     # 12 模块
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
│   └── utils/         # 工具
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