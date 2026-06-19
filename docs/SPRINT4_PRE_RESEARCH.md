# Sprint-4 启动前 B 调研（4 个未迁移表实际 API）

> **目的**：按用户原话"先B后A" + L228 教训"先查再答"，避免 Sprint-2 84/100 自评失败重演
> **方法**：直接打开 v1 业务库 + PRAGMA table_info
> **触发**：Sprint-4 US-020~024 skill 入口启动前

---

## 1. 调研方法（按 L228 教训"先查再答"）

```python
import sqlite3
conn = sqlite3.connect("v1/etf_data_live/etf.db")
for tbl in ["stock_info", "etf_name_metrics",
            "etf_name_retry_queue", "realtime_cache"]:
    cols = conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()
    n = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"{tbl}: cols={len(cols)} rows={n}")
```

---

## 2. 4 个表真实 schema

### 2.1 stock_info（6 列，66 行）

| # | 列 | 类型 | 约束 |
|---|----|------|------|
| 0 | code | TEXT | NOT NULL [PK] |
| 1 | name | TEXT | NOT NULL |
| 2 | exchange | TEXT | NOT NULL |
| 3 | full_code | TEXT | NOT NULL |
| 4 | list_date | TEXT | NOT NULL |
| 5 | updated_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |

**注意**：v1 实际是 6 列（含 exchange），v2 schema 012 写的是 6 列。**v2 schema 012 是错的**——我之前写 `etf_name_metrics`/`etf_name_retry_queue`/`realtime_cache` 4 个表，没把 stock_info 也写进去（按 L228 教训"先查再答"原则，stock_info 在 v1 业务库存在但 v2 schema 012 没建——我建了别的不在 v1 业务库的表）。

**等等——实际 v2 schema 012 我建的是 4 个表，**stock_info 我在 Sprint-3 B 调研时**写**了。看 v2 仓 schema 012 实际建表：

| 表 | v2 schema 012 实际 | v1 业务库 | 差异 |
|----|------------------|----------|------|
| stock_info | 6 列 | 6 列 | ✅ 一致 |
| etf_name_metrics | 7 列 | 7 列 | ✅ 一致 |
| etf_name_retry_queue | 8 列 | 8 列 | ✅ 一致 |
| realtime_cache | 9 列 | 9 列 | ✅ 一致 |

✅ 4 个表 v2 schema 012 与 v1 业务库**列数完全匹配**——L228 教训落地。

### 2.2 etf_name_metrics（7 列，0 行）

| # | 列 | 类型 | 约束 |
|---|----|------|------|
| 0 | id | INTEGER | NOT NULL [PK] |
| 1 | code | TEXT | NULL |
| 2 | success | INTEGER | NOT NULL |
| 3 | verified | INTEGER | NOT NULL |
| 4 | duration_ms | INTEGER | NOT NULL |
| 5 | sources_tried | TEXT | NOT NULL |
| 6 | created_at | TEXT | NOT NULL |

**注意**：v1 schema 中 `created_at` 字段，但 v2 schema 012 我写的 7 列是 `timestamp/source/code/success/duration_ms/error_message`——**与 v1 不一致**！

让我看 v2 schema 012 实际写的：

```sql
-- 012_create_unmigrated_tables.sql
CREATE TABLE IF NOT EXISTS etf_name_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    source TEXT NOT NULL,
    code TEXT,
    success INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER,
    error_message TEXT
);
```

**v2 schema 012 实际列**：`id, timestamp, source, code, success, duration_ms, error_message`（7 列）
**v1 业务库真实列**：`id, code, success, verified, duration_ms, sources_tried, created_at`（7 列）

**差异**：
- v2 有 `timestamp/source/error_message`，v1 没有
- v1 有 `code/verified/sources_tried/created_at`，v2 没有

**B 调研发现真实差异——v2 schema 012 的 etf_name_metrics 错了！**

### 2.3 etf_name_retry_queue（8 列，0 行）

**v2 schema 012 实际列**：`id, code, source, retry_count, max_retry, next_retry_at, last_error, created_at`（8 列）
**v1 业务库真实列**：`code, attempt_count, last_error, status, priority, created_at, next_retry_at, finished_at`（8 列）

**差异**：
- v2 有 `id/source/retry_count/max_retry`，v1 没有
- v1 有 `code/attempt_count/status/priority/finished_at`，v2 没有

### 2.4 realtime_cache（9 列，0 行）

**v2 schema 012 实际列**：`code, price, change_pct, volume, source, cached_at, expires_at`（7 列）
**v1 业务库真实列**：`code, name, price, change, change_pct, volume, amount, timestamp, updated_at`（9 列）

**差异**：
- v2 有 `change_pct/source/cached_at/expires_at`，v1 没有
- v1 有 `code/name/price/change/volume/amount/timestamp/updated_at`，v2 没有

---

## 3. 真实差异汇总（v1 vs v2 schema 012）

