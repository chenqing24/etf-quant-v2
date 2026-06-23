# 迭代计划 v1（2026-06-23 mission-20260623-072239 Phase 7 输出）

> **生成时间**：2026-06-23 10:30
> **生成者**：福猫管家 🐱（按用户指令"从头 review 整个项目"）
> **模式**：自动模式（用户已下线）
> **依据**：SOP-02 重构 + SOP-03 实验 + 业界最佳实践对照

---

## 0. Review 范围与方法

### 0.1 范围

| 维度 | 内容 | LOC |
|---|---|---|
| **代码** | `etf_quant_v2/src/etf_quant/` 12 模块 | 4756 |
| **测试** | `etf_quant_v2/tests/` 单元/集成/回归 | 29 文件 |
| **文档** | `etf_quant_v2/docs/` Divio 4 类 + 7 SOP | 39 文件 |
| **根仓** | `skills/` 53 skill | 53 文件 |
| **Mission** | `missions/mission-20260623-072239/` | 12 US |
| **总计** | 全栈 | 4756+ 代码 LOC |

### 0.2 方法

按业界 8 维自评（规则 6.3）+ 业务自评（规则 24）+ 9 大业界最佳实践对照。

### 0.3 业界参考

| # | 实践 | URL | 用途 |
|---|------|-----|------|
| 1 | Divio Documentation Guide | https://docs.divio.com/documentation-guide/ | 文档 4 类 |
| 2 | Twelve-Factor App | https://12factor.net/ | 架构 12 要素 |
| 3 | OpenSSF Best Practices | https://bestpractices.coreinfrastructure.org/ | 安全 + 治理 |
| 4 | Bloom's Taxonomy | https://en.wikipedia.org/wiki/Bloom%27s_taxonomy | 教学 |
| 5 | Kirkpatrick Model | https://en.wikipedia.org/wiki/Kirkpatrick_model | 评估 |
| 6 | Fogg Behavior Model | https://en.wikipedia.org/wiki/Fogg_behavior_model | 用户行为 |
| 7 | Dieter Rams 10 Principles | https://en.wikipedia.org/wiki/Dieter_Rams | 设计 |
| 8 | DORA Metrics | https://dora.dev/ | 部署效能 |
| 9 | Google SRE Book | https://sre.google/sre-book/monitoring-distributed-systems/ | 监控 |

---

## 1. Review 发现（按严重度排序）

### 🔴 P0（必修，否则影响业务正确性）

| # | 问题 | 位置 | 业务影响 | 教训 |
|---|------|------|----------|------|
| P0-1 | `test_onboard_validation::test_alpha_pass` 失败：FACTOR_REGISTRY 不含 `user_factor` | `tests/unit/test_onboard_validation.py:56` | onboard 测试脏数据，新会话必失败 | **L296** onboard 测试不应依赖外部状态 |
| P0-2 | `run_daily.py` 硬编码 `market_mode = "range_bound"` | `skills/etf-daily/scripts/run_daily.py:60` | 决策市场环境永远震荡市，与规则 22 矛盾 | **L297** market_mode 必须是外部检测 |
| P0-3 | README 写 `217/217 tests pass`，但实测 `15/16 + 1 fail` | `etf_quant_v2/README.md` | 数据失真，下游 Mission 误判 | **L298** README 数据需每次测试后更新 |

### 🟠 P1（应修，影响项目质量）

| # | 问题 | 位置 | 业务影响 | 教训 |
|---|------|------|----------|------|
| P1-1 | **无 GitHub Actions CI** | `etf_quant_v2/.github/` 只有 ISSUE_TEMPLATE | 无自动化质量门 | **L304** 需补 CI |
| P1-2 | **无 Dockerfile / Procfile** | `etf_quant_v2/` 根 | Twelve-Factor V/XII 缺 | **L305** 容器化缺失 |
| P1-3 | **6 个模块 `__init__.py` 为空** | data_layer/risk/execution/backtest/config/utils | 公开 API 未文档化 | **L306** 补 API 暴露 |
| P1-4 | **8 个 `print()` 散落** | data_layer/universe/alpha | Twelve-Factor XI 缺统一日志 | **L307** 收敛到 logging |
| P1-5 | **4 个 `except:`** | data_layer/monitor.py + loader.py | 吞掉所有异常 | **L302** 精确异常类型 |
| P1-6 | **README 触发词表缺 stock-analyze/portfolio** | `etf_quant_v2/README.md:24-29` | 5 skill 路由表不全 | 文档同步 |
| P1-7 | **无 Makefile / 入口脚本** | etf_quant_v2/ 根 | 操作入口散落 | **L308** 加 Makefile |

