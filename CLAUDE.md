# CLAUDE.md — Claude Code 协作指南

> **本文件给 Claude Code 看。AGENTS.md 是通用版本（本文件是 Claude 专用）。**

---

## 重要：这是 v2 项目

- **本项目**：`etf_quant_v2`（v2.0.0a1）
- **前身**：`etf_strategy`（v1，已废弃，本地仓已删除，GitHub tag `v1-deprecated-v2-refactor` 归档）
- **本地路径**：`/home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/`
- **完整迁移指南**：[AGENTS.md](AGENTS.md)（必读）+ [v1 GitHub V1_TO_V2_MIGRATION.md](https://github.com/chenqing24/etf-quant-strategy/blob/main/docs/V1_TO_V2_MIGRATION.md)

---

## Claude Code 工作流

### 1. 接到 ETF 相关任务时

**先扫这个目录**：
```
~/.qwenpaw/workspaces/default/skills/
├── etf-daily/         ← "ETF 决策" / "跑 ETF" / "ETF 每日检查"
├── etf-research/      ← "ETF 回测" / "ETF 验证" / "ETF 评分"
├── quant-knowledge/   ← "量化策略" / "量化教训"
├── stock-analyze/     ← "个股分析"
├── stock-portfolio/   ← "持仓组合"
└── etf-quant-decision-v1-DEPRECATED/  ← 不用，v1 已废弃
```

5 个 v2 skill 软链接到 `etf_quant_v2/skills/`。

### 2. 标准工具调用

```bash
# 每日决策
python ~/.qwenpaw/workspaces/default/skills/etf-daily/scripts/run_daily.py daily

# 回测
python ~/.qwenpaw/workspaces/default/skills/etf-research/scripts/run_validate.py

# v2 仓内直接调用
cd /home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2
python -m etf_quant.cli.main
```

### 3. 数据访问约定

- **唯一数据源**：`data/etf.db`（SQLite）
- **统一入口**：
  ```python
  from etf_quant.data_layer.loader import DataLoader
  from etf_quant.data_layer.writer import DataWriter
  ```
- **禁止**：`pd.read_csv()` 或 `sqlite3.connect()` 绕过

### 4. 测试与自检

```bash
cd /home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2
pytest tests/ -v                     # 217/217 测试
python scripts/腐化自检.py            # 8 维自检 100/100
```

### 5. 提交规范

- **5 段格式**（背景/改动/对比/自评/下一步）：参考 [COMMIT_TEMPLATE.md](COMMIT_TEMPLATE.md)
- **小步提交**：每个有意义的修改立即 commit
- **诚实自评**：按规则 6.2 真实打分，不美化

---

## Claude Code 必读文件

按顺序：

1. [README.md](README.md)——项目概览
2. [QUICKSTART.md](QUICKSTART.md)——5 分钟上手
3. [docs/PRD.md](docs/PRD.md)——29 US + 7 Sprint
4. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)——模块依赖
5. [CHANGELOG.md](CHANGELOG.md)——变更历史

---

## 红线（绝对禁止）

| ❌ 禁止 | 后果 |
|---------|------|
| 把 v1 当成当前项目 | 会运行 v1 的旧代码（已删除） |
| 直接读 CSV | 违反规则 15（数据源统一） |
| 跳过测试就交付 | 违反规则 5（先测试再交付） |
| 自评 100 分实际 45 分 | 违反规则 6.1（不美化） |
| 跨模块修复不输出设计 | 违反规则 4（先设计后实现） |

---

## 关键决策记录

- **v1 → v2 重构模式**：Strangler Fig（Fowler 2004）—— v2 仓从 v1 仓继承因子代码（22 个继承因子）+ 重写 4 模块 + 新增 6 模块
- **数据层架构**：DataWriter + DataLoader + SQLite（v3.0 统一数据入口）
- **业务实现标准**：29/29 US 100% 完成（Sprint-7 业务完整化）

---

**完整 AGENTS.md**：[AGENTS.md](AGENTS.md)
**SOP 索引**：见 AGENTS.md 第七节
