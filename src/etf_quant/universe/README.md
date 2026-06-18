# universe — 股票池

> **职责**：ETF 池的动态加载、筛选、分类
> **依据**：v1 5/30 ETF 池 + 6/17 v9-us002-pool-db-sot

## 接口契约

### ETFListLoader

```python
class ETFListLoader:
    """从 etf_names 表动态加载 ETF 池。

    池角色 5 分类（v1 已建立）：
    - core：核心池（可交易，14 只）
    - reference：参考池（不可交易，40 只）
    - legacy_holding：历史持仓（已清仓但保留元数据）
    - excluded：明确排除
    - unclassified：未分类（默认）

    关键设计（v1 教训 L19 教训）：
    - 默认值保守（unclassified + tradable=0）
    - 显式标注才进 core/reference
    """
    def load(self, role: str = "core") -> list[str]:
        """加载指定角色的 ETF 代码列表。"""

    def get_metadata(self, code: str) -> dict:
        """获取 ETF 元数据（名称/规模/上市日/池角色）。"""
```

## 关联

- `data_layer/contracts.py` — `SelectorResultSchema`（Set[str] codes）
- `config/etf_pools.py` — 池配置
- `data_layer/loader.py` — DB 读取

## 关联教训

- L19（标记角色不删数据）
- L62（动态加载，不硬编码）
- L228（300ETF 池外置 DB 化盲点）