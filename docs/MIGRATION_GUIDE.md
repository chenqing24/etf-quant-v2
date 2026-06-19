"""
DocMIGRATION_GUIDE.md — v1 → v2 迁移指南（按 PRD US-030 要求）

按规则 13 调研来源：
- v1 docs/MIGRATION_HISTORY.md（L101/L236 教训源头）
- v1 scripts/migrate_v*.py（多次迁移经验）
- Flyway Migrate（https://flywaydb.org/documentation/usage/migration）
- Liquibase SQL Format（https://www.liquibase.org/）

用途：
    v1 业务库 → v2 业务库 完整迁移指南。
    包含：环境准备、schema 迁移、数据迁移、验证、回滚。

被谁调用：
    - v1 用户切换到 v2
    - Sprint-5 US-030 验收

使用方式：
    # 1. 备份 v1
    cp etf_strategy/etf_data_live/etf.db etf_strategy/etf_data_live/etf.db.bak

    # 2. 初始化 v2 schema
    cd etf_quant_v2
    PYTHONPATH=src python scripts/init_database.py

    # 3. 迁移数据
    PYTHONPATH=src python scripts/migrate_v1_to_v2.py

    # 4. 验证
    /home/qwenpaw/ENV/bin/pytest tests/integration/

依赖：
    - src/etf_quant/data_layer/（4 Repo）
    - schema/migrations/000-017.sql（19 个迁移）

注意事项：
    - 数据迁移是单向的（v1 → v2），不支持反向
    - 迁移后 v2 不依赖 v1，可以独立运行
    - v1 业务库保留（不删除），作为备份
"""
# MIGRATION_GUIDE.md

# v1 → v2 迁移指南（按 PRD US-030 要求）

> **目标读者**：从 v1 切换到 v2 的用户
> **预计时间**：30 分钟（含 schema 迁移 + 数据迁移 + 验证）
> **风险等级**：中（需要备份 v1）

---

## 1. 迁移前准备

### 1.1 环境要求

| 工具 | 版本 | 验证 |
|------|------|------|
| Python | ≥ 3.11 | `python --version` |
| SQLite | ≥ 3.35 | `sqlite3 --version` |
| Git | ≥ 2.30 | `git --version` |
| pytest | ≥ 8.0 | `pytest --version` |

### 1.2 备份 v1 业务库（必做）

```bash
# 备份 v1 业务库
cp etf_strategy/etf_data_live/etf.db etf_strategy/etf_data_live/etf.db.bak.$(date +%Y%m%d)

# 验证备份
ls -la etf_strategy/etf_data_live/etf.db*
```

### 1.3 检查 v1 业务库状态

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('etf_strategy/etf_data_live/etf.db')
tables = ['etf_names', 'stock_info', 'trade_history', 'daily']
for tbl in tables:
    n = conn.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]
    print(f'{tbl}: {n} 行')
"
```

**预期输出**：
```
etf_names: 1486 行
stock_info: 66 行
trade_history: 2 行
daily: 69480 行
```

---

## 2. v2 安装

### 2.1 克隆 v2 仓

```bash
cd ~/projects
# v2 仓在独立目录（不污染 v1）
git clone <v2_repo_url> etf_quant_v2
cd etf_quant_v2
```

### 2.2 安装依赖

```bash
# 推荐：venv
python3.11 -m venv venv
source venv/bin/activate

# 安装 v2 包（含 dev 依赖）
pip install -e ".[dev]"
```

### 2.3 验证安装

```bash
python -c "import etf_quant; print('✅ v2 安装成功')"
```

---

## 3. Schema 迁移（v2 启动）

### 3.1 初始化 v2 schema

```bash
# 默认 v2 DB 路径：data/etf.db
PYTHONPATH=src python scripts/init_database.py

# 或自定义路径
ETF_QUANT_DB_PATH=/path/to/v2.db PYTHONPATH=src python scripts/init_database.py
```

**预期输出**：
```
✅ 成功 19/19 个迁移

📊 数据库表 (14 个):
  - audit_log
  - daily
  - decision_snapshot
  - etf_name_metrics
  - etf_name_retry_queue
  - etf_names
  - execution_log
  - performance_metrics
  - positions
  - realtime_cache
  - schema_version
  - sqlite_sequence
  - stock_info
  - trade_history
```

### 3.2 验证 schema 完整性

```bash
python3 -c "
import sqlite3
v1 = sqlite3.connect('etf_strategy/etf_data_live/etf.db')
v2 = sqlite3.connect('data/etf.db')
all_ok = True
for tbl in ['etf_names', 'stock_info', 'trade_history', 'positions',
            'audit_log', 'decision_snapshot', 'daily',
            'etf_name_metrics', 'etf_name_retry_queue', 'realtime_cache']:
    v1_cols = set(c[1] for c in v1.execute(f'PRAGMA table_info(\"{tbl}\")').fetchall())
    v2_cols = set(c[1] for c in v2.execute(f'PRAGMA table_info(\"{tbl}\")').fetchall())
    if v1_cols.issubset(v2_cols):
        print(f'✅ {tbl}: v1 {len(v1_cols)} 列 ⊆ v2 {len(v2_cols)} 列')
    else:
        all_ok = False
        print(f'❌ {tbl}: v1 有 v2 无: {v1_cols - v2_cols}')
