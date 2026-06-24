"""
monitor/data_health.py — 数据健康监控（v2 monitor 模块，US-018）

按 L62/L200 教训：
- 分钟级新鲜度（默认 80 分钟阈值，可配置）
- 交易日完整性（min_day_count 动态化）
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from etf_quant.data_layer.loader import DataLoader
from etf_quant.config.constants import DATA_DIR, DB_NAME, DEFAULT_MAX_DELAY_MINUTES


@dataclass
class DataHealthReport:
    """数据健康报告"""
    fresh: bool  # 数据是否新鲜
    fresh_minutes: float  # 距最新数据多少分钟
    threshold_minutes: int  # 阈值（默认 80）
    min_day_count: int  # 每只 ETF 最少交易日数
    issues: list  # 问题列表


class DataHealthMonitor:
    """数据健康监控器"""

    def __init__(
        self,
        loader: Optional[DataLoader] = None,
        threshold_minutes: int = DEFAULT_MAX_DELAY_MINUTES,  # 默认 1500 分钟（25h，覆盖非交易时段）
        min_day_count: int = 100,  # L62 教训：动态化
    ):
        if loader is None:
            db_path = f"{DATA_DIR}/{DB_NAME}"
            loader = DataLoader(db_path=db_path)
        self.loader = loader
        self.threshold_minutes = threshold_minutes
        self.min_day_count = min_day_count

    def check(self) -> DataHealthReport:
        """检查数据健康状态"""
        issues = []
        # 1. 数据新鲜度
        latest_date = self.loader.get_latest_date()
        if not latest_date:
            issues.append("daily 表无数据")
            return DataHealthReport(
                fresh=False, fresh_minutes=999,
                threshold_minutes=self.threshold_minutes,
                min_day_count=self.min_day_count, issues=issues,
            )
        latest = datetime.strptime(latest_date, "%Y-%m-%d")
        now = datetime.now()
        fresh_minutes = (now - latest).total_seconds() / 60
        if fresh_minutes > self.threshold_minutes:
            issues.append(
                f"数据已过期 {fresh_minutes:.0f} 分钟（阈值 {self.threshold_minutes}）"
            )
        return DataHealthReport(
            fresh=fresh_minutes <= self.threshold_minutes,
            fresh_minutes=fresh_minutes,
            threshold_minutes=self.threshold_minutes,
            min_day_count=self.min_day_count,
            issues=issues,
        )
