"""
scheduler/config.py — 默认 cron 任务配置（v2 scheduler）

用途：定义 4 个默认 cron 任务（etf-daily/research/backup/health-check）。
被谁调用：scripts/qwenpaw_cron_sync.py（CLI 同步）+ scheduler/cron.py。
按 v1 configs/cron_jobs.yaml 简化。
"""
from __future__ import annotations

from .cron import CronJobConfig


# 默认 cron 任务清单（按 v1 cron_jobs.yaml）
DEFAULT_CRON_JOBS = [
    CronJobConfig(
        name="etf-daily-check",
        schedule="30 14 * * 1-5",  # 工作日 14:30
        command="python skills/etf-daily/scripts/run_daily.py daily",
        description="ETF 每日决策（工作日 14:30）",
    ),
    CronJobConfig(
        name="etf-research-weekly",
        schedule="30 14 * * 0",  # 周日 14:30
        command="python skills/etf-research/scripts/run_validate.py validate",
        description="ETF 深度研究（周日 14:30）",
    ),
    CronJobConfig(
        name="sqlite-backup-daily",
        schedule="30 16 * * 1-5",  # 工作日 16:30
        command="python scripts/backup_sqlite.py",
        description="SQLite 数据备份（工作日 16:30）",
    ),
    CronJobConfig(
        name="data-health-check",
        schedule="0 9 * * 1-5",  # 工作日 09:00
        command="python -c 'from etf_quant.monitor.data_health import check; check()'",
        description="数据健康检查（工作日 09:00）",
    ),
]
