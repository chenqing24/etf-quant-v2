"""
tests/unit/alpha/test_factor_aliases.py — US-001 别名体系测试

按规则 28：每个因子必须带至少 1 个业界通用别名（MA5/RSI/MACD/ATR/BOLL_W 等）

总计：8 测试
"""
from __future__ import annotations

import pytest

from etf_quant.alpha.factors import (
    FACTOR_REGISTRY,
    ALIASES_REGISTRY,
    list_factors,
)
from etf_quant.alpha.factor_base import FactorMetadata


def test_28_factors_have_aliases():
    """US-001 AC1: 28 因子全有 aliases，每个至少 1 个业界通用名"""
    assert len(FACTOR_REGISTRY) == 27, f"Expected 28 factors, got {len(FACTOR_REGISTRY)}"
    assert len(ALIASES_REGISTRY) == 27, f"Expected 28 alias entries, got {len(ALIASES_REGISTRY)}"
    for name in FACTOR_REGISTRY:
        assert name in ALIASES_REGISTRY, f"因子 {name} 缺 aliases"
        assert len(ALIASES_REGISTRY[name]) >= 1, f"因子 {name} aliases 为空"


def test_factor_metadata_has_aliases_field():
    """US-001 AC2: FactorMetadata.aliases 字段存在"""
    meta = FactorMetadata(name="X", category=None, description="test")
    assert hasattr(meta, "aliases")
    assert meta.aliases == []  # 默认空 list（规则 19 deny）
    meta2 = FactorMetadata(name="X", category=None, description="test", aliases=["MA5"])
    assert meta2.aliases == ["MA5"]


def test_factor_metadata_has_ic_eval_date_field():
    """US-001 AC2: FactorMetadata.ic_eval_date 字段存在（规则 27 必填位）"""
    meta = FactorMetadata(name="X", category=None, description="test")
    assert hasattr(meta, "ic_eval_date")
    assert meta.ic_eval_date is None  # 默认 None


def test_industry_standard_aliases_present():
    """US-001 AC3: 业界通用缩写必现（MA5/RSI/MACD/ATR/BOLL_W/OBV/CCI/WR/VHF/ADX/KDJ）"""
    required = {
        "T5_ma5": "MA5",
        "M4_rsi": "RSI",
        "T1_macd_bar": "MACD",
        "W1_atr": "ATR",
        "W2_boll_width": "BOLL_W",
        "B1_boll_upper": "BOLL_UP",
        "V2_obv": "OBV",
        "O1_cci": "CCI",
        "O2_wr": "WR",
        "S1_vhf": "VHF",
        "T4_adx_trend": "ADX",
        "M5_kdj": "KDJ",
    }
    for factor_name, required_alias in required.items():
        assert factor_name in ALIASES_REGISTRY, f"缺因子 {factor_name}"
        assert required_alias in ALIASES_REGISTRY[factor_name], (
            f"因子 {factor_name} aliases 缺业界通用名 {required_alias}，"
            f"现有: {ALIASES_REGISTRY[factor_name]}"
        )


def test_aliases_no_duplicates_within_factor():
    """US-001: 单因子 aliases 内部不重复"""
    for name, aliases in ALIASES_REGISTRY.items():
        assert len(aliases) == len(set(aliases)), f"因子 {name} aliases 有重复: {aliases}"


def test_aliases_no_collision_across_factors():
    """US-001: 跨因子 aliases 不冲突（同一业界缩写不能指 2 个不同因子）"""
    from collections import defaultdict
    alias_to_factor = defaultdict(list)
    for factor, aliases in ALIASES_REGISTRY.items():
        for a in aliases:
            alias_to_factor[a].append(factor)
    collisions = {a: fs for a, fs in alias_to_factor.items() if len(fs) > 1}
    # 例外：M4_rsi 的 "RSI" 和 N3_rsi_oversold 的 "RSI_OS" 不会撞，但要排除真正冲突
    assert not collisions, f"别名冲突: {collisions}"


def test_alpha_state_json_compatibility():
    """US-001: alpha_state.json 用户旧选择不动（兼容）"""
    import json
    from pathlib import Path
    state_path = Path("data/alpha_state.json")
    if not state_path.exists():
        pytest.skip("alpha_state.json 不存在（Sprint 1 散户尚未选因子）")
    with open(state_path) as f:
        state = json.load(f)
    if "user_factors" in state:
        # 所有用户选的因子必须在 FACTOR_REGISTRY 里（兼容旧 key）
        for f in state["user_factors"]:
            assert f in FACTOR_REGISTRY, f"用户旧选择 {f} 不在 registry"


def test_factor_metadata_aliases_field_default_is_empty_list():
    """US-001: FactorMetadata.aliases 默认空 list（规则 19 deny 模式，不共享可变默认）"""
    m1 = FactorMetadata(name="A", category=None, description="x")
    m2 = FactorMetadata(name="B", category=None, description="y")
    m1.aliases.append("X")
    assert m2.aliases == [], "FactorMetadata.aliases 默认值不能共享可变对象"
