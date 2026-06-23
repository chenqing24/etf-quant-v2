"""
etf_quant/config — 配置常量模块

用途：v2 系统统一配置中心（路径/超时/阈值/URL 收口）。
被谁调用：12 模块全部依赖（data_layer/alpha/risk/...）。

按 SOUL.md 规则 9（首次出现就提取常量）：
    所有路径/超时/阈值/URL 收口在 constants.py
    禁止内联常量，违反则立即重构

子模块：
    - constants: DB_PATH / DATA_DIR / API URL / 监控阈值 / ETF 池默认值

入口示例：
    from etf_quant.config import constants
    db_path = constants.DB_PATH  # 绝对路径
    threshold = constants.DEFAULT_MAX_DELAY_MINUTES
"""
from etf_quant.config.constants import (
    DATA_DIR,
    DB_NAME,
    DB_PATH,
    SCHEMA_DIR,
    TRADES_FILE,
    TENCENT_QT_URL,
    TENCENT_IFZQ_URL,
    HTTP_TIMEOUT_SHORT,
    HTTP_TIMEOUT_LONG,
    WAL_MODE_ENABLED,
    DEFAULT_MIN_DAY_COUNT,
    DEFAULT_MAX_DELAY_MINUTES,
    DEFAULT_ALERT_COOLDOWN_SECONDS,
    DEFAULT_BASE_URL,
    DEFAULT_ETF_POOL_SIZE,
    DEFAULT_REFERENCE_POOL_SIZE,
)

__all__ = [
    "DATA_DIR", "DB_NAME", "DB_PATH", "SCHEMA_DIR", "TRADES_FILE",
    "TENCENT_QT_URL", "TENCENT_IFZQ_URL",
    "HTTP_TIMEOUT_SHORT", "HTTP_TIMEOUT_LONG",
    "WAL_MODE_ENABLED",
    "DEFAULT_MIN_DAY_COUNT", "DEFAULT_MAX_DELAY_MINUTES",
    "DEFAULT_ALERT_COOLDOWN_SECONDS", "DEFAULT_BASE_URL",
    "DEFAULT_ETF_POOL_SIZE", "DEFAULT_REFERENCE_POOL_SIZE",
]
