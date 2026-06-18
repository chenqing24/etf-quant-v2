# notify — 通知

> **职责**：钉钉推送、报告生成
> **依据**：v1 src/notify/ 双通道（notifier + scenario）

## 核心组件

### DingTalk 客户端

- **notifier.py**：信号通知（含买卖 + 警告）
- **scenario.py**：场景通知（简化版）
- **message.py**：消息模板
- **snapshot.py**：决策快照

## 接口契约

```python
class DingTalkClient(Protocol):
    def send(self, message: str, channel: str = "dingtalk") -> bool:
        """发送钉钉消息。"""

class SignalNotifier(Protocol):
    def notify_buy(self, signal: Signal) -> None: ...
    def notify_sell(self, position: Position) -> None: ...
    def notify_warning(self, msg: str) -> None: ...
```

## 关联教训

- L207（pytest mock 外部副作用 — 钉钉不应在测试中真推）
- L222（target-session 隔离 — 推送只到 WoXtGw==）