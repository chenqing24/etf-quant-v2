"""
universe/loader.py — ETF 池加载器（v2 universe 模块，US-012）

用途：
    从 SQLite 加载 ETF 池元数据（通过 ETFRepository + ETFNameLoader）。

被谁调用：
    - etf-daily skill 入口
    - monitor 模块（数据健康检查）
    - performance 模块（基准对比）
    - 任何需要"全市场 ETF 列表"的模块

功能说明：
    - ETFListLoader：组合 ETFRepository + ETFNameLoader
    - get_core_pool()：返回 tradable=1 + pool_role='core' 的 14 只
    - get_reference_pool()：返回 pool_role='reference' 的 300 只
    - 业务层零 SQL（规则 15）

使用方式：
    from etf_quant.universe.loader import ETFListLoader
    loader = ETFListLoader()
    codes = loader.get_tradable_codes()
    print(f'可交易: {len(codes)} 只')

依赖：
    - etf_quant.data_layer.etf_pool_repository.ETFRepository
    - etf_quant.data_layer.loader.ETFNameLoader

注意事项：
    - 业务层零 SQL（用 Repository，规则 15）
    - pool_role 默认 'unclassified'（规则 19：宁严勿宽）
    - tradable 默认 0（必须显式标 1）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional

from etf_quant.config.constants import DATA_DIR, DB_NAME

from etf_quant.data_layer.etf_pool_repository import ETFRepository
from etf_quant.data_layer.loader import ETFNameLoader


@dataclass
class ETFInfo:
    """ETF 元数据（v2 universe 通用类型）"""
    code: str
    name: str
    pool_role: str  # core / reference / excluded / unclassified
    tradable: bool  # True = 可交易
    category: Optional[str] = None  # 宽基/行业/主题/海外（可选）


class ETFListLoader:
    """ETF 池加载器（v2 universe 核心类）"""

    def __init__(self):
        # 显式传 v2 data/etf.db 路径（避免 ETFRepository 默认 v1 路径）
        db_path = f"{DATA_DIR}/{DB_NAME}"
        self.repo = ETFRepository(db_path=db_path)
        self.name_loader = ETFNameLoader()

    def load_all(self) -> List[ETFInfo]:
        """加载所有 ETF 元数据"""
        # 列出所有 code，然后逐个查 meta
        all_codes = self.repo.all_codes()
        result = []
        for code in all_codes:
            meta = self.repo.get_meta(code)
            if not meta:
                continue
            result.append(ETFInfo(
                code=code,
                name=meta.get("name") or self.name_loader.get_name(code),
                pool_role=meta.get("pool_role", "unclassified"),
                tradable=bool(meta.get("tradable", 0)),
                category=meta.get("category"),
            ))
        return result

    def get_core_pool(self) -> List[ETFInfo]:
        """获取核心池（14 只，CORE）"""
        return [
            e for e in self.load_all()
            if e.tradable and e.pool_role == "core"
        ]

    def get_reference_pool(self) -> List[ETFInfo]:
        """获取参考池（300 只，REFERENCE）"""
        return [
            e for e in self.load_all()
            if e.pool_role == "reference"
        ]

    def get_tradable_pool(self) -> List[ETFInfo]:
        """获取可交易池（tradable=1）"""
        return [e for e in self.load_all() if e.tradable]

    def get_tradable_codes(self) -> List[str]:
        """获取可交易 code 列表"""
        return [e.code for e in self.get_tradable_pool()]

    def filter_by_codes(self, codes: List[str]) -> List[ETFInfo]:
        """按 code 列表过滤"""
        code_set = set(codes)
        return [e for e in self.load_all() if e.code in code_set]

    def get_tencent_codes(self) -> List[str]:
        """返回腾讯 API 格式（sh/sz 前缀）"""
        result = []
        for e in self.get_tradable_pool():
            if e.code.startswith("5"):
                result.append(f"sh{e.code}")
            elif e.code.startswith("1"):
                result.append(f"sz{e.code}")
        return result

    def get_industry_mapping(self) -> Dict[str, str]:
        """获取 code → category 映射"""
        return {
            e.code: e.category or "未分类"
            for e in self.load_all()
        }
