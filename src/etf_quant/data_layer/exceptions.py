"""
v2 数据层异常（从 v1 src/data/exceptions.py 继承）。
"""
from __future__ import annotations


class DataValidationError(Exception):
    """数据验证失败（按 v1 DataWriter 模式）。"""

    def __init__(self, errors: list[str], source: str = "") -> None:
        self.errors = errors
        self.source = source
        super().__init__(f"DataValidationError in {source}: {errors}")


class DataLayerError(Exception):
    """数据层通用错误。"""


class SchemaVersionError(DataLayerError):
    """schema 版本不匹配（v2 新增）。"""


class ExecutionSourceError(DataLayerError):
    """执行源未标识（L101 教训）。"""