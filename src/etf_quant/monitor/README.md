# monitor — 监控

> **职责**：数据/系统/业务三层监控 + 主动告警
> **依据**：v1 src/data/monitor.py + L62/L200 教训

## 三层监控

### 1. 数据健康（data_health.py）
- 分钟级新鲜度（80 分钟阈值）
- 交易日完整性（min_day_count 动态化）
- 上一交易日计算（周末往前推）

### 2. 系统健康（system.py）
- CPU/内存/磁盘
- 进程存活

### 3. 业务健康（business.py）
- 持仓异常（最大回撤超阈值）
- 交易异常（频繁止损）
- 收益异常（大幅偏离预期）

## 接口契约

```python
class Monitor(Protocol):
    def check_data_health(self) -> HealthReport: ...
    def check_system_health(self) -> HealthReport: ...
    def check_business_health(self) -> HealthReport: ...

class AlertManager(Protocol):
    def alert(self, report: HealthReport) -> None:
        """发送告警（cooldown 1h，告警风暴防护）。"""
```

## 关联教训

- L62（监控阈值动态化）
- L200（沉默失败 7 天）
- L222（告警推送 target-session）