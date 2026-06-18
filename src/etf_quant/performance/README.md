# performance — 绩效评估

> **职责**：43 指标绩效评估、报告生成
> **依据**：v1 v7 评价体系（8 大类 43 指标）

## 8 大类 43 指标

| 类别 | 指标数 | 代表 |
|------|:---:|------|
| 收益类 | 8 | 总收益/年化/月均/日均 |
| 风险类 | 7 | 最大回撤/波动率/VaR |
| 风险调整 | 6 | 夏普/Calmar/Sortino/IR |
| 交易类 | 6 | 胜率/盈亏比/换手率 |
| 持仓类 | 4 | 平均持仓天数/最大同时持仓 |
| 市场类 | 4 | Beta/Alpha/相关性 |
| 因子类 | 4 | IC/ICIR/换手率 |
| 综合类 | 4 | 综合评分/排名 |

## 接口契约

```python
class MetricsCalculator(Protocol):
    def calculate(self, trades: list[Trade], positions: list[Position]) -> dict:
        """计算 43 指标。"""

class PerformanceReport(Protocol):
    def generate(self, metrics: dict) -> str:
        """生成绩效报告（Markdown 格式）。"""
```

## 关联教训

- L218（alpha 验证 + buy & hold 基准）
- L219（过拟合风险 + 样本外）
- L220（数据时长 + 偏差风险）