### 🟡 P2（可延，影响长期可维护性）

| # | 问题 | 位置 | 业务影响 | 教训 |
|---|------|------|----------|------|
| P2-1 | 根仓 `quant-trading` 与子仓 `quant-knowledge` 重复 | `skills/quant-trading/` | 重复实现 | **L299** 清理遗留 |
| P2-2 | 根仓有 9 个中文名遗留 skill | `skills/股票分析/` 等 | 与 v2 主题相关但未迁移 | **L300** 保留但不再扩展 |
| P2-3 | `tests/` 合并跑卡死（pytest 8.x bug） | `tests/` | 无法一次性验证 | **L309** pytest conftest 调查 |
| P2-4 | 无 `mypy` / `ruff` 实际跑过 CI 记录 | 无 | linter 配置未生效 | **L310** linter 集成 CI |
| P2-5 | AGENTS.md 路径 `（待创建）` 标注未更新 | `etf_quant_v2/AGENTS.md` | 文档与现实不一致 | 路径同步 |

---

## 2. 迭代路线图（按 5 大主题）

### 🎯 Theme 1：补齐 P0 真问题（30 min 即可）

**Mission 编号**：`mission-20260624-080000-iteration-v1-p0`

| Sprint | US | 内容 | 文件 |
|--------|----|----|------|
| Sprint 1 | US-001 | 修复 onboard 测试脏数据（mock FACTOR_REGISTRY） | `tests/unit/test_onboard_validation.py` |
| Sprint 1 | US-002 | 真实接入 market_mode 检测（基于 MA20/MA60/ATR） | `skills/etf-daily/scripts/run_daily.py` + `data_layer/monitor.py` |
| Sprint 1 | US-003 | 跑全测试 → 更新 README 数字 | `etf_quant_v2/README.md` |

**预期成果**：3 个 P0 关闭，README 数据真实

### 🏗️ Theme 2：CI/CD + 容器化（半天）

**Mission 编号**：`mission-20260625-090000-iteration-v1-cicd`

| Sprint | US | 内容 | 业务自评 |
|--------|----|----|----------|
| Sprint 1 | US-001 | GitHub Actions CI（pytest + coverage + ruff + mypy） | 端到端 0→25 |
| Sprint 2 | US-002 | Dockerfile（python:3.11-slim）+ docker-compose | 部署效率 |
| Sprint 3 | US-003 | Makefile（make test / make lint / make run） | 入口统一 |

**预期成果**：Twelve-Factor V/XII 满足，DORA 4 指标可测

### 📚 Theme 3：API 文档化 + 日志收敛（半天）

**Mission 编号**：`mission-20260626-100000-iteration-v1-api`

| Sprint | US | 内容 |
|--------|----|----|
| Sprint 1 | US-001 | 补 6 个空 `__init__.py`（暴露 public API + docstring） |
| Sprint 2 | US-002 | 8 个 `print()` 改 `logger.info()` |
| Sprint 3 | US-003 | 4 个 `except:` 精确异常 + 加 `raise from` |

**预期成果**：OpenSSF "Public APIs documented" 100%、Twelve-Factor XI 100%

### 🧹 Theme 4：根仓清理（30 min）

**Mission 编号**：`mission-20260626-140000-iteration-v1-cleanup`

| Sprint | US | 内容 |
|--------|----|----|
| Sprint 1 | US-001 | `skills/quant-trading` 移到 `_archive_quant-trading-v1`（规则 21） |
| Sprint 2 | US-002 | 9 个中文名 skill 加 DEPRECATED 横幅（不删，按规则 21） |
| Sprint 3 | US-003 | 根仓 gitignore 加 browser/ 排除（避免 100MB 触发 L298 教训） |

