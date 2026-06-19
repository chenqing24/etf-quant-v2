"""
alpha/strategy_c21.py — C21-1 策略（v1 颠覆性发现的金三角）

用途：
    实现 C21-1 ETF 选股策略（v1 C20 颠覆性发现的金三角）：
    - 入场过滤：BOLL 严格中轨 + close > MA60
    - 退出禁用：永远不卖（卖出是 alpha 拖累）
    - max_hold_days=99999（永远满仓）

被谁调用：
    - Sprint-2 US-006 验证（tests/unit/test_strategy_c21.py）
    - 未来 alpha/strategy_factory.py（多策略统一入口）
    - etf-daily skill 入口（skills/etf-daily/scripts/run_daily.py）

功能说明：
    - C21EntryConditions: BOLL 中轨阈值（±0.5%）+ MA60 趋势
    - C21ExitConditions: enabled=False（永远不卖）
    - C21Strategy: 完整策略类 + from_config() 加载
    - get_human_nature_warning(): 暴露 v1 5 项心理挑战（L227 教训）

使用方式：
    from etf_quant.alpha.strategy_c21 import C21Strategy
    strategy = C21Strategy.from_config()
    if strategy.should_buy(close=4.0, boll_middle=4.0, ma60=3.9):
        # 买入逻辑
    if strategy.should_sell(hold_days=100):
        # 永远不会卖（C21-1 关键）

依赖：
    - pandas: DataFrame 处理
    - configs/c21_strategy.json: v1 真实策略配置
    - L225 教训（alpha 真正来源是入场过滤 + 永远满仓）
    - L227 教训（用户定性结构化为 human_nature_warning）
    - L238 教训（先读真实 API 再写测试）

注意事项：
    - v1 颠覆性发现：金三角 = 入场过滤 + 永远满仓（不是 4 因子组合）
    - C20 实验验证：任何卖出信号都是负 alpha
    - C21-1 仅在 5 年以上历史 ETF 上验证（11 只），其他 ETF 效果未知
    - 心理挑战高（5 项警告），不适合所有人
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

# 项目根
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CONFIG_PATH = _REPO_ROOT / "configs" / "c21_strategy.json"


@dataclass
class C21EntryConditions:
    """C21-1 入场条件（v1 真实配置）。"""

    boll_threshold: float = 0.005  # BOLL 严格中轨阈值（±0.5%）
    ma_period: int = 60  # MA60 长期趋势

    def check_boll_strict_middle(self, close: float, boll_middle: float) -> bool:
        """BOLL 严格中轨：|close - BOLL_middle| / BOLL_middle <= 0.005。

        v1 rationale: 价格不太贵也不太便宜（20日均价 ±0.5%）。
        """
        if boll_middle <= 0:
            return False
        return abs(close - boll_middle) / boll_middle <= self.boll_threshold

    def check_ma60_trend_up(self, close: float, ma60: float) -> bool:
        """MA60 趋势向上：close > MA60。

        v1 rationale: 长期趋势向上（60日均线之上）。
        """
        return close > ma60

    def all_conditions_met(
        self, close: float, boll_middle: float, ma60: float
    ) -> bool:
        """所有入场条件同时满足（v1 严格 AND）。"""
        return (
            self.check_boll_strict_middle(close, boll_middle)
            and self.check_ma60_trend_up(close, ma60)
        )


@dataclass
class C21ExitConditions:
    """C21-1 退出条件（v1 验证：永远不卖）。"""

    enabled: bool = False  # C21-1 关键：永远不卖
    max_hold_days: int = 99999  # C11 修复：持仓管理 > 因子


@dataclass
class C21Strategy:
    """C21-1 策略（v1 C20 颠覆性发现的金三角）。"""

    entry: C21EntryConditions
    exit: C21ExitConditions

    @classmethod
    def from_config(cls, config_path: Optional[Path] = None) -> "C21Strategy":
        """从 JSON 配置加载（v1 模式 + L227 教训）。"""
        path = config_path or _CONFIG_PATH
        config = json.loads(path.read_text(encoding="utf-8"))

        entry_config = config["entry_conditions"]
        exit_config = config["exit_conditions"]

        return cls(
            entry=C21EntryConditions(
                boll_threshold=next(
                    c["threshold"]
                    for c in entry_config["conditions"]
                    if c["id"] == "boll_strict_middle"
                ),
                ma_period=60,
            ),
            exit=C21ExitConditions(
                enabled=exit_config["enabled"],
                max_hold_days=config["max_hold_days"],
            ),
        )

    def should_buy(
        self, close: float, boll_middle: float, ma60: float
    ) -> bool:
        """判断是否买入（v1 entry 条件）。"""
        return self.entry.all_conditions_met(close, boll_middle, ma60)

    def should_sell(self, hold_days: int) -> bool:
        """判断是否卖出（v1 C20 验证：永远 false）。

        即使 max_hold_days=99999，单笔永远不到期。
        这是 C21-1 与其他策略的核心区别。
        """
        if not self.exit.enabled:
            return False  # L225 教训：卖出是 alpha 拖累
        return hold_days >= self.exit.max_hold_days

    def get_human_nature_warning(self, config_path: Optional[Path] = None) -> dict:
        """获取人性警告（v1 L227 教训：用户定性结构化）。"""
        path = config_path or _CONFIG_PATH
        config = json.loads(path.read_text(encoding="utf-8"))
        return config.get("human_nature_warning", {})
