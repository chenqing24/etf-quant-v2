# INTERFACE_CONTRACT — 接口契约

> **版本**：v2.0
> **日期**：2026-06-20
> **依据**：Sprint-0 接口契约 + Sprint-7 业务完整化

---

## 1. data_layer Protocols

```python
# 5 个 Protocol（业务层依赖接口，不依赖实现）
class DataLoaderProtocol(Protocol):
    def load(self, min_rows: int = 300) -> Dict[str, pd.DataFrame]: ...
    def get_etf_list(self) -> List[str]: ...
    def get_latest_date(self, code: str = None) -> Optional[str]: ...

class IndicatorProtocol(Protocol):
    """因子接口（按 US-013 27 因子）"""
    def calculate(self, df: pd.DataFrame) -> pd.Series: ...

class SelectorProtocol(Protocol):
    """选股接口"""
    def select(self, scores: pd.DataFrame, top_n: int) -> List[str]: ...

class ReportGeneratorProtocol(Protocol):
    """报告接口"""
    def generate(self, results: Dict) -> str: ...

class FetcherProtocol(Protocol):
    """数据获取接口"""
    def fetch(self, code: str) -> pd.DataFrame: ...
```

## 2. alpha Factor 接口

```python
@dataclass
class FactorMetadata:
    name: str               # 因子名（如 "B1"）
    description: str        # 描述
    category: str           # 类别: trend/momentum/volume/volatility/oscillator/relative/reversal
    ic: Optional[float]     # IC 值
    ir: Optional[float]     # IR 值
    source: str = "v1"      # 来源
    oos_is: Optional[float] = None  # OOS/IS 比率

class Factor(ABC):
    metadata: FactorMetadata
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.Series: ...
```

## 3. universe ETFInfo

```python
@dataclass
class ETFInfo:
    code: str
    name: str
    pool_role: str          # core / reference / excluded / unclassified
    tradable: bool
    category: Optional[str] = None
```

## 4. notify TradeSignal

```python
@dataclass
class TradeSignal:
    date: str
    code: str
    action: str             # 'buy' or 'sell'
    price: float
    reason: str
    score: float = 0.0
    pnl: float = 0.0
```

## 5. portfolio Holding

```python
@dataclass
class Holding:
    code: str
    qty: int
    entry_price: float
    entry_date: str
    current_price: Optional[float] = None
```

## 6. monitor Reports

```python
@dataclass
class DataHealthReport:
    fresh: bool
    fresh_minutes: float
    threshold_minutes: int
    min_day_count: int
    issues: list

@dataclass
class SystemHealthReport:
    disk_free_gb: float
    db_size_mb: float
    issues: List[str]

@dataclass
class BusinessAlert:
    severity: str          # INFO / WARN / CRITICAL
    code: str
    message: str
```

## 7. scheduler CronJobConfig

```python
@dataclass
class CronJobConfig:
    name: str
    schedule: str           # cron 表达式
    command: str
    target_session: str = "WoXtGw=="  # L222 教训
    description: str = ""
```

## 8. 关键约束（按规则）

| 规则 | 约束 | 实施 |
|------|------|------|
| 规则 15 | 业务层零 SQL | pre-commit 钩子拦截 sqlite3.connect |
| 规则 19 | 默认值宁严勿宽 | pool_role 默认 unclassified，tradable 默认 0 |
| 规则 11 | 先调研再实现 | 每个新模块先 SPRINT_X_PRE_RESEARCH.md |
| 规则 13 | 业界参考 | 设计文档必须标注来源 |

## 9. Repository 接口

| Repository | 方法 | 说明 |
|------------|------|------|
| ETFRepository | list_codes(role) / all_codes() / get_meta(code) | etf_names 表 |
| TradeHistoryRepository | list_all() / insert() | trade_history 表 |
| PositionRepository | list_all() / update() | positions 表 |
| DecisionSnapshotRepository | insert() / list_all() | decision_snapshot 表 |
| AuditLogRepository | log() | audit_log 表 |
