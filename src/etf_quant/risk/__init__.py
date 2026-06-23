"""
etf_quant/risk — 风控模块（v2 US-007）

用途：9 步决策树（止损/止盈/到期/加仓/换仓）+ 市场环境响应。
被谁调用：etf-daily skill / etf-research skill / position_repo。

按 SOUL.md 规则 17（代码逻辑顺序）：
    止损（任意）> 止盈（需 min_days）> 到期
    持仓 < min_hold → 持有（短期）
    持仓 ≥ max_hold → 到期评估
    市场非 trend_up → 清仓空仓

子模块：
    - position_guide: 9 步决策树（PositionGuide + PositionGuideAnalyzer）

入口示例：
    from etf_quant.risk import PositionGuideAnalyzer
    analyzer = PositionGuideAnalyzer(db_path="/path/etf.db")
    guide = analyzer.analyze_position(
        code="510300", current_price=4.10,
        market_regime="trend_up", current_score=85,
    )
    if guide.should_stop_loss:
        # 止损逻辑
"""
from etf_quant.risk.position_guide import PositionGuide, PositionGuideAnalyzer

__all__ = ["PositionGuide", "PositionGuideAnalyzer"]
