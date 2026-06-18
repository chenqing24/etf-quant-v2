"""
v2 配置常量（从 v1 src/constants.py 继承）。
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

# WAL 模式（按 v1 6/1 教训：database locked 修复）
WAL_MODE_ENABLED = True

# 监控阈值（v1 L62 教训：必须动态化，从池加载器读）
# 默认值仅作为兜底
DEFAULT_MIN_DAY_COUNT = 10
DEFAULT_MAX_DELAY_MINUTES = 80
DEFAULT_ALERT_COOLDOWN_SECONDS = 3600  # 1h
DEFAULT_BASE_URL = "qt.gtimg.cn"

# ETF 池（v1 6/17 v9-us002-pool-db-sot）
DEFAULT_ETF_POOL_SIZE = 14
DEFAULT_REFERENCE_POOL_SIZE = 40