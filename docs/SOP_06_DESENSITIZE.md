# SOP_06_DESENSITIZE — 数据脱敏

> **版本**：v2.0
> **日期**：2026-06-20
> **依据**：v1 教训 L118-L120（隐私保护）

---

## 1. 脱敏对象

| 数据类型 | 脱敏方式 | 示例 |
|---------|---------|------|
| 邮箱 | hash | `user@example.com` → `u***@example.com` |
| 手机号 | 中间 4 位 * | `13800001234` → `138****1234` |
| 身份证 | 保留前 4 后 4 | `110101199001011234` → `1101********1234` |
| 真实姓名 | 替换为化名 | `张三` → `张*` |
| 银行卡 | 保留前 4 后 4 | `6225****1234` |
| 钉钉 webhook | 部分隐藏 | `https://oapi.dingtalk.com/robot/send?access_token=***` |

## 2. 自动脱敏脚本

```python
# scripts/desensitize.py
def desensitize_email(email: str) -> str: ...
def desensitize_phone(phone: str) -> str: ...
def desensitize_id_card(id_card: str) -> str: ...
def desensitize_name(name: str) -> str: ...
```

## 3. 脱敏检查

```bash
# commit 前自动跑
python scripts/desensitize.py --check
```

## 4. 脱敏原则

1. **不可逆**：hash 不用 MD5（不安全），用 SHA256
2. **一致性**：同一数据每次脱敏结果相同
3. **可逆性**：业务需要时可逆（加密存储）
4. **审计**：所有脱敏操作记入 audit_log

## 5. 隐私分级

| 级别 | 数据 | 保护 |
|------|------|------|
| L0 公开 | ETF 代码、价格、池角色 | 无需保护 |
| L1 内部 | 业务库结构、IC/IR 验证值 | 仓内可访问 |
| L2 私密 | 用户实盘记录、情绪标签 | 脱敏 + 加密 |
| L3 机密 | 钉钉 webhook、API 密钥 | 环境变量 + 不入 Git |

## 6. 关键原则

- 业务数据删除前确认"数据 vs 角色"（规则 21）
- 默认值宁严勿宽（规则 19）
- 隐私保护是 safety_gate 的一部分
