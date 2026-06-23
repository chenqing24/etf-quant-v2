"""
monitor/market_mode.py — 市场环境检测器（L297 教训：基于外部数据判断 market_mode）

按 SOUL.md 规则 22：
    判断逻辑应该基于外部数据，不是行为反推。
    旧代码 `market_mode = "trend_up" if action == "buy" else "range_bound"` 是行为反推（鸡生蛋）。

业界参考（按规则 13）：
    - Grinold & Kahn 2000 *Active Portfolio Management* Ch 18: trend / mean-reversion 周期判断
    - Brock, Lakonishok & LeBaron 1992: 简单均线交叉（MA20/MA60 spread）
    - Wilder 1978 *New Concepts in Technical Trading Systems*: ATR 波动率分类

检测规则（按 510300 大盘 200 日 K 线）:
    1. trend_up    : MA20 > MA60 > MA120 + spread(MA20-MA60)/MA60 > 0.5%
    2. trend_down  : MA20 < MA60 < MA120 + spread(MA20-MA60)/MA60 < -0.5%
    3. crash       : 5d 回报 < -7% 或 ATR(14) / close > 5%
    4. range_bound : 其他

输出：dict {"mode": "trend_up|trend_down|crash|range_bound", "ma20": float, "ma60": float, "spread": float}
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from etf_quant.data_layer.loader import DataLoader


@dataclass
class MarketModeReport:
    """市场环境报告"""
    mode: str  # trend_up / trend_down / crash / range_bound
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    ma120: Optional[float] = None
    spread_pct: float = 0.0  # (MA20 - MA60) / MA60
    atr_pct: float = 0.0  # ATR(14) / close
    ret_5d_pct: float = 0.0  # 5 日回报 %
    asof_date: Optional[str] = None
    reason: str = ""


class MarketModeDetector:
    """市场环境检测器（基于大盘 ETF 510300 默认，可配置）"""

    # 趋势判定阈值（按 Grinold 经验 + Brock 1992 论文）
    SPREAD_THRESHOLD_PCT = 0.5  # 0.5% 以上算趋势
    CRASH_5D_PCT = -7.0  # 5 日跌超 7% 算崩盘
    CRASH_ATR_PCT = 5.0  # ATR/close > 5% 算高波动崩盘
    MIN_HISTORY_DAYS = 130  # 至少 130 天（算 MA120 + buffer）

    def __init__(
        self,
        benchmark_code: str = "510300",
        loader: Optional[DataLoader] = None,
        db_path: Optional[str] = None,
    ):
        """Args:
            benchmark_code: 大盘 ETF 代码（默认 510300 沪深300）
            loader: DataLoader 实例（测试可注入）
            db_path: SQLite 路径（便捷参数，构造临时 loader）
        """
        self.benchmark_code = benchmark_code
        if loader is None:
            from etf_quant.config.constants import DATA_DIR, DB_NAME
            if db_path is None:
                db_path = f"{DATA_DIR}/{DB_NAME}"
            loader = DataLoader(db_path=db_path)
        self.loader = loader

    def detect(self) -> MarketModeReport:
        """检测当前市场环境。

        步骤：
            1. 拉 benchmark 日线（>= MIN_HISTORY_DAYS）
            2. 算 MA20 / MA60 / MA120
            3. 算 spread_pct / atr_pct / ret_5d_pct
            4. 按优先级判定：crash > trend > range_bound
        """
        try:
            data = self.loader.load(min_rows=self.MIN_HISTORY_DAYS)
            df = data.get(self.benchmark_code)
        except Exception as e:
            return MarketModeReport(
                mode="range_bound",
                reason=f"加载数据失败: {e}，默认震荡市（保守兜底）",
            )

        if df is None or len(df) < self.MIN_HISTORY_DAYS:
            return MarketModeReport(
                mode="range_bound",
                reason=f"数据不足 {self.MIN_HISTORY_DAYS} 天，实际 {len(df) if df is not None else 0} 天，"
                       f"默认震荡市（保守兜底）",
            )

        close = df["close"]
        ma20 = close.rolling(20).mean().iloc[-1]
        ma60 = close.rolling(60).mean().iloc[-1]
        ma120 = close.rolling(120).mean().iloc[-1]
        spread_pct = (ma20 - ma60) / ma60 * 100

        # ATR(14)
        high = df["high"]
        low = df["low"]
        prev_close = close.shift(1)
        tr = pd.concat([
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        current_price = close.iloc[-1]
        atr_pct = atr / current_price * 100

        # 5 日回报
        ret_5d_pct = (close.iloc[-1] / close.iloc[-6] - 1) * 100

        asof_date = str(df["date"].iloc[-1])

        # 判定逻辑（按优先级）
        if ret_5d_pct < self.CRASH_5D_PCT or atr_pct > self.CRASH_ATR_PCT:
            mode = "crash"
            reason = (f"5d 回报 {ret_5d_pct:.2f}% (< {self.CRASH_5D_PCT}%) 或 "
                      f"ATR/close {atr_pct:.2f}% (> {self.CRASH_ATR_PCT}%)")
        elif ma20 > ma60 > ma120 and spread_pct > self.SPREAD_THRESHOLD_PCT:
            mode = "trend_up"
            reason = (f"MA20={ma20:.3f} > MA60={ma60:.3f} > MA120={ma120:.3f}，"
                      f"spread={spread_pct:.2f}%")
        elif ma20 < ma60 < ma120 and spread_pct < -self.SPREAD_THRESHOLD_PCT:
            mode = "trend_down"
            reason = (f"MA20={ma20:.3f} < MA60={ma60:.3f} < MA120={ma120:.3f}，"
                      f"spread={spread_pct:.2f}%")
        else:
            mode = "range_bound"
            reason = f"MA20/MA60/MA120 非典型排列或 spread {spread_pct:.2f}% 介于 ±{self.SPREAD_THRESHOLD_PCT}%"

        return MarketModeReport(
            mode=mode,
            ma20=float(ma20),
            ma60=float(ma60),
            ma120=float(ma120),
            spread_pct=float(spread_pct),
            atr_pct=float(atr_pct),
            ret_5d_pct=float(ret_5d_pct),
            asof_date=asof_date,
            reason=reason,
        )
