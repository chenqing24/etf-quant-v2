"""
universe/filter.py — ETF 池筛选器（v2 universe 模块）

用途：
    提供各种 ETF 池筛选规则：
    - 行业过滤（金融/科技/消费/医药等）
    - 主题过滤（红利/低波/价值/成长）
    - 规模过滤（成交额/总市值）
    - 时间过滤（上市日期/数据起始日）

被谁调用：
    - etf-research skill（因子研究）
    - stock-portfolio skill（组合构建）
"""
from __future__ import annotations

from typing import List
from .loader import ETFListLoader, ETFInfo


class UniverseFilter:
    """ETF 池筛选器"""

    def __init__(self, loader: ETFListLoader = None):
        self.loader = loader or ETFListLoader()

    def by_category(self, category: str) -> List[ETFInfo]:
        """按行业分类筛选"""
        return [
            e for e in self.loader.load_all()
            if e.category == category
        ]

    def by_pool_role(self, role: str) -> List[ETFInfo]:
        """按池角色筛选（core/reference/excluded）"""
        return [
            e for e in self.loader.load_all()
            if e.pool_role == role
        ]

    def by_tradable(self, tradable: bool = True) -> List[ETFInfo]:
        """按是否可交易筛选"""
        return [
            e for e in self.loader.load_all()
            if e.tradable == tradable
        ]

    def by_code_prefix(self, prefix: str) -> List[ETFInfo]:
        """按代码前缀筛选（5=沪市，1=深市）"""
        return [
            e for e in self.loader.load_all()
            if e.code.startswith(prefix)
        ]

    def tradable_core_count(self) -> int:
        """可交易核心池数量（监控用）"""
        return len(self.loader.get_core_pool())
