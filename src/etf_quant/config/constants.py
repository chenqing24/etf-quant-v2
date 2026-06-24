"""
v2 配置常量（从 v1 src/constants.py 继承）。

用途：
    v2 系统的统一配置中心：
    - DB_PATH 绝对路径（L112 教训 + L321 教训：相对路径会被 cwd 污染）
    - resolve_db_path() 工具函数（兜底 cwd 漂移 + ETF_QUANT_DB_PATH 覆盖）
    - WAL 模式启用（v1 6/1 教训：database locked 修复）
    - 数据/监控/调度/ETF 池的默认值
    - v1 兼容字段（TRADES_FILE/TENCENT_QT_URL/HTTP_TIMEOUT_*）

被谁调用：
    - src/etf_quant/data_layer/（writer.py / loader.py / monitor.py）
    - src/etf_quant/execution/（tracker.py US-008 JSON 兼容）
    - src/etf_quant/monitor/（默认值兜底）
    - tests/integration/（init_database_regression 临时覆盖）
    - skills/etf-daily/scripts/run_daily.py（resolve_db_path 入口）

功能说明：
    - _PROJECT_ROOT 路径计算（按 L112 必须绝对）
    - DATA_DIR / DB_PATH / SCHEMA_DIR 三大目录
    - resolve_db_path() 工具函数（L321 教训）
    - WAL_MODE_ENABLED = True（v1 6/1 修复）
    - DEFAULT_* 监控阈值（v1 L62 教训：动态化兜底）

使用方式：
    from etf_quant.config import constants
    db_path = constants.DB_PATH  # 绝对路径（项目根 data/etf.db）
    # 或
    from etf_quant.config.constants import resolve_db_path
    db_path = resolve_db_path()  # 兜底 cwd 漂移

依赖：
    - 无（纯常量）
    - L112 教训（DB_PATH 绝对路径）
    - L62 教训（监控阈值动态化兜底）
    - L321 教训（run_daily 相对路径导致 cwd 漂移到空库）
    - v1 6/1 教训（WAL 模式）

注意事项：
    - 不要硬编码其他常量（违反 v1 L211 教训：机制层 > AI 自觉）
    - 临时测试覆盖用 ETF_QUANT_DB_PATH 环境变量（L236 教训）
    - v1 兼容字段保留到 v2 完全迁移后删除
    - resolve_db_path() 优先用 ETF_QUANT_DB_PATH 环境变量，其次 DB_PATH
"""
from __future__ import annotations

import os
from pathlib import Path

# 项目根（PROJECT_ROOT = v2 仓根 = src/etf_quant/ 的祖父目录）
# 不依赖 cwd（按 L112 教训：DB_PATH 必须绝对路径）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = _PROJECT_ROOT / "data"
DB_NAME = "etf.db"
DB_PATH = str(DATA_DIR / DB_NAME)
SCHEMA_DIR = _PROJECT_ROOT / "schema" / "migrations"


def resolve_db_path(override: str | None = None) -> str:
    """解析数据库路径（兜底 cwd 漂移 + 环境变量覆盖）。

    优先级（按 L321 教训）：
        1. 调用方显式 override 参数
        2. 环境变量 ETF_QUANT_DB_PATH（测试/集成用，L236 教训）
        3. constants.DB_PATH（项目根 data/etf.db，绝对路径）
        4. 同级目录的 data/etf.db（兜底 cwd 在仓库根或父目录）

    Args:
        override: 调用方显式指定的 db 路径（最高优先级）

    Returns:
        绝对路径字符串（保证 sqlite3.connect 能找到正确 db）

    业界参考：
        - Python pathlib 官方文档：Path.resolve() 锚定文件位置
        - pytest conftest.py 最佳实践：用 __file__ 锚定 rootdir
        - 12-Factor App § III Config：默认值应在开发环境直接可用

    L321 教训：run_daily.py 接受 --db-path data/etf.db（相对路径）时，
    若 cwd 在顶层（空 etf.db 所在），会连接到空库导致 "no such table"。
    本函数通过回退到项目根 data/etf.db 解决。
    """
    if override:
        p = Path(override)
        if p.is_absolute():
            return str(p)
        # 相对路径：先尝试 cwd，再回退到项目根
        if p.exists():
            return str(p.resolve())
        project_db = _PROJECT_ROOT / p
        if project_db.exists():
            return str(project_db)
        return str(p.resolve())  # 不存在时返回解析后的路径，调用方会看到错误

    env_path = os.environ.get("ETF_QUANT_DB_PATH")
    if env_path:
        return env_path  # 环境变量就是绝对路径（约定）

    return DB_PATH

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
DEFAULT_MAX_DELAY_MINUTES = 1500  # 25h：A 股收盘 15:00 后数据停更到次日 9:30，间隔 18.5h
DEFAULT_ALERT_COOLDOWN_SECONDS = 3600  # 1h
DEFAULT_BASE_URL = "qt.gtimg.cn"

# ETF 池（v1 6/17 v9-us002-pool-db-sot）
DEFAULT_ETF_POOL_SIZE = 14
DEFAULT_REFERENCE_POOL_SIZE = 40