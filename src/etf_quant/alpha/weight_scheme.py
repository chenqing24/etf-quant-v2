"""
alpha/weight_scheme.py — 权重方案（Layer 2 配置层，D-013 设计）

用途：
    因子权重的强类型封装 + D-004 5 维度校验。
    从散落各处（reports JSON / backtesting 等权 / daily 占位）抽出来作为单一来源。

被谁调用：
    - src/etf_quant/alpha/scoring.py（CrossSectionalScorer 接收 weight_scheme）
    - src/etf_quant/config/eight_factor_weights.json（运行时配置）
    - tests/unit/alpha/test_weight_scheme.py（单测）

设计原则（按规则 13 业界参考）：
    - Qlib WeightStrategy（microsoft/qlib）：权重作为可插拔策略
    - López de Prado《Advances in Financial ML》Ch 11：walk-forward 权重评估
    - D-004 5 维度评分体系（IC/IR + 稳定性 + 分散性 + 经济直觉 + 可解释性）

D-004 硬约束（按 D-004_top3_weights.json SOP_D-004.md）：
    - 权重最小值 ≥ 5%（防止"伪权重"=实际删除因子）
    - 权重最大值 ≤ 40%（防止单一因子主宰）
    - 权重总和 = 1.0（归一化）
    - 8 因子全部参与（权重 > 0 等同删除，不允许）
    - trend_up / range_bound 各一套
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

# D-004 硬约束（与 SOP_D-004.md 第一章保持一致）
MIN_WEIGHT = 0.05
MAX_WEIGHT = 0.40
WEIGHT_SUM_TOLERANCE = 1e-6

SUPPORTED_MARKET_MODES = ("trend_up", "range_bound")


@dataclass(frozen=True)
class WeightScheme:
    """权重方案（D-004 5 维度评分体系强类型封装）。

    Attributes:
        scheme_id: 方案 ID（如 "B2" / "A1"）
        weights_by_mode: {market_mode: {factor_name: weight}}
            支持 market_mode：trend_up / range_bound

    Example:
        >>> ws = WeightScheme.from_d004_b2()
        >>> ws.scheme_id
        'B2'
        >>> sum(ws.weights_by_mode["trend_up"].values())
        1.0
    """

    scheme_id: str
    weights_by_mode: dict[str, dict[str, float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # 1. scheme_id 非空
        if not self.scheme_id:
            raise ValueError("WeightScheme.scheme_id 不能为空")

        # 2. weights_by_mode 非空
        if not self.weights_by_mode:
            raise ValueError(f"WeightScheme '{self.scheme_id}' 不能为空")

        # 3. 必须包含 trend_up + range_bound
        missing_modes = [m for m in SUPPORTED_MARKET_MODES if m not in self.weights_by_mode]
        if missing_modes:
            raise ValueError(
                f"WeightScheme '{self.scheme_id}' 缺少 market_mode：{missing_modes}。"
                f"必须包含：{SUPPORTED_MARKET_MODES}"
            )

        # 4. 每个 mode 做 5 维度校验
        for mode, weights in self.weights_by_mode.items():
            self._validate_mode(scheme_id=self.scheme_id, mode=mode, weights=weights)

    @staticmethod
    def _validate_mode(scheme_id: str, mode: str, weights: dict[str, float]) -> None:
        """单个 market_mode 的 D-004 5 维度校验。"""
        # 维度 1: 权重和 = 1.0
        total = sum(weights.values())
        if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
            raise ValueError(
                f"WeightScheme '{scheme_id}' / {mode}: 权重和 {total:.6f} ≠ 1.0 "
                f"(容差 {WEIGHT_SUM_TOLERANCE})"
            )

        # 维度 2: 不允许 0 权重（D-004 硬约束）— 先校验 0，让错误信息更精准
        zeros = [f for f, w in weights.items() if w == 0]
        if zeros:
            raise ValueError(
                f"WeightScheme '{scheme_id}' / {mode}: 因子 {zeros} 权重为 0 "
                f"= 删除因子（违反 D-004 8 因子全部参与原则）"
            )

        # 维度 3: 权重范围 [MIN, MAX]
        for fname, w in weights.items():
            if w < MIN_WEIGHT - 1e-9:
                raise ValueError(
                    f"WeightScheme '{scheme_id}' / {mode}: 因子 '{fname}' 权重 {w:.4f} "
                    f"< 最小值 {MIN_WEIGHT}"
                )
            if w > MAX_WEIGHT + 1e-9:
                raise ValueError(
                    f"WeightScheme '{scheme_id}' / {mode}: 因子 '{fname}' 权重 {w:.4f} "
                    f"> 最大值 {MAX_WEIGHT}"
                )

        # 维度 4: 至少 1 个因子
        if not weights:
            raise ValueError(f"WeightScheme '{scheme_id}' / {mode}: 不能为空")

        # 维度 5: 因子名不能重复（dict 自动处理，但值不能是同一个）
        # 这里 dict 本身就是 unique keys，无需额外校验

    def get_weights(self, market_mode: str) -> dict[str, float]:
        """获取指定 market_mode 的权重。

        Args:
            market_mode: "trend_up" / "range_bound"

        Returns:
            {factor_name: weight} 拷贝（防止外部修改）

        Raises:
            ValueError: market_mode 不在 scheme 中
        """
        if market_mode not in self.weights_by_mode:
            raise ValueError(
                f"WeightScheme '{self.scheme_id}' 不支持 market_mode '{market_mode}'。"
                f"支持：{list(self.weights_by_mode.keys())}"
            )
        # 返回拷贝，防止外部修改
        return dict(self.weights_by_mode[market_mode])

    def factor_names(self) -> set[str]:
        """所有 market_mode 涉及到的因子集合（并集）"""
        result = set()
        for weights in self.weights_by_mode.values():
            result.update(weights.keys())
        return result

    def to_dict(self) -> dict:
        """导出为 dict（JSON 序列化用）"""
        return {
            "scheme_id": self.scheme_id,
            "weights_by_mode": self.weights_by_mode,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WeightScheme":
        """从 dict 还原"""
        return cls(
            scheme_id=data["scheme_id"],
            weights_by_mode=data["weights_by_mode"],
        )

    @classmethod
    def from_json_file(cls, path: Path | str) -> "WeightScheme":
        """从 JSON 文件加载（运行时配置入口）"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"权重配置文件不存在：{path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def d004_b2(cls) -> "WeightScheme":
        """D-004 B2 方案（trend_up 重趋势 + range 重摆动+量能）。

        来源：reports/2026-06-25_eight_factor_v2/D-004_top3_weights.json
        评分：ir_score=100 / stability=81 / diversity=94 / economic=62.5 / pref=100 / total=89.44
        """
        return cls(
            scheme_id="B2",
            weights_by_mode={
                "trend_up": {
                    "W2_boll_width": 0.05,
                    "B1_boll_upper": 0.05,
                    "M4_rsi": 0.10,
                    "V2_obv": 0.05,
                    "V3_maobv": 0.05,
                    "DMA": 0.30,
                    "M2_momentum_5d": 0.15,
                    "FIB": 0.25,
                },
                "range_bound": {
                    "W2_boll_width": 0.10,
                    "B1_boll_upper": 0.05,
                    "M4_rsi": 0.25,
                    "V2_obv": 0.15,
                    "V3_maobv": 0.15,
                    "DMA": 0.15,
                    "M2_momentum_5d": 0.10,
                    "FIB": 0.05,
                },
            },
        )


__all__ = [
    "WeightScheme",
    "MIN_WEIGHT",
    "MAX_WEIGHT",
    "SUPPORTED_MARKET_MODES",
]