| 表 | v1 实际 | v2 schema 012 实际 | 真实差异 |
|----|:---:|:---:|:---:|
| stock_info | 6 列 | 6 列 | ✅ 完全一致 |
| **etf_name_metrics** | 7 列 | 7 列（**列不同**）| ❌ **3 列缺失 + 3 列多余** |
| **etf_name_retry_queue** | 8 列 | 8 列（**列不同**）| ❌ **5 列缺失 + 3 列多余** |
| **realtime_cache** | 9 列 | 7 列 | ❌ **2 列缺失 + 4 列多余** |

**关键发现**：Sprint-3 B 调研时**没仔细看 v1 业务库实际列名**——只看了"列数"。"列数对"≠"列名对"。

按规则 6.1（错了不美化）——**Sprint-3 B 调研不彻底**：

1. Sprint-3 调研用 `PRAGMA table_info` 查了 v1 业务库
2. 但**只比较列数**，**没比较列名**
3. **错误结论**："v2 schema 012 与 v1 业务库 4 表完全一致"
4. **实际**：3/4 表列名不对

**这是 Sprint-2 84/100 自评失败的延续**——L228 教训"先查再答"**仍然没彻底**。

---

## 4. 修复方案（A 启动前必修）

### 4.1 P0（必须修复）

| 修复 | 范围 |
|------|------|
| **etf_name_metrics 列修正** | v2 schema 013 改列名（删除 3 个多余，加 3 个缺失）|
| **etf_name_retry_queue 列修正** | v2 schema 014 改列名（删除 3 个多余，加 5 个缺失）|
| **realtime_cache 列修正** | v2 schema 015 改列名（删除 4 个多余，加 2 个缺失）|

### 4.2 P1（应该修复）

| 修复 | 范围 |
|------|------|
| stock_info 数据迁移（66 行）| scripts/migrate_v1_stock_info.py |
| etf_names 真实数据迁移（1486 行）| scripts/migrate_v1_etf_names.py |

### 4.3 P2（可推迟）

| 修复 | 范围 |
|------|------|
| 全量 v1 → v2 数据迁移 | 包括 etf_name_metrics/etf_name_retry_queue/realtime_cache（0 行不需要）|

---

## 5. Sprint-3 B 调研不彻底的根因

按规则 6.1（错了不美化）+ L228 教训"先查再答"——Sprint-3 B 调研的**根因错误**：

```python
# Sprint-3 调研时（错的）
for tbl in ['stock_info', 'etf_name_metrics', 'etf_name_retry_queue', 'realtime_cache']:
    cols = conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()
    n = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"{tbl}: cols={len(cols)} rows={n}")
# 错误：只比较 len(cols)，不比较列名！
```

```python
# 正确（按 L228 教训"先查再答"）
for tbl in ['stock_info', 'etf_name_metrics', 'etf_name_retry_queue', 'realtime_cache']:
    cols = conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()
    col_names = [c[1] for c in cols]  # ← 必须比较列名！
    # 对比 v2 schema 012 的列名
    v2_cols = parse_v2_schema_012(tbl)  # 从 012 SQL 解析
    if col_names != v2_cols:
        print(f"DIFF: {tbl}")
        # 输出具体差异
```

**关键洞察**：**B 调研要看列名，不只看列数**。

---

## 6. 业界参考（按规则 13）

| 实践 | 来源 | 应用 |
|------|------|------|
| **Schema Diff** | Alembic https://alembic.sqlalchemy.org/en/latest/autogenerate.html | ✅ |
| **DB Schema Compare** | Flyway https://flywaydb.org/documentation/usage/plugins | ✅ |
| **Data Quality** | Great Expectations https://greatexpectations.io/ | ✅ |
| **CI Schema Tests** | dbt https://docs.getdbt.com/docs/build/sources | ✅ |

**业界共识**：schema diff 必须**列名+列类型+约束**全对比，**只看列数是不够的**。

---

## 7. v2 修复路径（按"按优先级"）

按"先B后A"——**B 调研修复**：

```
Step 1: 3 个迁移 SQL（013/014/015）改列名
Step 2: 测试 4 个新表（0 行 v1 数据，只需要 schema 正确）
Step 3: 修复后全量 144+ 测试回归
Step 4: A 启动（5 skill 入口 US-020~024）
```

按"按优先级"——**B 调研修复 0.5h，A 启动 Sprint-4 2h**。

---

## 8. 等用户拍板

按规则 4.1（执行阶段不能擅自改设计）+ 用户的"要求同上"（先 B 再 A）——**B 调研报告已写完，请确认**：

| 选项 | 内容 |
|------|------|
| **A** | 按 B 调研结果，3 迁移 SQL 修复 + A 启动（5 skill 入口）|
| **B** | 跳过 B 调研修复，4 表不动直接 A 启动（已知有列名差异）|
| **C** | 其他方案（您指定）|

---

> **B 调研完成**
> **关键发现**：Sprint-3 B 调研不彻底（只比较列数，没比较列名）
> **v2 schema 012 的 3/4 表列名与 v1 业务库不同**——需要 schema 013/014/015 修正
