"""
alpha/factors/sixty_min/__init__.py — 60min 因子包（D-007）

按 D-007 5 项隔离原则：
    1. 不参与实时决策（HOLD/BUY/SELL 不读 60min score）
    2. 不污染 8 因子权重（独立 FactorSet `sixty_min_4f`）
    3. 不参与 rank（不进入横截面打分）
    4. 不参与止盈/止损（daily 止盈止损只看日线）
    5. 不进 decision_snapshot（只入 IC history 表）

被谁调用：
    - scripts/eval_60min_factors.py（独立评估 pipeline）
    - tests/unit/alpha/sixty_min/（单测）

业界参考（按规则 13）：
    - TA-Lib 150+ indicators（分钟级适用）
    - QuantConnect LEAN 100+ indicators（Resolution.Minute）
    - Barber 2005 / Bollinger 2001 / Granville 1976

D-007 4 因子：
    - H1 intraday_trend：日内趋势
    - H2 volume_breakout：量能突破
    - H3 boll_width_pct：布林带宽度百分位
    - H4 price_volume_corr：量价相关性
"""
from etf_quant.alpha.factors.sixty_min.h1_intraday_trend import H1IntradayTrendFactor
from etf_quant.alpha.factors.sixty_min.h2_volume_breakout import H2VolumeBreakoutFactor
from etf_quant.alpha.factors.sixty_min.h3_boll_width_pct import H3BollWidthPctFactor
from etf_quant.alpha.factors.sixty_min.h4_price_volume_corr import H4PriceVolumeCorrFactor

__all__ = [
    "H1IntradayTrendFactor",
    "H2VolumeBreakoutFactor",
    "H3BollWidthPctFactor",
    "H4PriceVolumeCorrFactor",
]