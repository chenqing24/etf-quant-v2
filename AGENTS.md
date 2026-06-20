# AGENTS.md — 跨 AI 协作指南

> **如果你是 AI Agent（Claude Code / Cursor / Continue / Cline / Aider / GitHub Copilot / Windsurf / Warp / QwenPaw 等），请先读本文件。**

---

## 一、项目身份

- **本项目**：`etf_quant_v2`（v2.0.0a1）—— ETF 量化投资策略 v2 重构版
- **前身**：`etf_strategy`（v1，已废弃）—— 本地仓已删除，GitHub 保留为历史归档
- **本地路径**：`/home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/`
- **GitHub**：https://github.com/chenqing24/etf-quant-strategy （v1 仓，tag `v1-deprecated-v2-refactor` 标记归档）
- **v2 GitHub**：（待创建）https://github.com/chenqing24/etf-quant-v2

---

## 二、v1 → v2 关键变化

| 维度 | v1（已废弃） | v2（当前） |
|------|-------------|-----------|
| 因子数量 | 7 因子 | 27 因子 + W4 RV |
| 业务模块 | 50+ 文件散落 | 13 模块（alpha/portfolio/risk/notify/data_layer/universe/scheduler/monitor/performance/utils） |
| 数据层 | 多源（CSV + SQLite + 自定义） | SQLite 唯一（`data/etf.db`）+ DataLoader/DataWriter 统一入口 |
| 测试 | ~50 E2E（依赖网络） | 217/217（unit/integration/regression）+ 5 benchmark |
| SKILL | 1 个（`etf-quant-decision`） | 5 个（etf-daily/etf-research/quant-knowledge/stock-analyze/stock-portfolio） |
| 业务完整性 | 接口契约 | 100% 业务实现（29/29 US） |

**完整迁移说明**：[`docs/V1_TO_V2_MIGRATION.md`](../etf_strategy/docs/V1_TO_V2_MIGRATION.md)（v1 仓 GitHub 保留）

---

## 三、AI Agent 调用"ETF 策略"的工作流

### 3.1 触发词与 skill 路由

当用户说"ETF 决策"/"跑 ETF"/"ETF 每日检查"/"ETF 回测" 等：

| 用户意图 | 触发 skill | skill 路径 |
|----------|------------|-----------|
| 每日决策 / 跑 ETF | `etf-daily` | `~/.qwenpaw/workspaces/default/skills/etf-daily/`（软链接到 v2） |
| ETF 回测 / 验证 / 评分 | `etf-research` | `~/.qwenpaw/workspaces/default/skills/etf-research/` |
| 量化策略 / 教训 | `quant-knowledge` | `~/.qwenpaw/workspaces/default/skills/quant-knowledge/` |
| 个股 vs 板块 vs 大盘 | `stock-analyze` | `~/.qwenpaw/workspaces/default/skills/stock-analyze/` |
| 持仓组合 / 再平衡 | `stock-portfolio` | `~/.qwenpaw/workspaces/default/skills/stock-portfolio/` |

**v1 残留**（已废弃）：`etf-quant-decision-v1-DEPRECATED/`（不再使用）

### 3.2 标准调用方式

```bash
# 每日决策
python ~/.qwenpaw/workspaces/default/skills/etf-daily/scripts/run_daily.py daily

# 回测验证
python ~/.qwenpaw/workspaces/default/skills/etf-research/scripts/run_validate.py

# 量化知识查询
python ~/.qwenpaw/workspaces/default/skills/quant-knowledge/scripts/run_query.py
```

### 3.3 直接调用 v2 仓（高级用法）

```bash
cd /home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2
python -m etf_quant.cli.main [command]
```

---

## 四、AI Agent 必读文档

按优先级：

1. **[README.md](README.md)**（3712 字节）—— 项目概览 + 快速开始
2. **[QUICKSTART.md](QUICKSTART.md)**（2233 字节）—— 5 分钟上手
3. **[docs/PRD.md](docs/PRD.md)** —— 29 个 US + 7 个 Sprint 全景
4. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** —— 12 模块依赖图
5. **[docs/INTERFACE_CONTRACT.md](docs/INTERFACE_CONTRACT.md)** —— 模块接口
6. **[docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md)** —— 数据字段
7. **[CHANGELOG.md](CHANGELOG.md)** —— 变更历史
8. **[docs/MISSION_FINAL_REPORT_20260620.md](docs/MISSION_FINAL_REPORT_20260620.md)** —— Mission 最终报告

