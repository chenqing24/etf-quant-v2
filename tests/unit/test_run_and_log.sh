#!/bin/bash
# test_run_and_log.sh — run_and_log.sh 包装器测试（L321 教训 P1-3）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WRAPPER="${REPO_ROOT}/scripts/run_and_log.sh"
LOG_DIR="${REPO_ROOT}/reports/etf-daily-logs-test/$(date +%Y-%m-%d)"

echo "==============================================="
echo "[test_run_and_log] repo     = ${REPO_ROOT}"
echo "[test_run_and_log] log_dir  = ${LOG_DIR}"
echo "==============================================="

# ---------- 测试 1: daily 模式三份分离 ----------
echo "=== test 1: daily mode ==="
LOG_DIR="${LOG_DIR}" bash "${WRAPPER}" daily >/dev/null
# wrapper 内部已用 LOG_DIR 完整路径（包含日期子目录）
LOG_PATH="${LOG_DIR}"
test -d "${LOG_PATH}" || { echo "❌ 日志目录未创建: ${LOG_PATH}"; ls -la "${REPO_ROOT}/reports/etf-daily-logs-test/" 2>/dev/null; exit 1; }

# 检查三份文件都存在
DECISION=$(ls -t "${LOG_PATH}"/decision_daily_*.json | head -1)
STDOUT=$(ls -t "${LOG_PATH}"/stdout_daily_*.log | head -1)
STDERR=$(ls -t "${LOG_PATH}"/stderr_daily_*.log | head -1)

test -s "${DECISION}" || { echo "❌ decision 文件为空或不存在: ${DECISION}"; exit 1; }
test -s "${STDOUT}" || { echo "❌ stdout 文件为空或不存在: ${STDOUT}"; exit 1; }
test -s "${STDERR}" || { echo "❌ stderr 文件为空或不存在: ${STDERR}"; exit 1; }
echo "  ✓ 三份文件都存在且非空"
echo "    decision: ${DECISION}"
echo "    stdout:   ${STDOUT}"
echo "    stderr:   ${STDERR}"

# ---------- 测试 2: decision JSON 有效（规则 18）----------
python -c "import json; d=json.load(open('${DECISION}')); assert 'decision' in d, '缺少 decision 字段'; assert 'market_mode' in d, '缺少 market_mode 字段'; print(f'  ✓ decision JSON 有效：decision={d[\"decision\"]}, market_mode={d[\"market_mode\"]}')" || { echo "❌ decision JSON 无效"; exit 1; }

# ---------- 测试 3: 无效 mode 应拒绝 ----------
echo "=== test 3: invalid mode ==="
if LOG_DIR="${LOG_DIR}" bash "${WRAPPER}" invalid_mode >/dev/null 2>&1; then
    echo "❌ 无效 mode 应返回非 0 退出码"
    exit 1
fi
echo "  ✓ 无效 mode 被正确拒绝"

# ---------- 测试 4: 退出码透传 ----------
echo "=== test 4: 透传额外参数 ==="
set +e
LOG_DIR="${LOG_DIR}" bash "${WRAPPER}" daily --db-path /nonexistent/path/etf.db >/dev/null 2>&1
EXIT_CODE=$?
set -e
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "❌ 错误 db_path 应导致非 0 退出码，实际: ${EXIT_CODE}"
    exit 1
fi
echo "  ✓ 错误 db_path 透传：exit_code=${EXIT_CODE}"

echo "==============================================="
echo "✅ all tests passed"
echo "==============================================="
