# SOP_05_BACKUP — 备份与恢复

> **版本**：v2.0
> **日期**：2026-06-20

---

## 1. 备份策略

### 1.1 SQLite 数据库

- **频率**：每日 16:30（工作日）
- **方式**：scheduler cron 调 `scripts/backup_sqlite.py`
- **位置**：`data/backups/YYYY-MM-DD/etf.db`
- **保留**：最近 7 天 + 每周一全量保留 4 周

### 1.2 配置文件

- **频率**：每次修改前
- **方式**：git commit
- **位置**：configs/ + 仓 .git/

### 1.3 决策快照

- **频率**：每次决策（daily/eval/manual）
- **方式**：写入 decision_snapshot 表
- **保留**：永久（业务需要历史决策）

## 2. 备份命令

```bash
# 手动备份
python scripts/backup_sqlite.py --target=data/backups/manual/

# 自动备份（cron 触发）
python scripts/backup_sqlite.py
```

## 3. 恢复流程

```bash
# 1. 停止所有服务
# 2. 备份当前 DB
cp data/etf.db data/etf.db.bak
# 3. 恢复目标 DB
cp data/backups/YYYY-MM-DD/etf.db data/etf.db
# 4. 验证
sqlite3 data/etf.db "SELECT COUNT(*) FROM etf_names"
# 5. 重启服务
```

## 4. 灾难恢复

- **本地备份丢失**：从 workspace mission 仓的 progress.txt 恢复
- **workspace 丢失**：从 git 仓恢复
- **双备份原则**（v1 L101 教训）：本地 + workspace

## 5. 备份验证

每月一次：
```bash
python scripts/verify_backup.py --target=data/backups/
```

验证项：
- 备份文件存在
- DB 可读
- 表结构完整
- 行数合理
