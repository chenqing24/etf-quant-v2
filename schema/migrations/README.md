# Schema 迁移脚本

> 数据库 schema 演进历史，每次变更一个文件

## 命名规范
`NNN_<description>.sql`，NNN 从 001 开始递增

## 历史迁移
| # | 名称 | 说明 | 日期 |
|---|------|------|------|
| 001 | add_updated_at.sql | daily 表增加 updated_at 字段 | 2026-06-01 |
| 002 | add_amount_source_created_at.sql | daily 表补齐 amount/source/created_at | 2026-06-01 |

## 迁移流程
```bash
# 1. 应用迁移
sqlite3 etf_data_live/etf.db < schema/migrations/001_add_updated_at.sql

# 2. 验证
sqlite3 etf_data_live/etf.db ".schema daily"
```

## 幂等性说明
SQLite 的 `ALTER TABLE ADD COLUMN` 不支持 `IF NOT EXISTS`，所以：
- 重复执行会报错
- 需要在应用层判断列是否存在后再执行
- DataWriter._ensure_columns() 会自动处理
