---
name: stock-portfolio
description: |
  持仓组合管理（多 ETF 组合 + 再平衡 + 业绩归因）。

  触发场景：
  - 用户要求持仓组合分析
  - 用户要求再平衡建议

  执行方式：
    python skills/stock-portfolio/scripts/run_portfolio.py [action]
  参数：
    action: status | rebalance | attribution（默认 status）

  输出：
    - 当前持仓状态
    - 再平衡建议（按 PositionGuide）
    - 业绩归因（基于 trade_history）

  触发词：持仓组合 / 再平衡 / 业绩归因
---

# Stock Portfolio Skill

按 v2 设计（US-023）。

## 6 段标准注释

用途：
    stock-portfolio skill 入口（v1 portfolio_analyzer.py 拆分）。
    整合 position + trade_history + PositionGuide。

被谁调用：
    - QwenPaw 用户直接调用
    - skills/etf-daily/scripts/run_daily.py（持仓评估）

功能说明：
    - status: 当前持仓状态（按 PositionGuide 22 字段）
    - rebalance: 再平衡建议
    - attribution: 业绩归因

使用方式：
    python skills/stock-portfolio/scripts/run_portfolio.py status
    python skills/stock-portfolio/scripts/run_portfolio.py rebalance

依赖：
    - src/etf_quant/risk/position_guide.py（22 字段）
    - src/etf_quant/data_layer/position_repo.py
    - src/etf_quant/data_layer/trade_history_repo.py

注意事项：
    - max_holdings=2（v8 + 用户 B 决策）
    - 业绩归因按 v1 SOP-17（决策顺序）