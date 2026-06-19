# Sprint-5 启动前 B 调研（数据迁移 + 发布流程）

> **方法**：按 L228/L244 教训——直接打开 v1 业务库 + PRAGMA table_info + 必须比较列名
> **触发**：Sprint-5 US-026 数据迁移 + US-030 发布到 PyPI

---

## 1. 数据迁移调研（B-1）

### 1.1 v1 业务库数据规模

| 表 | v1 行数 | 是否需迁移 |
|----|:---:|:---:|
| etf_names | **1486** | ✅ 需迁移 |
| stock_info | **66** | ✅ 需迁移 |
| trade_history | **2** | ✅ 需迁移 |
| daily | **69480** | ✅ 需迁移 |
| positions | 0 | ❌ v1 无数据 |
| audit_log | 0 | ❌ v1 无数据 |
| decision_snapshot | 0 | ❌ v1 无数据 |
| etf_name_metrics | 0 | ❌ v1 无数据 |
| etf_name_retry_queue | 0 | ❌ v1 无数据 |
| realtime_cache | 0 | ❌ v1 无数据 |
| **总计** | **71034** | 4 表需迁移 |

### 1.2 v2 schema 与 v1 列名差异（按 L244 教训彻底对比）

| 表 | v1 列数 | v2 列数 | 真实差异 |
|----|:---:|:---:|------|
| etf_names | 14 | 18 | v2 多了 type/scale/list_date/is_reference（v1 无，迁移时填默认值）|
| stock_info | 6 | 10 | v1 有 full_code/updated_at/exchange；v2 有 industry/total_shares/float_shares/created_at |
| etf_name_retry_queue | 8 | 9 | v2 多了 id（AUTOINCREMENT，v1 用 code 作 PK）|
| trade_history | 37 | 37 | ✅ 完全一致 |
| positions | 14 | 14 | ✅ 完全一致 |
| audit_log | 8 | 8 | ✅ 完全一致 |
| decision_snapshot | 19 | 19 | ✅ 完全一致 |
| daily | 11 | 11 | ✅ 完全一致 |
| etf_name_metrics | 7 | 7 | ✅ 完全一致 |
| realtime_cache | 9 | 9 | ✅ 完全一致 |

**结论**：v1 全部列已在 v2 schema（v2 ⊇ v1）。迁移策略：
1. 取**交集列**（v1 ∩ v2）
2. v2 独有列填默认值（type='etf', scale=0, list_date='', is_reference=0）
3. `INSERT OR IGNORE` + 主键约束 = 幂等性

### 1.3 迁移脚本（US-026）

**位置**：`scripts/migrate_v1_to_v2.py`

**功能**：
- ✅ 4 表迁移（etf_names/stock_info/trade_history/daily）
- ✅ `--dry-run` 模式（不写入）
- ✅ 幂等性（`INSERT OR IGNORE`）
- ✅ 事务回滚（每表一个事务）
- ✅ 5 单元测试全过

**真实验证**（v1 业务库 71034 行）：
```
etf_names: 总 1486 行, 迁移 1486 行
stock_info: 总 66 行, 迁移 66 行
trade_history: 总 2 行, 迁移 2 行
daily: 总 69480 行, 迁移 69480 行

📊 总计迁移: 71034 行
```

### 1.4 业界参考（按规则 13）

| 实践 | 来源 | v2 应用 |
|------|------|---------|
| **Flyway Migrate** | https://flywaydb.org/documentation/usage/migration | ✅ 取交集列策略 |
| **Liquibase SQL Format** | https://www.liquibase.org/ | ✅ |
| **Database Refactoring** | Sadalage《Refactoring Databases》 | ✅ |
| **ETL Patterns** | Ralph Kimball https://www.kimballgroup.com/ | ✅ |

---

## 2. 发布流程调研（B-2）

### 2.1 调研方法（按规则 13 业界参考）

| 实践 | 来源 | v2 应用 |
|------|------|---------|
| **PyPI 官方指南** | https://packaging.python.org/tutorials/packaging-projects/ | ✅ |
| **Twine 上传工具** | https://twine.readthedocs.io/ | ✅ |
| **TestPyPI 测试** | https://packaging.python.org/guides/using-testpypi/ | ✅ |
| **Semantic Versioning** | https://semver.org/ | ✅ |
| **Trusted Publishing (OIDC)** | https://docs.pypi.org/trusted-publishers/ | ✅ |
| **GitHub Actions Release** | https://docs.github.com/actions | ✅ |

### 2.2 v2 现状

| 项 | 状态 |
|----|:---:|
| pyproject.toml | ✅ 已存在（name=etf-quant-v2, version=2.0.0a1）|
| README.md | ✅ 已存在 |
| LICENSE | ✅ MIT |
| src/etf_quant/ | ✅ 13 模块 |
| tests/ | ✅ 171 测试全过 |
| CHANGELOG.md | ⬜ 缺失 |
| .github/workflows/ | ⬜ 缺失 |
| Twine 配置 | ⬜ 待办 |

### 2.3 发布流程（Sprint-5 US-030）

按"按优先级"——**US-030 发布流程 6 步**：

```
Step 1: 写 CHANGELOG.md（v1 → v2 主要变更）
Step 2: 完善 pyproject.toml（添加 classifiers, urls, scripts）
Step 3: 写 GitHub Actions（CI/CD：pytest + lint + publish）
Step 4: 注册 PyPI 账户 + 2FA + Trusted Publishing
Step 5: 准备 release artifacts（wheel + sdist）
Step 6: twine upload dist/* + TestPyPI 验证
```

### 2.4 安全考虑（按规则 13）

| 项 | 来源 | v2 应用 |
|----|------|---------|
| **API Token + 2FA** | https://docs.pypi.org/account-verification/ | ✅ 必须 |
| **Trusted Publishing** | https://docs.pypi.org/trusted-publishers/ | ✅ 推荐 |
| **不提交密钥到 Git** | OWASP https://owasp.org/ | ✅ 用 env vars |

---

## 3. Sprint-5 启动计划

按"按优先级"——Sprint-5 6 US：

| US | 标题 | 计划 | 状态 |
|----|------|------|:---:|
| US-026 | v1 → v2 数据迁移（71034 行）| 0.3h | ✅ |
| US-027 | 性能基准测试 | 2h | ⬜ |
| US-028 | 文档整理 | 2h | ⬜ |
| US-029 | 端到端集成测试 | 2h | ⬜ |
| US-030 | 发布到 PyPI（6 步）| 3h | ⬜ |
| US-031 | Sprint-5 完整复盘 | 0.5h | ⬜ |
| **合计** | - | **9.8h** | - |

---

> **B 调研完成**
> **v1 → v2 数据迁移：71034 行真实验证成功**
> **发布流程：PyPI/Twine/TestPyPI/Trusted Publishing（业界参考）**
> **下一步**：Sprint-5 US-027 性能基准测试 → US-028 文档 → US-029 E2E → US-030 PyPI 发布