# scheduler — 调度

> **职责**：QwenPaw cron 封装、定时任务管理
> **依据**：v1 configs/cron_jobs.yaml + scripts/qwenpaw_cron_sync.py

## 核心组件

| 组件 | 角色 |
|------|------|
| `cron.py` | 封装 qwenpaw cron API |
| `jobs.yaml` | 单一真相源（v1 6/16 建立）|
| `sync.py` | wrapper 脚本（--dry-run/--backup/--prune/--only）|

## 定时任务

| 任务 | 时间 | 用途 |
|------|------|------|
| 新闻早报 | 09:30 工作日 | 财经科技新闻 |
| 数据质量监控 | 09:00 工作日 | 数据健康检查 |
| ETF 量化每日评估 | 14:30 工作日 | 量化决策 |
| SQLite 每日备份 | 16:30 工作日 | 数据库备份 |

**所有 cron 默认 target-session=WoXtGw==**（L222 教训）

## 关联教训

- L222（target-session 分流推送）