"""
universe/mapper.py — 行业映射器（v2 universe 模块）

用途：
    提供 ETF code → 行业分类的映射（用于 stock-analyze 占位符实现）
"""
from __future__ import annotations

from typing import Dict
from .loader import ETFListLoader


class IndustryMapper:
    """行业映射器"""

    def __init__(self, loader: ETFListLoader = None):
        self.loader = loader or ETFListLoader()

    def get_industry_of(self, code: str) -> str:
        """获取单只 ETF 的行业分类"""
        mapping = self.loader.get_industry_mapping()
        return mapping.get(code, "未分类")

    def get_all_industries(self) -> Dict[str, list]:
        """获取所有行业 → ETF code 列表"""
        result: Dict[str, list] = {}
        for e in self.loader.load_all():
            cat = e.category or "未分类"
            result.setdefault(cat, []).append(e.code)
        return result

    def get_peers(self, code: str) -> list:
        """获取同行业的所有 ETF codes"""
        industry = self.get_industry_of(code)
        return self.get_all_industries().get(industry, [])
