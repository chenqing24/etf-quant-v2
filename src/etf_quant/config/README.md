# config — 配置

> **职责**：配置外置、加载器、版本管理
> **依据**：v1 config/ 5 文件 + utils/config.py

## 核心组件

| 组件 | 角色 | 来源 |
|------|------|------|
| `loader.py` | 统一配置加载 | v1 utils/config.py |
| `strategy.py` | 策略配置 | v1 strategy/config.py |
| `risk.py` | 风控配置 | v1 risk/config_types.py |
| `versions.py` | schema 版本管理 | v2 新增 |

## 接口契约

```python
class ConfigLoader(Protocol):
    def load(self, name: str) -> dict:
        """加载指定配置（从 YAML/JSON 文件）。"""

class ConfigVersion(Protocol):
    """schema 版本管理（v2 新增）。"""
    def get_version(self) -> str:
        """获取当前 schema 版本（基于 schema/migrations/）。"""
```

## 关联教训

- L211（机制层 > AI 自觉 — 业务校验放 store.add()）
- L222（target-session 隔离）