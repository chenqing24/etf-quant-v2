# risk — 风控

> **职责**：止损/止盈/集中度/合规
> **依据**：v1 src/risk/manager.py + US-007 PositionGuide 22 字段

## 核心组件

### PositionGuide（US-007 6/3 落地）

**22 字段决策树 9 步**：

```
legacy_holding > 止损 > 短期 > 止盈 > 到期 > 空仓 > 加仓 > 换仓 > 持有
```

每步检查：code/name/action/price/quantity/amount/date + 12 个决策字段

## 接口契约

```python
class PositionGuide(Protocol):
    """22 字段决策树（v1 US-007）。"""
    def guide(
        self,
        position: Position,
        market_context: dict,
    ) -> GuideAction:
        """返回指南动作（HOLD/SELL/BUY 等）。"""

class RiskManager(Protocol):
    """风控管理（v1 src/risk/manager.py 模式）。"""
    def check_stop_loss(self, position: Position) -> bool:
        """止损检查（任意时刻触发，v1 规则 17）。"""

    def check_take_profit(self, position: Position) -> bool:
        """止盈检查（持仓满 min_hold_days 后触发）。"""
```

## 关联教训

- L67（用户实盘亏损 → 补救措施）
- L69（max_holdings=1 擅自假设错）
- 规则 17（止损止盈顺序：止损任意 > 止盈需 min_hold > 到期）