---

## 五、AI Agent 工作约定

### 5.1 数据访问

- **唯一数据源**：`data/etf.db`（SQLite）
- **统一读取入口**：`from etf_quant.data_layer.loader import DataLoader`
- **统一写入入口**：`from etf_quant.data_layer.writer import DataWriter`
- **禁止**：直接 `pd.read_csv()`、`sqlite3.connect()` 绕过统一入口

### 5.2 测试要求

- **测试总数**：217/217 全过
- **测试类型**：unit（159）+ integration（32）+ regression（26）
- **运行测试**：`pytest tests/ -v`
- **8 维自检**：`python scripts/腐化自检.py`

### 5.3 提交规范

- **COMMIT 模板**：[COMMIT_TEMPLATE.md](COMMIT_TEMPLATE.md)（5 段格式：背景/改动/对比/自评/下一步）
- **小步提交**：每个有意义的修改立即 commit
- **pre-commit 钩子**：必须通过
- **诚实声明**：自评分数不美化

### 5.4 因子实现

- **位置**：`src/etf_quant/alpha/factors/`
- **基类**：`factor_base.py`（FactorBase 抽象类）
- **注册**：`registry.py`（27 因子 + W4 RV）
- **新因子**：继承 FactorBase + register + 单元测试

---

## 六、禁止事项（红线）

| ❌ 禁止 | ✅ 正确做法 |
|---------|------------|
| 直接读 CSV 文件作为数据源 | 用 DataLoader 查 SQLite |
| 多模块各自写库 | 统一通过 DataWriter |
| 凭"我以为"推断行为 | 看 `is_real`/`emotion`/`reason` 等标识字段 |
| 自评 100 分实际 45 分 | 按规则 6.2 诚实打分 |
| 跳过 SOP 跨模块修复 | 走完所有 Phase |
| 改 .gitignore 不记录教训 | 记入 MEMORY.md |

---

## 七、SOP 索引

| 编号 | 主题 | 路径 |
|------|------|------|
| SOP_01 | 数据采集 | [docs/SOP_01_DATA.md](docs/SOP_01_DATA.md) |
| SOP_02 | 重构与修复开发 | [docs/SOP_02_REFACTOR_DEV.md](docs/SOP_02_REFACTOR_DEV.md) |
| SOP_03 | 实验流程 | [docs/SOP_03_EXPERIMENT.md](docs/SOP_03_EXPERIMENT.md) |
| SOP_04 | 数据源接入 | [docs/SOP_04_DATASOURCE.md](docs/SOP_04_DATASOURCE.md) |
| SOP_05 | 备份与恢复 | [docs/SOP_05_BACKUP.md](docs/SOP_05_BACKUP.md) |
| SOP_06 | 脱敏 | [docs/SOP_06_DESENSITIZE.md](docs/SOP_06_DESENSITIZE.md) |
| SOP_07 | Mission 流程 | [docs/SOP_07_MISSION.md](docs/SOP_07_MISSION.md) |

---

## 八、跨会话记忆

- **MEMORY.md**（v2 仓根）：v2 项目长期记忆（教训/决策/上下文）
- **PROFILE.md**（v2 仓根）：用户资料（偏好/习惯/背景）

---

## 九、参考来源

- v1 仓归档说明：https://github.com/chenqing24/etf-quant-strategy/blob/main/README.md
- v1 迁移指南：https://github.com/chenqing24/etf-quant-strategy/blob/main/docs/V1_TO_V2_MIGRATION.md
- v1 最终快照：https://github.com/chenqing24/etf-quant-strategy/releases/tag/v1-deprecated-v2-refactor
- v1 完整版备份：`/home/qwenpaw/.qwenpaw/workspaces/default/etf_strategy_v1_full_backup_20260620.zip`（83.2MB）

---

**AI Agent 读完本文档后，建议先 `ls` v2 仓根目录 + 读 README.md + 读 QUICKSTART.md 即可开始工作。**
