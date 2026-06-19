# QUICKSTART — 5 分钟快速开始

> **版本**：v2.0
> **日期**：2026-06-20
> **目标**：5 分钟让新用户跑通 etf-quant-v2 核心流程

---

## 1. 装环境（1 分钟）

```bash
# 克隆仓
git clone <etf-quant-v2>

# 装依赖
cd etf_quant_v2
pip install -e ".[dev]"
```

## 2. 跑测试（1 分钟）

```bash
# 跑所有测试（不含 benchmark 约 2 分钟）
pytest tests/ --ignore=tests/benchmark -q

# 期望：217+ passed
```

## 3. 跑 5 Skill 入口（1 分钟）

```bash
# 1. ETF 每日决策
python skills/etf-daily/scripts/run_daily.py daily

# 2. ETF 深度研究
python skills/etf-research/scripts/run_validate.py validate

# 3. 个股分析
python skills/stock-analyze/scripts/run_analyze.py info 159338

# 4. 组合状态
python skills/stock-portfolio/scripts/run_portfolio.py status

# 5. 量化知识
python skills/quant-knowledge/scripts/run_knowledge.py strategy
```

## 4. 跑完整流程（1 分钟）

```bash
# 8 步完整 demo
python demo_full_flow.py
```

## 5. 8 维度腐化自检（1 分钟）

```bash
# 检查代码质量
python scripts/腐化自检.py --non-interactive --sprint=7

# 期望：100/100
```

## 下一步

- 阅读 `docs/PRD.md` 了解产品需求
- 阅读 `docs/ARCHITECTURE.md` 了解架构
- 阅读 `docs/INTERFACE_CONTRACT.md` 了解接口
- 阅读 `docs/DATA_DICTIONARY.md` 了解数据库
- 阅读 5 SOP（`docs/SOP_01_DATA.md` 等）了解流程规范

## 常见问题

### Q1: 测试失败怎么办？

```bash
# 1. 检查 Python 版本（≥ 3.11）
python3 --version

# 2. 重新装依赖
pip install -e ".[dev]" --force-reinstall

# 3. 跑单个测试文件
pytest tests/unit/alpha/test_factors.py -v
```

### Q2: pre-commit 拦截怎么办？

```bash
# 1. 看拦截原因
python scripts/git-hooks/pre-commit

# 2. 修复（一般是缺标准注释或缺测试）

# 3. 重新 commit
```

### Q3: 数据过期怎么办？

```bash
# 1. 看数据健康
python -c "from etf_quant.monitor import DataHealthMonitor; print(DataHealthMonitor().check())"

# 2. 手动更新（如果有数据源）
python scripts/refetch_etf_data.py
```

## 联系

- GitHub Issues: <repo>/issues
- 文档：`docs/INDEX.md`（待建）
- 教训库：`memory/lessons/`
