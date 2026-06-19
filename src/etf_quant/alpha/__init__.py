"""
etf_quant/alpha — 信号/因子（v2 27 因子，US-013 完成）

子模块：
    - factor_base: 因子抽象基类（Factor / FactorCategory / FactorResult）
    - factors: 27 因子注册（26 继承 + 1 W4 RV）
    - analysis.batch_ic: IC/IR 批量评估
    - strategy_c21: C21-1 金三角策略（US-007 已完成）

入口：
    from etf_quant.alpha.factors import get_factor, list_factors
    from etf_quant.alpha.analysis import BatchICEvaluator
    from etf_quant.alpha.strategy_c21 import C21Strategy
"""
from etf_quant.alpha.factors import ALL_FACTORS, FACTOR_REGISTRY, get_factor, list_factors

__all__ = ["ALL_FACTORS", "FACTOR_REGISTRY", "get_factor", "list_factors"]
