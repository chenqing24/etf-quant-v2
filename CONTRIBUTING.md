# 贡献指南

> 感谢您对 etf-quant-v2 项目的关注！本文档说明如何参与贡献。

---

## 一、行为准则

本项目采用 [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/) 简化版：

- **尊重他人**：不同意见请文明表达
- **专注技术**：争论基于数据和代码，不针对个人
- **建设性反馈**：提建议时给替代方案

---

## 二、如何贡献

### 2.1 报告 Bug

- 使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.md)
- 提供：复现步骤 / 预期行为 / 实际行为 / 环境信息（Python 版本 / 操作系统 / 依赖版本）
- 搜索现有 issue 避免重复

### 2.2 提议新功能

- 使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.md)
- 说明：使用场景 / 期望 API / 替代方案
- 大功能请先在 issue 讨论，再开 PR

### 2.3 提交代码

#### 工作流（按 v1 实践）

```
1. Fork 仓库到你的账号
2. 创建特性分支（git checkout -b feature/xxx 或 mission/xxx-yyy）
3. 按 SOP-02 流程开发（见 docs/SOP_02_REFACTOR_DEV.md）
4. 按 COMMIT_TEMPLATE.md 5 段格式写 commit
5. pre-commit 检查通过
6. push 到你的 fork
7. 创建 PR 到 chenqing24/etf-quant-v2 的 main 分支
8. PR 标题用 [v2] 前缀 + 简述（如 [v2] fix(alpha): W4 RV 公式修正）
9. PR 描述用 .github/PULL_REQUEST_TEMPLATE.md
10. 等待 CI 通过 + review
```

#### Commit 规范

格式：`<type>(<scope>): <subject>`（中文 ≤ 50 字）

类型：
- `feat` 新功能
- `fix` 修复 bug
- `docs` 文档
- `refactor` 重构
- `test` 测试
- `chore` 杂项

5 段格式：背景 / 改动 / 对比计划 / 自评 / 下一步（详见 [COMMIT_TEMPLATE.md](COMMIT_TEMPLATE.md)）

#### 代码规范

- **Python**：遵循 PEP 8 + ruff 配置（`pyproject.toml [tool.ruff]`）
- **类型注解**：必须（mypy strict mode）
- **docstring**：模块/类/函数必须有（按规则 13）
- **测试**：新功能必须有单元测试（覆盖率 ≥ 80%）
- **pre-commit**：必须通过（机制层拦截）

---

## 三、数据卫生（重要！）

### 3.1 不要提交的数据

- `data/etf.db`（业务数据，13M+）
- `data/experiments/`（实验数据）
- `etf_performance.json` / `etf_positions.json`（实盘数据）
- `*.db` / `*.db-journal` / `*.db-wal`
- `__pycache__/` / `.pytest_cache/` / `.benchmarks/`

**已通过 .gitignore 强制排除**，但请自觉遵守。

### 3.2 数据库变更

- **DDL 必须迁移到 `schema/`**：禁止直接改运行中的 `data/etf.db`
- **新增字段**：必须更新 schema + 写 migration 脚本
- **测试用 DB**：`tests/` 下用临时 db，跑完即删

### 3.3 业务库 vs 测试库

- 业务数据：`data/etf.db`（gitignore）
- 测试数据：`tests/fixtures/*.db`（入 git，作为标准 fixture）
- CI 用 fixture（`scripts/init_database.py` 初始化）

---

## 四、SOP 索引

| 编号 | 用途 | 路径 |
|------|------|------|
| SOP-01 | 数据采集 | [docs/SOP_01_DATA.md](docs/SOP_01_DATA.md) |
| SOP-02 | 重构与修复开发 | [docs/SOP_02_REFACTOR_DEV.md](docs/SOP_02_REFACTOR_DEV.md) |
| SOP-03 | 实验流程 | [docs/SOP_03_EXPERIMENT.md](docs/SOP_03_EXPERIMENT.md) |
| SOP-04 | 数据源接入 | [docs/SOP_04_DATASOURCE.md](docs/SOP_04_DATASOURCE.md) |
| SOP-05 | 备份与恢复 | [docs/SOP_05_BACKUP.md](docs/SOP_05_BACKUP.md) |
| SOP-06 | 脱敏 | [docs/SOP_06_DESENSITIZE.md](docs/SOP_06_DESENSITIZE.md) |
| SOP-07 | Mission 流程 | [docs/SOP_07_MISSION.md](docs/SOP_07_MISSION.md) |

---

## 五、版本号规范

按 [Semantic Versioning 2.0.0](https://semver.org/)：

- **MAJOR**：不兼容的 API 变更
- **MINOR**：向后兼容的功能新增
- **PATCH**：向后兼容的 bug 修复
- **预发布**：`-a1` / `-rc1` / `-beta.1` 等

当前版本：`2.0.0a1`（alpha 1）

---

## 六、问题求助

- **GitHub Issues**：https://github.com/chenqing24/etf-quant-v2/issues
- **项目主页**：https://github.com/chenqing24/etf-quant-v2
- **本地路径**：`/home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/`
- **AGENTS.md**：[AGENTS.md](AGENTS.md)（AI Agent 必读）

---

## 参考来源

- v1 CONTRIBUTING 不存在（v1 仓 zip 验证无）
- v1 PR 工作流：9 个 PR 全 merged（GitHub API 验证）
- v1 commit 风格：Angular（git log 验证）
- v1 SOP 体系：9 个 SOP（v1 SOP_INDEX.md）
- v2 继承 + 改进：v2 SOP_02 与 v1 SOP_02 流程一致