print('✅ v1 全部列已在 v2 schema' if all_ok else '❌ 仍有缺失')
"
```

---

## 4. 数据迁移（v1 → v2）

### 4.1 干跑（--dry-run）

```bash
PYTHONPATH=src python scripts/migrate_v1_to_v2.py --dry-run
```

**预期输出**：
```
📂 v1 业务库: /home/qwenpaw/.../etf_strategy/etf_data_live/etf.db
📂 v2 业务库: data/etf.db
🔧 模式: DRY-RUN（不写入）

  etf_names: 总 1486 行, 迁移 1486 行
  stock_info: 总 66 行, 迁移 66 行
  trade_history: 总 2 行, 迁移 2 行
  daily: 总 69480 行, 迁移 69480 行

📊 总计迁移: 71034 行
```

### 4.2 实际迁移

```bash
PYTHONPATH=src python scripts/migrate_v1_to_v2.py
```

**预期输出**（同干跑，但实际写入 v2）：
```
📊 总计迁移: 71034 行
```

### 4.3 验证迁移结果

```bash
python3 -c "
import sqlite3
v2 = sqlite3.connect('data/etf.db')
for tbl, expected in [('etf_names', 1486), ('stock_info', 66),
                      ('trade_history', 2), ('daily', 69480)]:
    n = v2.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]
    if n == expected:
        print(f'✅ {tbl}: {n} 行（符合预期）')
    else:
        print(f'❌ {tbl}: {n} 行（预期 {expected}）')
"
```

---

## 5. 迁移后验证

### 5.1 运行测试

```bash
cd etf_quant_v2
/home/qwenpaw/ENV/bin/pytest tests/ -v
```

**预期**：176/176 通过

### 5.2 跑性能基准

```bash
/home/qwenpaw/ENV/bin/pytest tests/benchmark/ --benchmark-only --benchmark-sort=mean
```

**预期**：5/5 通过

### 5.3 业务冒烟测试

```bash
# 测试 etf-daily skill
ETF_QUANT_DB_PATH=data/etf.db python skills/etf-daily/scripts/run_daily.py daily
```

**预期输出**：
```json
{
  "model_name": "v2_sop",
  "strategy_name": "C21Strategy",
  "holdings_count": 0,
  "snapshot_id": "..."
}
```

---

## 6. 回滚（如迁移失败）

### 6.1 备份 v2 DB

```bash
cp data/etf.db data/etf.db.migration-failed.$(date +%Y%m%d)
```

### 6.2 删除 v2 DB 重建

```bash
rm -f data/etf.db data/etf.db-wal data/etf.db-shm
PYTHONPATH=src python scripts/init_database.py
```

### 6.3 恢复 v1 业务库（如果需要）

```bash
# v1 业务库未动（只读），不需要恢复
# 但如果误删了 v1，从备份恢复
cp etf_strategy/etf_data_live/etf.db.bak.YYYYMMDD etf_strategy/etf_data_live/etf.db
```

---

## 7. 常见问题（FAQ）

### 7.1 迁移后 v1 业务库还在吗？

**在**。v1 → v2 是**单向迁移**（v1 业务库保留，作为历史数据）。v1 业务库**不删除**，但**不再写入**。

### 7.2 v2 业务库能直接给 v1 用吗？

**不能**。v2 schema 与 v1 业务库**列数不完全一致**（v2 ⊇ v1）：
- `etf_names` v2 多了 `type/scale/list_date/is_reference`（4 列）
- `stock_info` v2 多了 `industry/total_shares/float_shares/created_at`（4 列）
- `etf_name_retry_queue` v2 多了 `id`（1 列）

### 7.3 v2 数据能反向迁移回 v1 吗？

**不能直接迁移**。如果需要反向：
1. 写 v2 → v1 反向迁移脚本
2. 取 v2 列的子集（v2 ∩ v1）
3. INSERT OR REPLACE 到 v1

### 7.4 迁移后 v1 还能用吗？

**能，但建议停止使用**。v1 和 v2 是独立系统——同时使用会**数据不一致**。

---

## 8. 业界参考（按规则 13）

| 实践 | 来源 | v2 应用 |
|------|------|---------|
| Flyway Migrate | https://flywaydb.org/documentation/usage/migration | ✅ |
| Liquibase SQL Format | https://www.liquibase.org/ | ✅ |
| Database Refactoring | Sadalage《Refactoring Databases》 | ✅ |
| ETL Patterns | Ralph Kimball | ✅ |

---

> **迁移完成**
> **预期时间：30 分钟**
> **风险等级：中（需要备份）**
> **回滚成本：低（删除 v2 DB 重建）**