# MEMORY.md — v2 长期记忆

> AI Agent 必读。本文件是 v2 项目跨会话的长期记忆（教训/决策/上下文/工具设置）。

---

## 一、项目身份

- **本项目**：`etf_quant_v2`（v2.0.0a1）—— ETF 量化投资策略 v2 重构版
- **前身**：`etf_strategy`（v1）—— 已废弃，2026-06-20 归档
- **本地路径**：`/home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/`
- **服务对象**：月海巫师（AI 量化教育公司创始人，5 年 Python 全栈 DevOps）

---

## 二、v1 → v2 关键决策（不可妥协）

### 2.1 Strangler Fig 模式（Fowler 2004）
- v2 仓从 v1 仓**继承**因子代码（22 个继承因子），不重写
- **重写** 4 模块（data_layer/scheduler/monitor/notify 业务实现）
- **新增** 6 模块（universe/portfolio/risk/performance/config/utils）
- **总模块数**：13 个

### 2.2 数据源统一原则（规则 15）
- **唯一数据源**：`data/etf.db`（SQLite）
- **统一读取入口**：`DataLoader`（`src/etf_quant/data_layer/loader.py`）
- **统一写入入口**：`DataWriter`（`src/etf_quant/data_layer/writer.py`）
- **路由**：`DataSourceRouter`（`src/etf_quant/data_layer/router.py`）
- **禁止**：直接 `pd.read_csv()` 或 `sqlite3.connect()` 绕过

### 2.3 SKILL 拆分（v1 → v2）
- v1: 1 个 skill `etf-quant-decision`（混合 daily/eval/trade/history/perf）
- v2: 5 个 skill 拆分（etf-daily/etf-research/quant-knowledge/stock-analyze/stock-portfolio）
- 软链接位置：`~/.qwenpaw/workspaces/default/skills/<name> -> /home/qwenpaw/.qwenpaw/workspaces/default/etf_quant_v2/skills/<name>`

---

## 三、关键教训（v1 + Sprint-7 沉淀）

### 3.1 数据层
- **L15**：数据只存一份（SQLite），入口只有一个（DataSourceRouter）
- **L228**：先查再答，调研后必须标注来源
- **L244**：必须比较列名（数据源 schema 变更时）

### 3.2 重构
- **L246**：诚实声明（自评 100 → 实际 78 是教训）
- **L247**：US 前必须读 PRD 原始定义（避免"接口契约"和"业务实现"混淆）
- **L252**：依赖 v1 数据路径时显式传路径（ETFRepository DEFAULT_DB='etf_data_live/etf.db' 是 v1 残留，v2 用 `data/etf.db`）

### 3.3 工程
- **L241**：pre-commit 真实验证（不是装饰）
- **L255**：pre-commit 注释规则（"用途：/被谁调用：" 标准注释）
- **L256**：v2-roadmap 仓外管理（不在 v2 仓内）

### 3.4 AI 工作流（本 Mission 新增）
- **L257**：用户环境无 sudo 时，下载二进制首选 `urllib.request` + Python 自带库（避免 curl 下载超时）
- **L258**：fine-grained PAT 的 `push` ≠ `pull_requests:write`，创建 PR 需单独 scope
- **L259**：跨仓软链接用绝对路径，避免 `../../` 解析陷阱（验证方法：`readlink -f <link>`）

### 3.5 SKILL 路由
- QwenPaw 只扫描 `~/.qwenpaw/workspaces/default/skills/`，不扫描项目仓内子目录
- v2 skill 必须**软链接或拷贝**到 workspace skills/ 才能被 QwenPaw 调用
- v1 skill `etf-quant-decision` 已备份为 `etf-quant-decision-v1-DEPRECATED`

### 3.6 AI 发现机制（本 Mission 重要发现）
- **AI 不会主动到 v1 GitHub 查 README**（横幅只对主动查的人有效）
- **AI 第一眼看到的是项目根目录的引导文件**（AGENTS.md / CLAUDE.md / .cursorrules）
- v2 仓**之前没有 AI 引导文件**——本 Mission 修复（AGENTS.md + CLAUDE.md + README 更新）

---

## 四、工具设置

### 4.1 网络访问
- **国内网站**：直接访问（腾讯/新浪/天天基金/东方财富/百度百科）
- **国外网站**：必须走代理 `socks5://127.0.0.1:1080`
- **注意**：`~/.gitconfig` 强制全局代理，git 命令需 `git -c http.proxy= -c https.proxy=` 绕过

### 4.2 GitHub 凭据
- **账号**：chenqing24
- **PAT**：`GITHUB_PAT_REDACTED`
- **PAT 权限**：`{admin, maintain, push, triage, pull}` ✅
- **PAT 缺**：`pull_requests:write` ❌（创建 PR 需手动或升级 scope）
- **v1 仓**：`chenqing24/etf-quant-strategy`（548 commits + 8 tag + tag `v1-deprecated-v2-refactor`）
- **v2 仓**：（待创建）`chenqing24/etf-quant-v2`

### 4.3 数据源 API
- 腾讯行情：`https://qt.gtimg.cn`（限速 2 秒）
- 新浪行情：`https://hq.sinajs.cn`（限速 2 秒）
- AKTools：`http://127.0.0.1:8080`（本地服务，限速 5 秒）

---

## 五、关键数字

- **总 US**：29（US-030 已删 PyPI）
- **测试**：217/217 全过（unit 159 + integration 32 + regression 26）+ 5 benchmark
- **8 维自检**：100/100
- **Git commits**：53（v2 仓 main 分支）
- **总文件数**：171
- **Sprint 全景**：Sprint-0 (9 任务) + Sprint-1 (5) + Sprint-2/3 (4) + Sprint-4 (5) + Sprint-5 (5 + 1 暂停) + Sprint-6 (1) + Sprint-7 (5 业务实现)
- **Tags**：sprint-0/1/2-3/4/5/6/7-complete + v2.0-final + v2.0-pre-us001 + v1-deprecated-v2-refactor（v1 归档）

---

## 六、v1 备份位置

- **完整版 zip**：`/home/qwenpaw/.qwenpaw/workspaces/default/etf_strategy_v1_full_backup_20260620.zip`（83.2MB / 4542 文件）
- **v1 GitHub**：https://github.com/chenqing24/etf-quant-strategy（548 commits + 8 tag）
- **v1 标签**：`v1-deprecated-v2-refactor`（b2d3e8b）—— 标记归档
- **v1 早期备份**：`/home/qwenpaw/.qwenpaw/workspaces/default/etf_strategy_backup/`（412M，用户另一份，未删）

---

## 七、SOP 索引

| 编号 | 主题 | 路径 |
|------|------|------|
| SOP_01 | 数据采集 | `docs/SOP_01_DATA.md` |
| SOP_02 | 重构与修复开发 | `docs/SOP_02_REFACTOR_DEV.md` |
| SOP_03 | 实验流程 | `docs/SOP_03_EXPERIMENT.md` |
| SOP_04 | 数据源接入 | `docs/SOP_04_DATASOURCE.md` |
| SOP_05 | 备份与恢复 | `docs/SOP_05_BACKUP.md` |
| SOP_06 | 脱敏 | `docs/SOP_06_DESENSITIZE.md` |
| SOP_07 | Mission 流程 | `docs/SOP_07_MISSION.md` |

---

**最后更新**：2026-06-20（Mission 20260620-080956 完成）
**维护人**：福猫管家 🐱