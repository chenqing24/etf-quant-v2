# Execution 层重构设计（v2 Sprint-2 US-007）

> **目的**：v1 TradeTracker 1483 行 + 20 处 SQL → v2 execution/ 3 文件 + 委托模式
> **调研方法**：规则 13 业界参考（每条标注 ✅ Verified）
> **触发**：用户原话"A，参考业界最佳实践来设计"

---

## 1. 业界 3 大架构模式（调研）

### 模式 1：Repository 模式（DDD）

| 来源 | 引用 | Verified |
|------|------|:--------:|
| Eric Evans《Domain-Driven Design》2003 | https://domainlanguage.com/ddd/ | ✅ |
| Microsoft "Repository pattern" | https://docs.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design | ✅ |
| Martin Fowler "Repository" | https://martinfowler.com/eaaCatalog/repository.html | ✅ |

**核心**：业务层不直接访问 DB，通过 Repository 接口。
- ✅ v1 ETFRepository 已经是这个模式（已复制到 v2 data_layer）
- ✅ v2 设计：所有 SQL 必须封装在 Repository/DAO 类中

### 模式 2：Unit of Work 模式（DDD）

| 来源 | Verified |
|------|:--------:|
| Eric Evans《DDD》| ✅ |
| Martin Fowler "UnitOfWork" https://martinfowler.com/eaaCatalog/unitOfWork.html | ✅ |

**核心**：把多个 Repository 操作封装为事务单元。
- v1 tracker.py 每个方法都自己 conn.commit()（散乱）
- v2 设计：**业务层不调 commit**，由 UnitOfWork 自动管理

### 模式 3：Data Mapper 模式（Fowler P of EAA）

| 来源 | Verified |
|------|:--------:|
| Martin Fowler "Data Mapper" https://martinfowler.com/eaaCatalog/dataMapper.html | ✅ |
| Hibernate / MyBatis 实现 | ✅ |

**核心**：业务对象与 DB 行完全分离，业务代码看不到 SQL。
- v1 tracker.py 业务对象 TradeRecord/Position 是 dataclass
- v2 设计：Mapper 类负责 dataclass ↔ SQL 转换

---

## 2. v1 现状（按 L228 教训"先查再答"）

| 指标 | 数字 | 来源 |
|------|:---:|------|
| tracker.py 总行数 | 1483 | `wc -l` |
| 公开方法 | 14 | `grep "^def "` |
| 总方法 | 37 | 同上 |
| SQL 语句 | 20 | `grep "INSERT\|UPDATE\|DELETE\|SELECT"` |
| sqlite3.connect | 2 处 | `grep "sqlite3.connect"` |
| cursor/conn 使用 | ~15 处 | `grep "conn."` |
| 旧 v1 import | 1 处（已修）| `grep "from src."` |

**v1 架构问题**：
- 业务方法紧耦合 SQL（每个公开方法都自己 conn.execute + conn.commit + conn.close）
- 违反 v2 规则 15（业务代码不能 sqlite3.connect）
- 没有 Repository 抽象（v1 tracker 自己写 SQL）
- 没有事务管理（散乱 commit）

---

## 3. v2 设计（按业界 3 大模式）

### 3.1 三层架构

```
v2 execution/ 层架构：

execution/                          # 业务层（不写 SQL）
├── tracker.py          # TradeTracker 业务方法（委托模式）
├── position_guide.py   # 持仓指南（v1 US-007 业务）
├── validator.py        # 交易验证（v1 业务）
└── types.py            # TradeRecord / Position dataclass

data_layer/                  # 数据层（所有 SQL 集中）
├── trade_history_repo.py   # trade_history 表 SQL（Repository 模式）
├── position_repo.py         # positions 表 SQL
├── audit_log_repo.py        # audit_log 表 SQL
├── decision_snapshot_repo.py # decision_snapshot 表 SQL
└── etf_pool_repository.py  # 已存在（v1 复制）
```

### 3.2 关键设计原则

