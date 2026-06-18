# execution — 执行

> **职责**：交易记录、决策快照、交易验证
> **依据**：v1 src/trade/tracker.py 1483 行（v2 拆 3 文件）+ US-008 6/3

## v2 拆分（解决 v1 单文件 1483 行技术债）

| v1 文件 | v2 拆分 | 行数估算 |
|---------|---------|:---:|
| src/trade/tracker.py | execution/tracker.py | ~600 |
| | execution/decision_snapshot.py | ~300 |
| | execution/validator.py | ~200 |
| | execution/cost.py | ~80 |

## 接口契约

### TradeTracker

```python
class TradeTracker(Protocol):
    """交易记录（31 字段）。"""
    def record_buy(
        self,
        code: str,
        price: float,
        quantity: int,
        reason: str,
        is_real: bool,  # 区分模拟 vs 实盘
        emotion: str,    # calm/fear/fomo/regret
        session: str,    # A/B/C/D/E/F
        signal_snapshot: dict,
        model: str,      # Q-009 决策上下文
        strategy: str,
        evaluation: str,
        snapshot_ref: str,
    ) -> int:
        """记录买入，返回 trade_id。"""

    def record_sell(self, ...) -> int: ...
```

## 关联教训

- L67（用户实盘亏损 → 159611 案例）
- L117（半途改造 — US-009 tracker 签名 bug）
- Q-009（决策上下文必填 4 字段）