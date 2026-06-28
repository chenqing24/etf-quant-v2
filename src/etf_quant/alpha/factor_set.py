"""
alpha/factor_set.py — 因子子集（Layer 1 灵活层，D-013 设计）

用途：
    从 FACTOR_REGISTRY（27 因子池）中按业务需要选子集。
    与 FACTOR_REGISTRY 解耦：池是稳定的，子集是动态的。

被谁调用：
    - src/etf_quant/alpha/scoring.py（CrossSectionalScorer 接收 factor_set）
    - src/etf_quant/alpha/weight_scheme.py（WeightScheme 校验权重键在 factor_set 中）
    - tests/unit/alpha/test_factor_set.py（单测）

设计原则（按规则 13 业界参考）：
    - WorldQuant 101 Alphas (Kakushadze 2016): 101 个 alpha 公式构成因子池，按需组合
    - Qlib Alpha158 (microsoft/qlib): 因子池 + 数据 Handler 解耦
    - QuantConnect LEAN FineSelection: 全集 + 选股抽象

业务约束：
    - 所有 factor_names 必须在 FACTOR_REGISTRY 中（不存在 → 报错而非静默）
    - 不允许空集（至少 1 个因子）
    - 名称重复自动去重
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from etf_quant.alpha.factors import FACTOR_REGISTRY


@dataclass(frozen=True)
class FactorSet:
    """因子子集（从 FACTOR_REGISTRY 池中选）。

    Attributes:
        name: 子集名称（用于 logging / 配置定位 / 缓存键）
        factor_names: 因子名列表（必须在 FACTOR_REGISTRY 中）

    Example:
        >>> fs = FactorSet.eight_factor_v2()
        >>> fs.name
        'eight_factor_v2'
        >>> len(fs.factor_names)
        8
        >>> "DMA" in fs.factor_names  # 注意：DMA 当前不在 FACTOR_REGISTRY
        False
    """

    name: str
    factor_names: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # 1. 非空校验
        if not self.factor_names:
            raise ValueError(f"FactorSet '{self.name}' 不能为空集")

        # 2. 去重（保持顺序）
        seen = set()
        deduped = []
        for fname in self.factor_names:
            if fname not in seen:
                seen.add(fname)
                deduped.append(fname)
        # frozen=True 不能直接赋值，用 object.__setattr__
        object.__setattr__(self, "factor_names", tuple(deduped))

        # 3. 池存在性校验（不允许未知因子）
        unknown = [f for f in self.factor_names if f not in FACTOR_REGISTRY]
        if unknown:
            raise ValueError(
                f"FactorSet '{self.name}' 包含未知因子 {unknown}。"
                f"已知因子（前 5 个）：{list(FACTOR_REGISTRY.keys())[:5]}..."
            )

    def __iter__(self) -> Iterator[str]:
        return iter(self.factor_names)

    def __len__(self) -> int:
        return len(self.factor_names)

    def __contains__(self, factor_name: str) -> bool:
        return factor_name in self.factor_names

    def get_factor_classes(self) -> dict[str, type]:
        """返回 {factor_name: Factor class}（用于实例化）"""
        return {name: FACTOR_REGISTRY[name] for name in self.factor_names}

    def to_dict(self) -> dict:
        """导出为 dict（JSON 序列化用）"""
        return {"name": self.name, "factor_names": list(self.factor_names)}

    @classmethod
    def from_dict(cls, data: dict) -> "FactorSet":
        """从 dict 还原"""
        return cls(name=data["name"], factor_names=tuple(data["factor_names"]))

    @classmethod
    def eight_factor_v2(cls) -> "FactorSet":
        """D-004 精选 8 因子（v2 SOP 落地版）。

        注意：当前 FACTOR_REGISTRY 27 因子中只有 6 个直接对应 D-004：
            - W2_boll_width ✓
            - B1_boll_upper ✓
            - M4_rsi ✓
            - V2_obv ✓
            - V3_maobv ✓
            - M2_momentum_5d ✓
        DMA / FIB 当前不在 FACTOR_REGISTRY（D-013 后续补，或在 Scorer 内部特判）。

        Returns:
            FactorSet(name="eight_factor_v2", 6 因子 in registry)
        """
        # 暂时返回 6 因子（registry 已有的），DMA/FIB 在 Scorer 内部特殊处理
        return cls(
            name="eight_factor_v2",
            factor_names=(
                "W2_boll_width",
                "B1_boll_upper",
                "M4_rsi",
                "V2_obv",
                "V3_maobv",
                "M2_momentum_5d",
            ),
        )

    @classmethod
    def all_registered(cls) -> "FactorSet":
        """全 27 因子（用于 IC/IR 批量评估、研究场景）"""
        return cls(name="all_registered", factor_names=tuple(FACTOR_REGISTRY.keys()))


__all__ = ["FactorSet"]