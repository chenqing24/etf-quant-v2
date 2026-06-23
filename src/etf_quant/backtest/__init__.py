"""
etf_quant/backtest — 回测验证模块

用途：综合回测验证（v2 28 因子全 IC/IR 评估 + PBO 防过拟合）。
被谁调用：etf-research skill / quantor-onboard alpha 块 / IC 季度巡检。

子模块：
    - comprehensive_validator: ComprehensiveValidator（v2 28 因子综合回测）

入口示例：
    from etf_quant.backtest import ComprehensiveValidator
    validator = ComprehensiveValidator(db_path="/path/etf.db")
    result = validator.validate(...)
"""
from etf_quant.backtest.comprehensive_validator import (
    ComprehensiveValidator,
    ComprehensiveResult,
)

__all__ = ["ComprehensiveValidator", "ComprehensiveResult"]
