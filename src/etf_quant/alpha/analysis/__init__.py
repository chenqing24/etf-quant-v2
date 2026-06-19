"""
alpha/analysis/__init__.py — alpha 分析子包
"""
from etf_quant.alpha.analysis.batch_ic import (
    BatchICEvaluator,
    ICResult,
    calculate_ic,
    calculate_ir,
)

__all__ = ["BatchICEvaluator", "ICResult", "calculate_ic", "calculate_ir"]
