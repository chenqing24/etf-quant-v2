# Security Policy

> v2 量化系统的安全策略和漏洞报告流程。

---

## Supported Versions

| 版本 | 支持状态 |
|------|---------|
| 2.0.x (current) | ✅ Active |
| 1.x (etf_strategy) | ❌ Deprecated（已归档） |

---

## Reporting a Vulnerability

**请勿在 GitHub Issues 公开漏洞！**

### 报告流程

1. **私下联系**：通过 GitHub Security Advisories（推荐）
   - 访问 https://github.com/chenqing24/etf-quant-v2/security/advisories/new
   - 填写漏洞详情
2. **邮件联系**（备选）：联系项目所有者 chenqing24
3. **响应时间**：48 小时内确认收到，7 天内评估严重程度
4. **修复时间**：根据严重程度 1-4 周
5. **披露时间**：修复后 90 天公开 CVE

### 报告内容

请提供：
- 漏洞类型（XSS / SQL 注入 / 越权 / 数据泄露 / 等）
- 复现步骤（PoC 代码 / 截图）
- 影响范围（哪些模块 / 数据）
- 严重程度评估（Critical / High / Medium / Low）
- 建议修复方案（如有）

---

## 安全设计原则

### 1. 数据层隔离

- 业务数据 `data/etf.db` 不入 git（.gitignore 强制）
- 测试用 fixture 入 git，但**脱敏后**才能入（见 SOP-06）
- 交易实盘数据（`etf_performance.json` / `etf_positions.json`）不入 git

### 2. 凭据管理

- **API Key**：用 `.env` 文件（不入 git）+ `python-dotenv` 加载
- **钉钉 Webhook**：URL 存环境变量，**禁止硬编码**
- **数据库密码**：用密钥管理（`pydantic SecretStr`）
- **GitHub PAT**：定期轮换（90 天）+ 最小权限原则

### 3. 输入验证

- 用户输入必须过 `pydantic` 验证
- ETF 代码必须 6 位数字 + 正确交易所前缀（sh/sz）
- 日期范围必须合法（start < end）
- 文件路径必须 `pathlib.Path.resolve()` + 白名单检查

### 4. 依赖安全

- `pip-audit` 定期扫描
- GitHub Dependabot（v2 仓 push 后开启）
- 关键依赖锁版本（`pyproject.toml` 用 `>=` 而非 `==`）

### 5. 审计日志

- 所有交易记录必须包含 `is_real` / `emotion` / `reason` 字段（防 AI 误判）
- 决策快照必须可追溯（schema 007 `decision_snapshot` 表）
- 任何数据修改必须记录时间戳 + 修改人

---

## 已知安全考虑

### 1. 量化策略信号

- **不构成投资建议**：所有信号为算法生成，需用户人工判断
- **实盘风险**：用户应自行验证再下单
- **历史回测 ≠ 未来表现**：规则 6.1 强制诚实声明

### 2. 数据源 API

- 腾讯/新浪/AKShare 都是第三方 API，无 SLA 保证
- 限速遵守（腾讯 2s/新浪 2s/AKTools 5s）
- 失败重试必须指数退避，避免被封

### 3. 钉钉推送

- Webhook URL 视为敏感凭据
- 推送内容自动脱敏（隐藏身份证/手机号等 PII）

---

## 安全更新通知

- Watch GitHub repo：https://github.com/chenqing24/etf-quant-v2/watchers
- Security Advisories：https://github.com/chenqing24/etf-quant-v2/security/advisories
- Release notes：[CHANGELOG.md](CHANGELOG.md)

---

## 参考来源

- GitHub Security Advisories 文档
- v1 仓无 SECURITY.md（zip 验证缺失）
- v2 SOP-06 脱敏规范：[docs/SOP_06_DESENSITIZE.md](docs/SOP_06_DESENSITIZE.md)
- OWASP Top 10（Web 安全，量化系统参考）
- CWE（Common Weakness Enumeration）