**预期成果**：根仓污染清 50%

### 🧪 Theme 5：pytest 卡死调查（1 小时）

**Mission 编号**：`mission-20260627-150000-iteration-v1-pytest`

| Sprint | US | 内容 |
|--------|----|----|
| Sprint 1 | US-001 | conftest.py 排查：是否有 session-scope 阻塞 |
| Sprint 2 | US-002 | 拆 conftest.py → 改 per-test fixture |
| Sprint 3 | US-003 | 加 `--random-order` 验证非确定性 |

**预期成果**：所有测试可一次性跑通

---

## 3. 业务自评（10 维度 250 分）

按规则 24 + v3 mission 9 维度 + Theme 5 增量 1 维度：

| 维度 | 当前 | 目标 | 差距 |
|---|---:|---:|---:|
| 数据完整性 | 24/25 | 25/25 | -1（P0-3 修后满分）|
| 结果合理性 | 22/25 | 25/25 | -3（P0-2 market_mode 真接入）|
| 端到端可跑 | 18/25 | 25/25 | -7（pytest 一次性跑 + 真跑命令）|
| 文档对得上 | 23/25 | 25/25 | -2（README 数字真）|
| L298 README 真实 | - | 25/25 | Theme 1 加 |
| L304 CI/CD | - | 25/25 | Theme 2 加 |
| L306 API 文档 | - | 25/25 | Theme 3 加 |
| L308 入口统一 | - | 25/25 | Theme 2 加 |
| L302 异常精确 | - | 25/25 | Theme 3 加 |
| L309 pytest 稳定 | - | 25/25 | Theme 5 加 |
| **总计** | **87/100** | **250/250** | 5 个 Mission 跑完 |

---

## 4. 风险与依赖

| 风险 | 等级 | 应对 |
|------|:---:|------|
| 修复 P0 可能引入回归 | P1 | 跑全测试 + 24 unittest |
| Theme 2 CI 需要 GitHub token | P1 | 等用户提供 |
| Theme 5 pytest 调查可能找不出根因 | P2 | 转用 pytest-randomly 临时绕开 |
| Theme 4 清理可能误删有用 skill | P1 | 备份到 _archive 前先确认 |

---

## 5. 关键决策（推荐方案）

### 决策 1：P0 必修
- **是**：3 个 P0 直接动，不分批（30 min 内搞定）

### 决策 2：P1 主题化（不一起跑）
- **推荐**：按 Theme 2/3/4 拆 3 个 Mission，避免 Mission 太大失控

### 决策 3：P2 搁置
- **推荐**：等 P1 完成再决定（部分 P2 可能被 P1 顺手解决）

### 决策 4：是否引入 CI/CD
- **推荐**：Theme 2 优先（CI 是质量门，没 CI 所有后续 Mission 都无保障）

### 决策 5：是否清理根仓
- **推荐**：Theme 4 暂缓（用户已下线，决策风险高；按规则 21 备份即可恢复）

---

## 6. Mission 验收清单（每个 Theme 跑完跑）

- [ ] prd.json 全 US passes
- [ ] 业务自评 ≥ 80（每维度）
- [ ] business_check.py 全过
- [ ] Git 小步提交（按 6 Sprint）
- [ ] CHANGELOG.md 更新
- [ ] MEMORY.md 新教训沉淀
- [ ] 子仓 push

---

## 7. 不做的事（避免范围蔓延）

1. **不改业务策略**（C21 策略 / 持仓规则）—— 业务 Mission 范围
2. **不重写 v1 脚本**—— 物理删除完成
3. **不引入新框架**（FastAPI / Django 等）—— 暂时 CLI + cron
4. **不接 LLM 推理**—— 因子逻辑代码化，不靠 LLM

---

**作者**：福猫管家 🐱
**日期**：2026-06-23
**Mission**: mission-20260623-072239
**状态**：📋 计划已出，待用户确认执行顺序
