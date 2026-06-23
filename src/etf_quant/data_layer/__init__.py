"""
etf_quant/data_layer — 数据访问层（v3.0 单一入口）

按 SOUL.md 规则 15（数据源统一原则）：
    "数据只存一份：SQLite；入口只有一个：DataSourceRouter"
    所有业务模块只通过 data_layer 读写 etf.db，不直接读 CSV 或第三方 API。

子模块：
    - loader: DataLoader（读）+ ETFNameLoader（兼容旧代码）
    - writer: DataWriter（写 + WAL 模式 + schema migration）
    - *repo: 8 个 Repository（trade_history / position / audit_log / decision_snapshot / etf_pool）
    - contracts: 5 个 Protocol（业务层依赖接口，不依赖实现）
    - exceptions: 数据层异常（DataValidationError / SchemaVersionError 等）

入口示例：
    from etf_quant.data_layer import DataLoader, DataWriter
    loader = DataLoader()
    data = loader.load(min_rows=300)
"""
from etf_quant.data_layer.loader import DataLoader, ETFNameLoader, load_etf_data
from etf_quant.data_layer.writer import DataWriter
from etf_quant.data_layer.contracts import (
    DataLoaderProtocol,
    IndicatorProtocol,
    SelectorProtocol,
    ReportGeneratorProtocol,
    FetcherProtocol,
    OHLCVSchema,
    IndicatorSchema,
    SelectorResultSchema,
    TradeRecordSchema,
)
from etf_quant.data_layer.exceptions import (
    DataValidationError,
    DataLayerError,
    SchemaVersionError,
    ExecutionSourceError,
)

__all__ = [
    # Loaders
    "DataLoader", "ETFNameLoader", "load_etf_data",
    # Writer
    "DataWriter",
    # Contracts
    "DataLoaderProtocol", "IndicatorProtocol", "SelectorProtocol",
    "ReportGeneratorProtocol", "FetcherProtocol",
    "OHLCVSchema", "IndicatorSchema", "SelectorResultSchema", "TradeRecordSchema",
    # Exceptions
    "DataValidationError", "DataLayerError", "SchemaVersionError", "ExecutionSourceError",
]
