"""
alpha/factors/__init__.py — 28 因子注册入口（US-013，2026-06-21 加 T5_ma5）

按规则 11（先调研再实现）+ 规则 14（架构改造有回归测试）：
    - 27 因子 = 25 继承（v1 业界标准公式，US-002 删 M6_macd_diff 重复）+ 1 W4 RV（v9 唯一稳健新写）+ 1 T5_ma5（散户新加）
    - 工厂模式：FACTOR_REGISTRY[name] -> Factor class
    - 列表模式：ALL_FACTORS 顺序遍历

被谁调用（按规则 18 / v1 L118）：
    - src/etf_quant/alpha/registry.py（向后兼容导出）
    - src/etf_quant/backtest/comprehensive_validator.py（4 验证器跑单因子综合分）
    - src/etf_quant/alpha/analysis/batch_ic.py（批量 IC 计算）
    - tests/unit/test_factors.py（27+1 因子单测）
    - skills/quantor-onboard/scripts/run_alpha.py（散户 alpha 引导）
    - skills/quantor-onboard/scripts/business_check.py（业务自评因子数校验）

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
from etf_quant.alpha.factors.t5_ma5 import T5MA5Factor  # 散户新加（2026-06-21 Sprint-7 后补）
from etf_quant.alpha.factors.v1_volume import V1VolumeFactor
from etf_quant.alpha.factors.w4_rv import W4RVFactor

# 27 因子注册表（key: 因子名, value: Factor 类）
FACTOR_REGISTRY: dict[str, type[Factor]] = {
    # 趋势类 (4)
    "T1_macd_bar": T1MACDbarFactor,
    "T2_ma_bull": T2MABullFactor,
    "T3_sar_trend": T3SARTrendFactor,
    "T4_adx_trend": T4ADXTrendFactor,
    "T5_ma5": T5MA5Factor,  # 散户新加（2026-06-21）
    # 动量类 (6)
    "M1_momentum_3d": M1Momentum3dFactor,
    "M2_momentum_5d": M2Momentum5dFactor,
    "M3_momentum_10d": M3Momentum10dFactor,
    "M4_rsi": M4RSIFactor,
    "M5_kdj": M5KDJFactor,
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
    "S2_adx_strength": S2ADXStrengthFactor,
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

# 28 因子业界别名表（规则 28：每个因子至少 1 个业界通用缩写）
ALIASES_REGISTRY: dict[str, list[str]] = {
    "T1_macd_bar": ["MACD", "MACD红柱", "MACD_hist", "MACD柱"],
    "T2_ma_bull": ["MA20", "MA20多头", "MA_BULL"],
    "T3_sar_trend": ["SAR", "抛物线", "MA10代理"],
    "T4_adx_trend": ["ADX", "ADX趋势", "DMI趋势"],
    "T5_ma5": ["MA5", "5日均线", "MA_5"],
    "M1_momentum_3d": ["MOM_3D", "3日动量", "ROC_3"],
    "M2_momentum_5d": ["MOM_5D", "5日动量", "ROC_5"],
    "M3_momentum_10d": ["MOM_10D", "10日动量", "ROC_10"],
    "M4_rsi": ["RSI", "RSI(14)", "Relative Strength Index"],
    "M5_kdj": ["KDJ", "KDJ_K", "随机指标"],    "V1_volume": ["VOL", "成交量", "VOL_MA5"],
    "V2_obv": ["OBV", "能量潮", "On Balance Volume"],
    "V3_maobv": ["OBV_MA", "OBV均线", "OBV_MA20"],
    "V4_volume_ratio": ["V_RATIO", "量比", "VR"],
    "W1_atr": ["ATR", "ATR(14)", "真实波幅"],
    "W2_boll_width": ["BOLL_W", "布林带宽", "BW"],
    "W3_volatility": ["VOLAT", "波动率", "STD_20"],
    "W4_rv": ["RV", "已实现波动率变化", "Realized Vol"],
    "B1_boll_upper": ["BOLL_UP", "布林上轨", "Bollinger Upper"],
    "S1_vhf": ["VHF", "垂直水平过滤", "Vertical Horizontal Filter"],
    "S2_adx_strength": ["ADX_S", "ADX强度", "ADX归一化"],
    "O1_cci": ["CCI", "CCI(20)", "顺势指标"],
    "O2_wr": ["WR", "WR(14)", "Williams %R", "威廉指标"],
    "R1_relative": ["RPS", "RS", "相对强弱"],
    "N1_reversal_3d": ["REVERSAL_3D", "3日反转", "均值回归_3D"],
    "N2_reversal_5d": ["REVERSAL_5D", "5日反转", "均值回归_5D"],
    "N3_rsi_oversold": ["RSI_OS", "RSI超卖", "RSI_Oversold"],
}

# 因子 legacy 映射表（规则 21 + US-002）：
#   - M6_macd_diff: 公式与 T1_macd_bar 完全重复（DIF - DEA = MACD 红柱），删除
#   - S2_adx: 改名 S2_adx_strength 以区分 T4_adx_trend
# 旧选择自动迁移到新名（alpha_state.json 兼容）
LEGACY_FACTOR_MAP: dict[str, str] = {
    "M6_macd_diff": "T1_macd_bar",      # 公式等价：MACD 柱
    "S2_adx": "S2_adx_strength",        # 改名以区分 T4
}


def migrate_legacy_factor_name(old_name: str) -> str:
    """迁移用户旧因子名到新名（用于 alpha_state.json 兼容）。"""
    return LEGACY_FACTOR_MAP.get(old_name, old_name)


# 顺序列表（保证计算可重复）
ALL_FACTORS: list[type[Factor]] = list(FACTOR_REGISTRY.values())

# 验证：必须是 27 个
assert len(ALL_FACTORS) == 27, f"Expected 27 factors (US-002 删 M6_macd_diff 重复后), got {len(ALL_FACTORS)}: {[f.__name__ for f in ALL_FACTORS]}"


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
    "ALIASES_REGISTRY",
    "LEGACY_FACTOR_MAP",
    "migrate_legacy_factor_name",
    "get_factor",
    "list_factors",
]
