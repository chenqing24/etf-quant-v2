# data_layer — 数据层

> **职责**：所有数据采集、写入、读取、监控的唯一入口
> **依据**：v2-roadmap/notes/09_data_layer.md + v1 src/data/ + 规则 15（数据源统一）

## 核心约束

- **业务代码禁止 sqlite3.connect**（pre-commit 拦截）
- **所有写入走 DataWriter**（自动 WAL + 防重复）
- **所有读取走 DataLoader**（统一接口）
- **所有数据契约走 `contracts.py`**（5 Schema + 5 Protocol）

## 接口契约

### Schema（数据契约）

| Schema | 字段 | 来源 |
|--------|------|------|
| `OHLCVSchema` | code/date/open/high/low/close/volume | v1 继承 |
| `IndicatorSchema` | ma5/ma10/rsi14 等 | v1 继承 |
| `SelectorResultSchema` | Set[str] (codes) | v1 继承 |
| `TradeRecordSchema` | 31 字段（含 is_real/emotion/snapshot_ref）| v1 继承 |
| `BacktestResultSchema` | 收益/夏普/回撤/胜率/IC/IR | v2 新增 |
| `PerformanceMetricsSchema` | 8 大类 43 指标 | v2 新增 |
| `PositionStateSchema` | 持仓状态枚举 | v2 新增 |
| `DecisionSnapshotSchema` | 14 字段（model_name/strategy/eval/...）| v2 新增 |

### Protocol（接口契约）

| Protocol | 方法 | 来源 |
|----------|------|------|
| `DataLoaderProtocol` | load/load_single | v1 继承 |
| `IndicatorProtocol` | calculate | v1 继承 |
| `SelectorProtocol` | select_etfs | v1 继承 |
| `ReportGeneratorProtocol` | generate_report | v1 继承 |
| `FetcherProtocol` | fetch_daily | v1 继承 |
| `BacktestEngineProtocol` | run_backtest | v2 新增 |
| `RiskManagerProtocol` | check_position | v2 新增 |
| `ExecutionTrackerProtocol` | record_buy/sell | v2 新增 |

## 文件

- `contracts.py` — 5 Schema + 5 Protocol（从 v1 继承）
- `writer.py` — DataWriter（待 US-003 实现）
- `loader.py` — DataLoader（待 US-003 实现）
- `monitor.py` — 数据监控（待 US-003 实现）

## 关联教训

- L15（数据源统一）
- L22（基于外部数据判断）
- L62（监控阈值动态化）
- L112（DB_PATH 绝对路径）
- L200（沉默失败 7 天）
- L228（300ETF 盲点）