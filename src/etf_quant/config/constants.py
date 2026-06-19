"""
v2 配置常量（从 v1 src/constants.py 继承）。

用途：
    v2 系统的统一配置中心：
    - DB_PATH 绝对路径（L112 教训）
    - WAL 模式启用（v1 6/1 教训：database locked 修复）
    - 数据/监控/调度/ETF 池的默认值
    - v1 兼容字段（TRADES_FILE/TENCENT_QT_URL/HTTP_TIMEOUT_*）

被谁调用：
    - src/etf_quant/data_layer/（writer.py / loader.py / monitor.py）
    - src/etf_quant/execution/（tracker.py US-008 JSON 兼容）
    - src/etf_quant/monitor/（默认值兜底）
    - tests/integration/（init_database_regression 临时覆盖）

功能说明：
    - _PROJECT_ROOT 路径计算（按 L112 必须绝对）
    - DATA_DIR / DB_PATH / SCHEMA_DIR 三大目录
    - WAL_MODE_ENABLED = True（v1 6/1 修复）
    - DEFAULT_* 监控阈值（v1 L62 教训：动态化兜底）

使用方式：
    from etf_quant.config import constants
    db_path = constants.DB_PATH  # 绝对路径

依赖：
    - 无（纯常量）
    - L112 教训（DB_PATH 绝对路径）
    - L62 教训（监控阈值动态化兜底）
    - v1 6/1 教训（WAL 模式）

注意事项：
    - 不要硬编码其他常量（违反 v1 L211 教训：机制层 > AI 自觉）
    - 临时测试覆盖用 ETF_QUANT_DB_PATH 环境变量（L236 教训）
    - v1 兼容字段保留到 v2 完全迁移后删除
"""
from __future__ import annotations

from pathlib import Path

# 项目根（PROJECT_ROOT = v2 仓根 = src/etf_quant/ 的祖父目录）
# 不依赖 cwd（按 L112 教训：DB_PATH 必须绝对路径）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = _PROJECT_ROOT / "data"
DB_NAME = "etf.db"
DB_PATH = str(DATA_DIR / DB_NAME)
SCHEMA_DIR = _PROJECT_ROOT / "schema" / "migrations"

# 兼容 v1 字段名（US-008 JSON 兼容）
TRADES_FILE = DATA_DIR / "etf_trades.json"

# API 地址（v1 兼容）
TENCENT_QT_URL = "http://qt.gtimg.cn"
TENCENT_IFZQ_URL = "http://ifzq.gtimg.cn"
HTTP_TIMEOUT_SHORT = 5
HTTP_TIMEOUT_LONG = 15

# WAL 模式（按 v1 6/1 教训：database locked 修复）
WAL_MODE_ENABLED = True

# 监控阈值（v1 L62 教训：必须动态化，从池加载器读）
DEFAULT_MIN_DAY_COUNT = 10
DEFAULT_MAX_DELAY_MINUTES = 80
DEFAULT_ALERT_COOLDOWN_SECONDS = 3600  # 1h
DEFAULT_BASE_URL = "qt.gtimg.cn"

# ETF 池（v1 6/17 v9-us002-pool-db-sot）
DEFAULT_ETF_POOL_SIZE = 14
DEFAULT_REFERENCE_POOL_SIZE = 40