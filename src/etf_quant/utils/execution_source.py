"""
v2 执行源标识（按 L101 教训：多执行源无标识 = 串扰风险）。

强制每个写入操作携带 --source 标识：
- skill: 用户通过 skill 调用
- cron: QwenPaw cron 定时任务
- manual: 用户手动操作
- cli: CLI 直接调用
- test: 单元测试（仅测试用）
"""
from __future__ import annotations

import logging
import os
import threading
from enum import Enum
from typing import Optional

_logger = logging.getLogger("etf_quant.execution_source")


class ExecutionSource(str, Enum):
    """执行源枚举（L101 教训）。"""
    SKILL = "skill"
    CRON = "cron"
    MANUAL = "manual"
    CLI = "cli"
    TEST = "test"
    UNKNOWN = "unknown"


# 全局线程局部变量（每个线程独立）
_local = threading.local()


def set_source(source: ExecutionSource, agent_id: str = "default") -> None:
    """设置当前线程的执行源。"""
    _local.source = source
    _local.agent_id = agent_id


def get_source() -> ExecutionSource:
    """获取当前线程的执行源。"""
    return getattr(_local, "source", ExecutionSource.UNKNOWN)


def get_agent_id() -> str:
    """获取当前线程的 agent_id。"""
    return getattr(_local, "agent_id", "default")


def require_source() -> ExecutionSource:
    """强制要求有执行源（机制层强制 — L101 教训）。

    Raises:
        ExecutionSourceError: 当执行源为 UNKNOWN 时
    """
    src = get_source()
    if src == ExecutionSource.UNKNOWN:
        # 兜底：尝试从环境变量读
        env_src = os.environ.get("ETF_QUANT_SOURCE", "").lower()
        if env_src in ("skill", "cron", "manual", "cli", "test"):
            set_source(ExecutionSource(env_src))
            return get_source()
        raise ExecutionSourceError(
            "执行源未标识。调用前必须 set_source() 或设置 ETF_QUANT_SOURCE 环境变量。"
        )
    return src


def clear() -> None:
    """清除当前线程的执行源（测试用）。"""
    if hasattr(_local, "source"):
        delattr(_local, "source")
    if hasattr(_local, "agent_id"):
        delattr(_local, "agent_id")


# 入口装饰器（按 v1 命令行 --source 模式）
def with_source(func):
    """装饰器：自动从命令行参数提取 --source。"""
    import functools
    import inspect

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 从 kwargs 找 source
        source = kwargs.get("source") or os.environ.get("ETF_QUANT_SOURCE", "cli")
        try:
            set_source(ExecutionSource(source.lower()))
        except ValueError:
            _logger.warning("未知 source: %s, 降级为 CLI", source)
            set_source(ExecutionSource.CLI)
        return func(*args, **kwargs)
    return wrapper