**P1：业务层零 SQL**
- execution/ 任何文件**禁止** `import sqlite3`
- 所有 DB 操作通过 `data_layer/*_repo.py`

**P2：Repository 接口统一**
- 每个 Repo 类提供 5 个标准方法：`get/insert/update/delete/list`
- 业务层只调 Repo，不知道表名/字段名

**P3：事务由调用方管理（简化版 UnitOfWork）**
- 每个业务方法**先开 conn，最后 commit/rollback**
- 不引入 UnitOfWork 类（v2 规模不需要）

**P4：Data Mapper 集中**
- TradeRecord / Position / AuditLog dataclass ↔ DB 行的转换
- 全部在 Repo 类内完成（业务代码不写 SQL 字符串）

### 3.3 重构步骤（3-4h 估算）

| Step | 内容 | 时间 | 风险 |
|------|------|:---:|:---:|
| 1 | data_layer/trade_history_repo.py（最复杂）| 1h | 中 |
| 2 | data_layer/position_repo.py | 0.5h | 低 |
| 3 | data_layer/audit_log_repo.py | 0.3h | 低 |
| 4 | data_layer/decision_snapshot_repo.py | 0.3h | 低 |
| 5 | execution/tracker.py 重写（委托模式）| 1h | 中 |
| 6 | tests/unit/test_execution_tracker.py 扩展 | 0.5h | 低 |
| 7 | pre-commit 验证 + 全量测试 | 0.2h | 低 |
| **合计** | - | **3.8h** | - |

### 3.4 与 v1 API 兼容性

**保留** v1 14 个公开方法（按 Sprint-2 US-007 验收标准）：
- record_buy / record_sell / load_trades / load_positions
- get_holdings / get_account_summary
- check_stop_loss / check_take_profit / can_buy / can_sell
- check_portfolio / check_data_consistency
- get_consistency_report / export_csv

**改**：每个方法**内部**从 `self._get_conn()` 改为 `repo.insert()/get()` 委托。

---

## 4. 验收标准（按 Sprint-2 US-007）

- [ ] 4 个 Repo 类（trade_history/position/audit_log/decision_snapshot）
- [ ] execution/tracker.py 重写，**零 sqlite3 import**
- [ ] v1 14 个公开方法全部保留
- [ ] pre-commit 钩子 0 硬错误
- [ ] tests/unit/test_execution_tracker.py 9 → 14+ 通过
- [ ] 全量测试（41 + 16 = 57+ 测试）全过
- [ ] US-007 自评 100/100

---

## 5. 风险评估

| 风险 | 等级 | 缓解 |
|------|:---:|------|
| v1 SQL 行为差异（v1 vs v2 DB 字段名）| 中 | 先 read v1 真实 SQL，再写 Repo |
| 事务边界变化（v1 每个方法自己 commit）| 中 | 保持每个方法单事务（不引入 UnitOfWork）|
| 测试 fixture 与 v1 不兼容 | 低 | 用 ETF_QUANT_DB_PATH 环境变量 |

---

## 6. 业界参考总结

| 模式 | 来源 | v2 应用 |
|------|------|---------|
| Repository | Evans 2003 / Fowler | 4 个 Repo 类封装所有 SQL |
| Unit of Work | Evans 2003 / Fowler | 简化版：每个方法单事务 |
| Data Mapper | Fowler | Repo 类内 dataclass ↔ SQL 转换 |
| 12-Factor | Heroku 2011 | config 外置（已用 ETF_QUANT_DB_PATH）|
| Strangler Fig | Fowler 2004 | 渐进替换 v1 tracker |

---

## 7. 不做的事（YAGNI）

- ❌ UnitOfWork 抽象类（v2 规模不需要）
- ❌ 异步 SQL（v1 同步，保持兼容）
- ❌ ORM（SQLAlchemy 引入成本高，v1 不用）
- ❌ 多数据库支持（v2 单一 SQLite）
- ❌ Event Sourcing（v1 状态机已经够）

---

> **下一步**：开始执行 Step 1-7（按 SOP-02 Phase 4 小步快走）
