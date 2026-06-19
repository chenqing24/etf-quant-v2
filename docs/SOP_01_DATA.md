# SOP_01_DATA — 数据获取/存储/查询规范

> **版本**：v2.0
> **日期**：2026-06-20
> **依据**：v1 SOP-01 + Sprint-7 业务完整化

---

## 1. 数据源可靠性排序

```
高 → 低
腾讯API > 新浪API > AKShare新浪 > 天天基金 > BaoStock > AKShare东财
```

## 2. 网络访问规则

```
✅ 国内网站：直接访问
   - 腾讯行情API (qt.gtimg.cn)
   - 新浪财经API (hq.sinajs.cn)
   - 天天基金网 (fundgz.1234567.com.cn)
   - 东方财富 (api.fund.eastmoney.com)
   - 上交所 (query.sse.com.cn)

❌ 国外网站：必须走代理
   - GitHub
   - 官方文档（英文）
   - PyPI

代理配置：socks5://127.0.0.1:1080
```

## 3. 限速规则（硬约束）

| 数据源 | 最小间隔 | 超过后果 |
|--------|---------|----------|
| 腾讯API | 2秒 | IP被封 |
| 新浪API | 2秒 | 返回空数据 |
| 天天基金 | 3秒 | 限流 |
| **AKTools** | **5秒** | **拒绝服务** |
| AKShare东财 | 5秒 | 返回错误 |

## 4. 不可用接口清单

| 接口 | 原因 | 替代方案 |
|------|------|----------|
| 雪球Xueqiu | 数据格式异常 | 无需替代 |
| 百度百科 | 限流严重 | 无需替代 |
| 东方财富EMF | ETF不可用 | AKShare东财 |
| AKShare东财 fund_etf_hist_em | 不可用 | AKShare新浪 |

## 5. 数据获取流程

```
1. 调研：测试所有候选数据源
2. 文档：验证字段格式，写入 DATA_SOURCE_REFERENCE.md
3. 部署：限流严重时部署本地服务（aktools-server）
4. 测试：先小批量再全量
5. 集成：统一HTTP API入口
```

## 6. 数据存储原则

1. **唯一数据源**：SQLite（data/etf.db）
2. **单一入口**：data_layer 的 6 个 Repository
3. **业务层零 SQL**：pre-commit 钩子拦截
4. **WAL 模式**：提高并发

## 7. 数据查询原则

1. **优先使用 ETFRepository / TradeHistoryRepository**
2. **避免 SELECT *，明确字段**
3. **批量查询用 IN (...) 而非多次单独查询**
4. **统计查询用聚合函数，不要在 Python 层聚合**

## 8. 备份与恢复

- 每日 16:30 SQLite 自动备份（scheduler cron）
- 备份位置：data/backups/YYYY-MM-DD/
- 保留策略：最近 7 天 + 每周一全量

## 9. 脱敏（隐私保护）

- 用户实盘数据需脱敏后才能 commit
- 邮箱、手机号用 hash
- 真实姓名替换为化名
