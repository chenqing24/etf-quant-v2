"""
backtest/comprehensive_validator.py — ComprehensiveValidator 4 验证器

用途：
    v1 6/1 增强版综合验证器（4 验证器 + 权重 + 通过阈值）。
    v2 简化：保留核心 API（composite_score + pass_），简化实现。

被谁调用：
    - skills/etf-research/scripts/run_validate.py
    - src/etf_quant/backtest/engine.py（未来）

功能说明：
    4 验证器 + 权重（v1 6/1 增强版）：
    - WalkForward (40%): 时序滚动验证
    - MonteCarlo (15%): 显著性检验
    - CrossETF (35%): 跨 ETF 泛化
    - Consistency (10%): 综合一致性
    pass_threshold = 0.6

使用方式：
    from etf_quant.backtest.comprehensive_validator import (
        ComprehensiveValidator, ComprehensiveResult,
    )
    validator = ComprehensiveValidator()
    result = validator.validate(backtest_results)
    if result.pass_:
        # 策略通过验证

依赖：
    - v1 ComprehensiveValidator 配置（commit 53c82b2）
    - v1 6/1 教训：过拟合检测至关重要（v8_sop MC p-value=1.0）

注意事项：
    - v1 MC 总是 1.0（已通过降低权重缓解）
    - 阈值 0.6 是 v1 增强后的标准
    - 综合评分 = WF*0.4 + MC*0.15 + CE*0.35 + Consistency*0.10
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


# v1 6/1 增强版配置
DEFAULT_CONFIG = {
    "walk_forward": {
        "train_months": 6,
        "test_months": 3,
        "min_windows": 6,
        "transaction_cost": 0.002,
    },
    "monte_carlo": {
        "n_simulations": 1000,
        "transaction_cost": 0.002,
        "confidence_level": 0.05,
    },
    "cross_etf": {
        "train_ratio": 0.5,
        "min_train_etfs": 7,
        "min_test_etfs": 5,
        "min_gap": 0.2,
    },
    "weights": {
        "walk_forward": 0.40,
        "monte_carlo": 0.15,
        "cross_etf": 0.35,
        "consistency": 0.10,
    },
    "pass_threshold": 0.6,
    "market_benchmark": "510300",
}


@dataclass
class ComprehensiveResult:
    """综合验证结果（v1 兼容）。"""

    composite_score: float
    pass_: bool
    confidence: str

    # 各模块结果
    walk_forward_score: float
    monte_carlo_score: float
    cross_etf_score: float
    consistency: float

    # 详细信息
    walk_forward_details: Dict = field(default_factory=dict)
    monte_carlo_details: Dict = field(default_factory=dict)
    cross_etf_details: Dict = field(default_factory=dict)

    # 元信息
    timestamp: str = ""
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ComprehensiveValidator:
    """综合验证调度器（v1 6/1 增强版简化）。"""

    def __init__(self, config: Dict = None) -> None:
        self.config = config or DEFAULT_CONFIG

    def validate(self, backtest_results: List[Dict]) -> ComprehensiveResult:
        """运行 4 验证器并综合评分。

        Args:
            backtest_results: 回测结果列表，每个 dict 至少含:
                - etf_code: str
                - train_period: tuple (start, end)
                - test_period: tuple (start, end)
                - train_return: float
                - test_return: float
                - sharpe: float
                - max_drawdown: float

        Returns:
            ComprehensiveResult: 综合验证结果
        """
        # 4 验证器（v2 简化版）
        wf_score = self._walk_forward_validate(backtest_results)
        mc_score = self._monte_carlo_validate(backtest_results)
        ce_score = self._cross_etf_validate(backtest_results)
        consistency = self._consistency_check(wf_score, mc_score, ce_score)

        # 加权综合
        weights = self.config["weights"]
        composite = (
            wf_score * weights["walk_forward"]
            + mc_score * weights["monte_carlo"]
            + ce_score * weights["cross_etf"]
            + consistency * weights["consistency"]
        )

        # 通过判断
        threshold = self.config["pass_threshold"]
        pass_ = composite >= threshold

        # 置信度分级
        if composite >= 0.8:
            confidence = "HIGH"
        elif composite >= 0.6:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        warnings = []
        recommendations = []
        if mc_score < 0.5:
            warnings.append("Monte Carlo 显著性低（p-value 可能 > 0.05）")
        if ce_score < 0.5:
            warnings.append("Cross ETF 泛化能力不足")
        if wf_score < 0.5:
            warnings.append("Walk Forward 时序验证失败")

        from datetime import datetime
        return ComprehensiveResult(
            composite_score=composite,
            pass_=pass_,
            confidence=confidence,
            walk_forward_score=wf_score,
            monte_carlo_score=mc_score,
            cross_etf_score=ce_score,
            consistency=consistency,
            walk_forward_details={"min_windows": self.config["walk_forward"]["min_windows"]},
            monte_carlo_details={"n_simulations": self.config["monte_carlo"]["n_simulations"]},
            cross_etf_details={"min_train_etfs": self.config["cross_etf"]["min_train_etfs"]},
            timestamp=datetime.now().isoformat(timespec="seconds"),
            warnings=warnings,
            recommendations=recommendations,
        )

    def _walk_forward_validate(self, results: List[Dict]) -> float:
        """Walk Forward 验证（时序滚动 + min_windows）。"""
        cfg = self.config["walk_forward"]
        min_windows = cfg["min_windows"]

        # v2 简化：检查回测结果窗口数
        n_windows = len(results)
        if n_windows < min_windows:
            return 0.0

        # 简化评分：所有 test_return > 0 的比例
        positive = sum(1 for r in results if r.get("test_return", 0) > 0)
        return positive / n_windows if n_windows > 0 else 0.0

    def _monte_carlo_validate(self, results: List[Dict]) -> float:
        """Monte Carlo 显著性检验（v2 简化版）。"""
        if not results:
            return 0.0
        # 简化：基于 sharpe 均值
        sharpes = [r.get("sharpe", 0) for r in results]
        avg_sharpe = sum(sharpes) / len(sharpes)
        # sharpe > 1 → 高显著性
        if avg_sharpe > 2:
            return 1.0
        elif avg_sharpe > 1:
            return 0.8
        elif avg_sharpe > 0:
            return 0.5
        return 0.0

    def _cross_etf_validate(self, results: List[Dict]) -> float:
        """Cross ETF 泛化验证。"""
        cfg = self.config["cross_etf"]
        min_train = cfg["min_train_etfs"]

        # v2 简化：检查不同 ETF 的胜率
        etf_codes = set(r.get("etf_code") for r in results)
        n_etfs = len(etf_codes)
        if n_etfs < min_train:
            return 0.0

        # 简化：胜率（test_return > 0）跨 ETF 的平均
        positive_count = sum(1 for r in results if r.get("test_return", 0) > 0)
        return positive_count / len(results) if results else 0.0

    def _consistency_check(self, wf: float, mc: float, ce: float) -> float:
        """综合一致性检查（标准差越小分数越高）。"""
        scores = [wf, mc, ce]
        if not scores:
            return 0.0
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = variance ** 0.5
        # std 越小分数越高（std=0 → 1.0，std=0.5 → 0.5）
        return max(0.0, 1.0 - std * 2)
