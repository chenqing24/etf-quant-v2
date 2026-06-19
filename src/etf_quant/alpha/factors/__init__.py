"""
alpha/factors/__init__.py — 27 因子注册入口（US-013）

按规则 11（先调研再实现）+ 规则 14（架构改造有回归测试）：
    - 27 因子 = 26 继承（v1 业界标准公式）+ 1 W4 RV（v9 唯一稳健新写）
    - 工厂模式：FACTOR_REGISTRY[name] -> Factor class
    - 列表模式：ALL_FACTORS 顺序遍历

业界参考（按规则 13）：
    - WorldQuant 101 Alphas (Kakushadze 2016) 因子注册表模式
    - QuantConnect LEAN FactorFile
"""
from __future__ import annotations

from etf_quant.alpha.factor_base import (
    Factor,
    FactorCategory,
    FactorMetadata,
    FactorResult,
    validate_factor_result,
)
from etf_quant.alpha.factors.b1_boll import B1BollUpperFactor
from etf_quant.alpha.factors.inherited import (
    M1Momentum3dFactor,
    M2Momentum5dFactor,
    M3Momentum10dFactor,
    M4RSIFactor,
    M5KDJFactor,
    M6MACDdiffFactor,
    N1Reversal3dFactor,
    N2Reversal5dFactor,
    N3RSIOversoldFactor,
    O1CCIFactor,
    O2WRFactor,
    R1RelativeFactor,
    S1VHFFactor,
    S2ADXStrengthFactor,
    T2MABullFactor,
    T3SARTrendFactor,
    T4ADXTrendFactor,
    V2OBVFactor,
    V3MAOBVFactor,
    V4VolumeRatioFactor,
    W1ATRFactor,
    W2BollWidthFactor,
    W3VolatilityFactor,
)
from etf_quant.alpha.factors.t1_macd import T1MACDbarFactor
from etf_quant.alpha.factors.v1_volume import V1VolumeFactor
from etf_quant.alpha.factors.w4_rv import W4RVFactor

# 27 因子注册表（key: 因子名, value: Factor 类）
FACTOR_REGISTRY: dict[str, type[Factor]] = {
    # 趋势类 (4)
    "T1_macd_bar": T1MACDbarFactor,
    "T2_ma_bull": T2MABullFactor,
    "T3_sar_trend": T3SARTrendFactor,
    "T4_adx_trend": T4ADXTrendFactor,
    # 动量类 (6)
    "M1_momentum_3d": M1Momentum3dFactor,
    "M2_momentum_5d": M2Momentum5dFactor,
    "M3_momentum_10d": M3Momentum10dFactor,
    "M4_rsi": M4RSIFactor,
    "M5_kdj": M5KDJFactor,
    "M6_macd_diff": M6MACDdiffFactor,
    # 量能类 (4)
    "V1_volume": V1VolumeFactor,
    "V2_obv": V2OBVFactor,
    "V3_maobv": V3MAOBVFactor,
    "V4_volume_ratio": V4VolumeRatioFactor,
    # 波动类 (4)
    "W1_atr": W1ATRFactor,
    "W2_boll_width": W2BollWidthFactor,
    "W3_volatility": W3VolatilityFactor,
    "B1_boll_upper": B1BollUpperFactor,
    "W4_rv": W4RVFactor,  # v9 唯一稳健新写
    # 趋势强度 (2)
    "S1_vhf": S1VHFFactor,
    "S2_adx": S2ADXStrengthFactor,
    # 超买超卖 (2)
    "O1_cci": O1CCIFactor,
    "O2_wr": O2WRFactor,
    # 相对强弱 (1)
    "R1_relative": R1RelativeFactor,
    # 反转类 (3)
    "N1_reversal_3d": N1Reversal3dFactor,
    "N2_reversal_5d": N2Reversal5dFactor,
    "N3_rsi_oversold": N3RSIOversoldFactor,
}

# 顺序列表（保证计算可重复）
ALL_FACTORS: list[type[Factor]] = list(FACTOR_REGISTRY.values())

# 验证：必须是 27 个
assert len(ALL_FACTORS) == 27, f"Expected 27 factors, got {len(ALL_FACTORS)}: {[f.__name__ for f in ALL_FACTORS]}"


def get_factor(name: str) -> Factor:
    """根据因子名获取因子实例。"""
    if name not in FACTOR_REGISTRY:
        raise KeyError(f"Unknown factor: {name}. Available: {list(FACTOR_REGISTRY.keys())}")
    return FACTOR_REGISTRY[name]()


def list_factors() -> list[str]:
    """列出所有 27 因子名。"""
    return list(FACTOR_REGISTRY.keys())


__all__ = [
    "Factor",
    "FactorCategory",
    "FactorMetadata",
    "FactorResult",
    "validate_factor_result",
    "B1BollUpperFactor",
    "V1VolumeFactor",
    "T1MACDbarFactor",
    "T2MABullFactor",
    "T3SARTrendFactor",
    "T4ADXTrendFactor",
    "M1Momentum3dFactor",
    "M2Momentum5dFactor",
    "M3Momentum10dFactor",
    "M4RSIFactor",
    "M5KDJFactor",
    "M6MACDdiffFactor",
    "V2OBVFactor",
    "V3MAOBVFactor",
    "V4VolumeRatioFactor",
    "W1ATRFactor",
    "W2BollWidthFactor",
    "W3VolatilityFactor",
    "W4RVFactor",
    "S1VHFFactor",
    "S2ADXStrengthFactor",
    "O1CCIFactor",
    "O2WRFactor",
    "R1RelativeFactor",
    "N1Reversal3dFactor",
    "N2Reversal5dFactor",
    "N3RSIOversoldFactor",
    "FACTOR_REGISTRY",
    "ALL_FACTORS",
    "get_factor",
    "list_factors",
]
