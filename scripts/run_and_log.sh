#!/bin/bash
# run_and_log.sh — ETF skill 日志三份分离包装器（L321 教训 P1-3）
#
# 用途：把 run_daily.py 三个模式（daily/eval/history）的输出自动分离到：
#   1. ${LOG_DIR}/decision_${TS}.json  ← JSON 决策结果（机器读）
#   2. ${LOG_DIR}/stdout_${TS}.log     ← 控制台输出（人读 + grep）
#   3. ${LOG_DIR}/stderr_${TS}.log     ← 错误流（debug）
#
# 使用：
#   bash scripts/run_and_log.sh daily              # 跑 daily
#   bash scripts/run_and_log.sh eval               # 跑 eval
#   bash scripts/run_and_log.sh history            # 跑 history
#   bash scripts/run_and_log.sh daily --db-path X  # 透传参数
#
# 默认 LOG_DIR = reports/etf-daily-logs/YYYY-MM-DD/
# 可通过 LOG_DIR 环境变量覆盖
#
# 业界参考：
# - 12-Factor App § XI Logs：stdout/stderr 分流
# - systemd journald：自动按优先级分流
# - GNU tee --output-error=warn：管道最佳实践
# - bash 重定向优先级 (2>err 1>out 的顺序敏感)

set -euo pipefail

# ---------- 1. 解析参数 ----------
MODE="${1:-daily}"
shift 2>/dev/null || true
EXTRA_ARGS=("$@")

# 验证 mode
case "${MODE}" in
    daily|eval|history) ;;
    *) echo "❌ 无效 mode: ${MODE}（应是 daily/eval/history）" >&2; exit 2 ;;
esac

# ---------- 2. 计算日志目录 ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 日期子目录
DATE_STR="$(date +%Y-%m-%d)"
TS_STR="$(date +%Y%m%d_%H%M%S)"

# 报告目录：默认 reports/etf-daily-logs/YYYY-MM-DD/
LOG_DIR="${LOG_DIR:-${REPO_ROOT}/reports/etf-daily-logs/${DATE_STR}}"
mkdir -p "${LOG_DIR}"

DECISION_FILE="${LOG_DIR}/decision_${MODE}_${TS_STR}.json"
STDOUT_FILE="${LOG_DIR}/stdout_${MODE}_${TS_STR}.log"
STDERR_FILE="${LOG_DIR}/stderr_${MODE}_${TS_STR}.log"

# ---------- 3. 启动提示 ----------
echo "=========================================="
echo "[run_and_log] mode     = ${MODE}"
echo "[run_and_log] repo     = ${REPO_ROOT}"
echo "[run_and_log] log_dir  = ${LOG_DIR}"
echo "[run_and_log] decision = ${DECISION_FILE}"
echo "=========================================="

# ---------- 4. 跑命令，三份分离 ----------
# 关键：重定向顺序
#   - 2>${STDERR_FILE} 先把 stderr 单独走（否则会进 stdout 漏斗）
#   - 1>${STDOUT_FILE} 把 stdout 单独走
#   - tee 复制 stdout 到 decision 文件（grep 第一次 { 行）
# 注意：tee 必须先接 stdout 才会拿到 json

set +e
cd "${REPO_ROOT}"

# 拆 run_daily 输出：第一行 { 之前是 prompt，{ 之后到结尾是 JSON
python "${REPO_ROOT}/skills/etf-daily/scripts/run_daily.py" "${MODE}" "${EXTRA_ARGS[@]}" \
    1>"${STDOUT_FILE}" \
    2>"${STDERR_FILE}"

EXIT_CODE=$?
set -e

# ---------- 5. 抽 JSON 行到 decision 文件 ----------
# SKILL 输出格式：可能有 db_path 提示 + JSON（prompt 是 stderr 已经被分流）
# 从 stdout 中抽第一行 { 开始到结尾的 JSON
if [ -s "${STDOUT_FILE}" ]; then
    # 用 awk 抽 { 起始的行到结尾
    awk '/^{/,/^}/' "${STDOUT_FILE}" > "${DECISION_FILE}" || true
fi

# ---------- 6. 验证 decision JSON（规则 18）----------
DECISION_VALID=0
if [ -s "${DECISION_FILE}" ]; then
    if python -c "import json, sys; json.load(open('${DECISION_FILE}'))" 2>/dev/null; then
        DECISION_VALID=1
    fi
fi

# ---------- 7. 打印汇总 ----------
echo "=========================================="
echo "[run_and_log] exit_code        = ${EXIT_CODE}"
echo "[run_and_log] decision_valid   = ${DECISION_VALID} (1=OK)"
echo "[run_and_log] stdout_lines     = $(wc -l < "${STDOUT_FILE}")"
echo "[run_and_log] stderr_lines     = $(wc -l < "${STDERR_FILE}")"
echo "[run_and_log] decision_file    = ${DECISION_FILE}"
echo "=========================================="

# 退出码透传
exit ${EXIT_CODE}
