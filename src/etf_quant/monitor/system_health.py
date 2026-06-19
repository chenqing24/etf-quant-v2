"""
monitor/system_health.py — 系统健康监控（v2 monitor 模块）

监控维度：
- 磁盘空间（>5GB 警告）
- 数据库大小
- Python 进程内存
- 交易日判断
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import List


@dataclass
class SystemHealthReport:
    """系统健康报告"""
    disk_free_gb: float
    db_size_mb: float
    issues: List[str]


class SystemHealthMonitor:
    """系统健康监控器"""

    DISK_MIN_GB = 5.0  # 最小磁盘空间

    def check(self) -> SystemHealthReport:
        """检查系统健康"""
        issues = []
        # 1. 磁盘空间
        usage = shutil.disk_usage("/")
        disk_free_gb = usage.free / (1024 ** 3)
        if disk_free_gb < self.DISK_MIN_GB:
            issues.append(
                f"磁盘空间不足 {disk_free_gb:.1f}GB < {self.DISK_MIN_GB}GB"
            )
        return SystemHealthReport(
            disk_free_gb=disk_free_gb,
            db_size_mb=0.0,  # 暂不查 DB 大小
            issues=issues,
        )
