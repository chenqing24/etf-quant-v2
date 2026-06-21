# DATA_DICTIONARY — 数据字典

> **版本**：v2.0
> **日期**：2026-06-20
> **数据库**：SQLite（data/etf.db）
> **迁移**：schema/migrations/ 008-019（v2 完整对齐 v1 业务库）

---

## 1. 4 核心业务表

### 1.1 etf_names（ETF 元数据）

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| code | TEXT PRIMARY KEY | ETF 代码（如 510300）| - |
| name | TEXT | ETF 名称 | - |
| tradable | INTEGER | 是否可交易（0/1）| 0（规则 19）|
| pool_role | TEXT | 池角色（core/reference/excluded/unclassified）| unclassified |
| category | TEXT | 行业分类（宽基/行业/主题/海外）| NULL |
| created_at | TIMESTAMP | 创建时间 | - |
| updated_at | TIMESTAMP | 更新时间 | - |

**业务规则**：
- 1486 只 ETF（v1 业务库迁移）
- 14 只 core（v2 C21-1 用）
- 40 只 reference
- 1432 只 unclassified（待分类）

### 1.2 daily（每日行情）

| 字段 | 类型 | 说明 |
|------|------|------|
| code | TEXT | ETF 代码 |
| date | DATE | 交易日期 |
| open | REAL | 开盘价 |
| high | REAL | 最高价 |
| low | REAL | 最低价 |
| close | REAL | 收盘价 |
| volume | INTEGER | 成交量 |
| amount | REAL | 成交额 |
| PRIMARY KEY | (code, date) | |

**业务规则**：
- 69480 行（v1 业务库迁移）
- 14 只核心池 5 年+ 数据

### 1.3 trade_history（交易历史）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 交易 ID |
| date | DATE | 交易日期 |
| code | TEXT | ETF 代码 |
| action | TEXT | buy/sell |
| price | REAL | 成交价 |
| qty | INTEGER | 数量 |
| amount | REAL | 成交金额 |
| strategy | TEXT | 策略名 |
| reason | TEXT | 交易原因 |
| emotion | TEXT | 情绪（实盘：calm/fear/fomo/regret）|
| is_real | INTEGER | 是否实盘（0/1）|

**业务规则**：
- 2 行（v1 业务库迁移）
- 规则 23：分析时先看 is_real 字段

### 1.4 stock_info（个股/ETF 信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| code | TEXT PRIMARY KEY | 股票代码 |
| name | TEXT | 股票名称 |
| exchange | TEXT | 交易所 |
| full_code | TEXT | 完整代码 |
| list_date | DATE | 上市日期 |
| updated_at | TIMESTAMP | 更新时间 |

**业务规则**：
- 66 行（v1 业务库迁移）
- 注意：不含 600519 等常见股票（v1 ETF 业务库无个股）

## 2. v2 扩展表

### 2.1 positions（持仓）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 持仓 ID |
| code | TEXT | ETF 代码 |
| qty | INTEGER | 数量 |
| entry_price | REAL | 入场价 |
| entry_date | DATE | 入场日期 |
| current_price | REAL | 当前价 |
| pnl_pct | REAL | 盈亏比例 |
| status | TEXT | open/closed |

### 2.2 decision_snapshot（决策快照）

| 字段 | 类型 | 说明 |
|------|------|------|
| snapshot_id | TEXT PRIMARY KEY | 快照 ID |
| snapshot_time | TIMESTAMP | 快照时间 |
| trigger | TEXT | 触发器（daily/eval/manual）|
| model_name | TEXT | 模型名 |
| strategy_name | TEXT | 策略名 |
| market_regime | TEXT | 市场模式 |

### 2.3 audit_log（审计日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 日志 ID |
| timestamp | TIMESTAMP | 时间 |
| source | TEXT | 执行源（v2_sop / cron / manual）|
| action | TEXT | 操作 |
| details | TEXT | 详情 |

## 3. v2 不变表（v1 业务库迁移）

- etf_name_metrics（v1 字段：created_at/verified/sources_tried）
- etf_name_retry_queue（v1 字段：attempt_count/status/priority/finished_at）
- realtime_cache（v1 字段：name/change/volume/amount/timestamp/updated_at）

## 4. 数据访问原则（规则 15）

- 业务层零 SQL
- 通过 data_layer 的 6 个 Repository 访问
- pre-commit 钩子拦截 sqlite3.connect

## 5. 迁移历史

| 迁移 | 内容 |
|------|------|
| 008-012 | v1 业务库 19 新列 + 4 新表 |
| 013-015 | Sprint-4 修列名（3 迁移 SQL）|
| 016-019 | Sprint-5 v1 → v2 数据迁移（71034 行）|

## 5. v3 增量数据源（2026-06-21 — mission-20260621-193542）

### 5.1 factor_icir.csv（IC 评估结果）

> **位置**：`data/factor_icir.csv`
> **生成**：`python scripts/run_factor_evaluation.py`（按规则 15 数据源统一）
> **业务**：27 因子在 510300（沪深 300 ETF）近 2 年（504 交易日）IC/IR 评估
> **业界参考**：Grinold & Kahn 2000 *Active Portfolio Management* Ch 4

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| factor_name | TEXT | 因子 ID（27 因子） | T5_ma5 |
| ic | REAL | Spearman ρ（IC 均值） | -0.3604 |
| ir | REAL | IC.mean() / IC.std() | -1.6166 |
| ic_std | REAL | IC 标准差 | 0.223 |
| sample_count | INTEGER | 滚动窗口数 | 89 |
| forward_window | INTEGER | 前瞻 N 日（默认 5） | 5 |
| eval_date | TEXT | 评估时间（含时分） | 2026-06-21 20:01:38 |
| benchmark | TEXT | 基准 ETF（默认 510300） | 510300 |

### 5.2 factor_icir_history.csv（季度对比历史）

> **位置**：`data/factor_icir_history.csv`
> **生成**：每次跑 `run_factor_evaluation.py` 自动 append（按规则 18 CSV 必验证）
> **业务**：季度 IC 巡检的数据源（US-008/010）

| 字段 | 类型 | 说明 |
|------|------|------|
| （同 factor_icir.csv） | | 含 eval_date 区分不同次跑 |

**append 模式防覆盖**（按规则 18）：
- `mode='a'`，header 仅首次写
- 多次跑行数累加（3 次跑 = 81 行）

### 5.3 reports/ic_decay_YYYYMMDD.md（季度巡检报告）

> **位置**：`reports/ic_decay_YYYYMMDD.md`
> **生成**：`python scripts/check_ic_decay.py`（US-010 实施）
> **业务**：对比上季度 vs 本季度 IC，识别衰减因子

**报告结构**：
1. 概况（巡检因子数 + 衰减因子数）
2. ⚠️ 衰减因子表格（|ΔIC|>0.03 或 |IR|<0.5）
3. AI 建议（降权/弃用/移到参考池）

### 5.4 业务自评数据源（v3 增量）

> **位置**：`missions/mission-20260621-193542/scripts/business_check.py`
> **业务**：9 维度 225 分自动断言（v2 5 维度 125 分基础上 +4 维度）
> **业界参考**：DORA Metrics + AWS Well-Architected
