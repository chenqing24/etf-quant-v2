"""
test_constants_and_source.py — constants + execution_source 单元测试

按 v1 教训 L112（DB_PATH 绝对路径）+ L101（执行源强制标识）。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class TestConstants:
    """L112 教训：DB_PATH 必须绝对路径。"""

    def test_db_path_is_absolute(self):
        from etf_quant.config import constants
        assert os.path.isabs(constants.DB_PATH), \
            f"DB_PATH 必须是绝对路径（按 L112 教训），实际: {constants.DB_PATH}"

    def test_data_dir_exists_or_creatable(self):
        from etf_quant.config import constants
        # DATA_DIR 父目录应该可创建
        assert constants.DATA_DIR.parent.exists(), \
            f"父目录不存在: {constants.DATA_DIR}"

    def test_wal_mode_enabled(self):
        from etf_quant.config import constants
        assert constants.WAL_MODE_ENABLED is True, "WAL 模式应启用（v1 6/1 教训）"

    def test_default_min_day_count_10(self):
        from etf_quant.config import constants
        # v1 6/2 monitor 修复后 min_day_count 动态化，默认兜底 10
        assert constants.DEFAULT_MIN_DAY_COUNT == 10

    def test_default_max_delay_minutes_80(self):
        from etf_quant.config import constants
        # v1 分钟级监控 80 分钟阈值
        assert constants.DEFAULT_MAX_DELAY_MINUTES == 80

    def test_alert_cooldown_1h(self):
        from etf_quant.config import constants
        # L222 教训：cron 推送分流
        assert constants.DEFAULT_ALERT_COOLDOWN_SECONDS == 3600


class TestExecutionSource:
    """L101 教训：多执行源无标识 = 串扰。"""

    def test_sources_enum(self):
        from etf_quant.utils.execution_source import ExecutionSource
        sources = [s.value for s in ExecutionSource]
        assert "skill" in sources
        assert "cron" in sources
        assert "manual" in sources
        assert "cli" in sources
        assert "test" in sources

    def test_default_is_unknown(self):
        from etf_quant.utils.execution_source import (
            ExecutionSource, get_source, clear,
        )
        clear()
        assert get_source() == ExecutionSource.UNKNOWN

    def test_set_and_get_source(self):
        from etf_quant.utils.execution_source import (
            ExecutionSource, get_source, set_source, clear,
        )
        clear()
        set_source(ExecutionSource.SKILL, agent_id="test-agent")
        assert get_source() == ExecutionSource.SKILL
        clear()

    def test_require_source_raises_when_unknown(self):
        from etf_quant.utils.execution_source import (
            ExecutionSource, require_source, clear,
        )
        clear()
        # 清空环境变量
        old_env = os.environ.pop("ETF_QUANT_SOURCE", None)
        try:
            with pytest.raises(Exception) as exc_info:
                require_source()
            assert "执行源未标识" in str(exc_info.value) or "source" in str(exc_info.value).lower()
        finally:
            if old_env:
                os.environ["ETF_QUANT_SOURCE"] = old_env
            clear()

    def test_require_source_succeeds_when_set(self):
        from etf_quant.utils.execution_source import (
            ExecutionSource, require_source, set_source, clear,
        )
        clear()
        set_source(ExecutionSource.CRON, agent_id="cron-1")
        src = require_source()
        assert src == ExecutionSource.CRON
        clear()

    def test_environment_variable_fallback(self):
        from etf_quant.utils.execution_source import (
            ExecutionSource, require_source, clear,
        )
        clear()
        old_env = os.environ.get("ETF_QUANT_SOURCE")
        os.environ["ETF_QUANT_SOURCE"] = "manual"
        try:
            src = require_source()
            assert src == ExecutionSource.MANUAL
        finally:
            if old_env:
                os.environ["ETF_QUANT_SOURCE"] = old_env
            else:
                os.environ.pop("ETF_QUANT_SOURCE", None)
            clear()
