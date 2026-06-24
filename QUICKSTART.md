# 🚀 5 分钟快速开始

> **借鉴**：[Divio Tutorial 风格](https://docs.divio.com/documentation-guide/) + [Carpentries Instructional Design](https://carpentries.org/workshops)
> **目标**：5 分钟跑通 ETF 每日决策
> **适用**：散户/教学用户/新手开发者

---

## 1️⃣ 安装（1 分钟）

```bash
# 克隆项目
git clone https://github.com/your-org/etf-quant-v2.git
cd etf-quant-v2

# 创建虚拟环境（避免污染全局 Python）
python3 -m venv ~/etf-env
source ~/etf-env/bin/activate

# 安装依赖（含开发依赖）
pip install -e ".[dev]"
```

**验证**：
```bash
python3 -c "from etf_quant.alpha.factors import FACTOR_REGISTRY; print(f'✅ {len(FACTOR_REGISTRY)} 因子已注册')"
# 期望输出：✅ 28 因子已注册
```

---

## 2️⃣ 初始化数据库（1 分钟）

```bash
# 一键初始化（创建 etf.db + schema + 默认池）
python3 scripts/init_database.py
```

**验证**：
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('data/etf.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM etf_names WHERE pool_role=\"core\"')
print(f'✅ core 池 {cur.fetchone()[0]} 只 ETF')
"
```

---

## 3️⃣ 拉取数据（1 分钟）

```bash
# 拉取 core 池 14 只 ETF 历史数据
python3 scripts/update_core_etf_data.py
```

**期望**：
```
[ 1/14] 512170: ✅ +320 条 | 最新 2026-06-24
[ 2/14] 512200: ✅ +320 条 | 最新 2026-06-24
...
✅ 成功: 14/14
```

---

## 4️⃣ 跑每日决策（1 分钟）

```bash
# 跑每日决策
python3 skills/etf-daily/scripts/run_daily.py daily
```

**期望输出**：
```json
{
  "model_name": "v2_sop",
  "strategy_name": "C21Strategy",
  "market_mode": "trend_up",
  "decision": "HOLD",
  "holdings_count": 1,
  "holdings_detail": [{"code": "512170"}]
}
```

---

## 5️⃣ 跑真实回测（1 分钟）

```bash
# 单只回测
python3 scripts/run_real_backtest.py single 512170

# 全 core 池回测（30-60 秒）
python3 scripts/run_real_backtest.py all
```

**期望输出**：
```json
{
  "code": "512170",
  "total_return": -33.98,
  "sharpe": -0.65,
  "max_drawdown": -37.42,
  "n_trades": 8
}
```

---

## 🎯 跑通后下一步

| 你想 | 看哪里 |
|------|--------|
| 理解 27 因子含义 | [docs/SKILL_USER_GUIDE.md](docs/SKILL_USER_GUIDE.md) |
| 看策略回测历史表现 | [scripts/run_real_backtest.py](scripts/run_real_backtest.py) |
| 调整因子权重 | [configs/factor_weights.yaml](configs/factor_weights.yaml) |
| 跑 examples 案例 | `examples/` 目录（5 个 Jupyter notebook）|
| 贡献代码 | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

## 🆘 故障排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `ModuleNotFoundError: No module named 'etf_quant'` | 没装 v2 | `pip install -e ".[dev]"` |
| `No such file: data/etf.db` | 没初始化 | `python3 scripts/init_database.py` |
| `akshare.RemoteDisconnected` | 数据源断连 | 改用 [腾讯接口](scripts/update_core_etf_data.py)（已内置 fallback）|
| `pytest 卡死` | L318 已知问题 | 单文件跑：`pytest tests/unit/test_xxx.py -v` |

更多 → [docs/FAQ.md](docs/FAQ.md)

---

## 📚 业界参考（按 SOUL.md 规则 13）

| 资源 | 借鉴点 |
|------|--------|
| [Divio Documentation](https://docs.divio.com/documentation-guide/) | Tutorial 风格 |
| [Carpentries Workshops](https://carpentries.org/workshops) | 教学设计 |
| [Bloom's Taxonomy](https://en.wikipedia.org/wiki/Bloom%27s_taxonomy) | 学习目标分 6 层 |
| [Kirkpatrick Model](https://en.wikipedia.org/wiki/Kirkpatrick_model) | 培训效果 4 层 |