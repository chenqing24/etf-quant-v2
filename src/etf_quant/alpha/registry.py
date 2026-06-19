"""
alpha/registry.py — 因子注册表门面（US-013）

业界参考（按规则 13）：
    - WorldQuant Brain Alpha Library 101 factors (Kakushadze 2016)
    - QuantConnect LEAN FactorFile
"""
from __future__ import annotations

from etf_quant.alpha.factors import (
    ALL_FACTORS,
    FACTOR_REGISTRY,
    get_factor,
    list_factors,
)

# 向后兼容：FACTOR_REGISTRY 已迁移至 factors/__init__.py
__all__ = ["FACTOR_REGISTRY", "ALL_FACTORS", "get_factor", "list_factors"]
