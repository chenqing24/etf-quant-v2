"""
scheduler/cron.py — QwenPaw cron 封装（v2 scheduler 模块，US-015）

用途：
    封装 qwenpaw cron API（按规则 4 + L222 教训 target-session 隔离）。

被谁调用：
    - scripts/qwenpaw_cron_sync.py（CLI 同步脚本）
    - etf-daily skill（注册每日任务）
    - monitor 模块（注册数据健康检查）
"""
from __future__ import annotations

import subprocess
import json
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class CronJobConfig:
    """Cron 任务配置（v2 scheduler 通用类型）"""
    name: str
    schedule: str  # cron 表达式（5 字段：分 时 日 月 周）
    command: str
    target_session: str = "WoXtGw=="  # L222 教训：隔离 session
    description: str = ""


class CronSync:
    """Cron 任务同步器"""

    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id

    def list_jobs(self) -> List[dict]:
        """列出所有 cron 任务"""
        result = subprocess.run(
            ["qwenpaw", "cron", "list", "--agent-id", self.agent_id],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

    def add_job(self, config: CronJobConfig) -> bool:
        """添加 cron 任务"""
        result = subprocess.run(
            [
                "qwenpaw", "cron", "create",
                "--agent-id", self.agent_id,
                "--name", config.name,
                "--schedule", config.schedule,
                "--command", config.command,
                "--target-session", config.target_session,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0

    def remove_job(self, name: str) -> bool:
        """删除 cron 任务"""
        result = subprocess.run(
            [
                "qwenpaw", "cron", "delete",
                "--agent-id", self.agent_id,
                "--name", name,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
