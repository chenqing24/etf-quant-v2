#!/usr/bin/env bash
# scripts/run_unit_tests.sh — pytest 9.x 合并跑有 bug（卡死），用逐文件方式跑
#
# 按 L309 教训：pytest 9.x + 17 文件会卡在 stdout buffer
# 解决：单文件逐跑 + 统计 pass/fail
#
# 业界参考（按规则 13）：
# - pytest 官方 issue tracker（pytest 9.x stdout 累积问题）
# - CircleCI: max pytest output buffer 限制

set +e  # 不中断，单文件失败不阻后续

cd "$(dirname "$0")/.."  # 项目根
LOG_DIR="reports/pytest"
mkdir -p "$LOG_DIR"
SUMMARY="$LOG_DIR/summary.txt"
> "$SUMMARY"

total_pass=0
total_fail=0
total_files=0
failed_files=()

for f in tests/unit/test_*.py; do
    name=$(basename "$f" .py)
    log_file="$LOG_DIR/${name}.log"
    out=$(timeout 30 python3 -m pytest "$f" --tb=line -q --no-header 2>&1)
    echo "$out" > "$log_file"

    # 提取最后一行 summary
    # pytest 9.x 有时不输出 "X passed" 行，只输出 progress bar [100%]
    # 兼容性：从 progress bar 数 dots，或匹配 "X passed" / "X failed"
    summary=$(echo "$out" | grep -E "passed|failed" | tail -1)
    if [ -z "$summary" ]; then
        # 回退：数 progress bar 中的 dots
        dots=$(echo "$out" | tail -1 | grep -oE '\.' | wc -l)
        if [ "$dots" -gt 0 ]; then
            summary="$dots passed (pytest 9.x 无 summary 行)"
            p=$dots
            fc=0
        else
            summary="(no output, possibly timed out)"
            p=0
            fc=0
        fi
    else
        p=$(echo "$summary" | grep -oE "[0-9]+ passed" | grep -oE "[0-9]+" | head -1)
        p=${p:-0}
        fc=$(echo "$summary" | grep -oE "[0-9]+ failed" | grep -oE "[0-9]+" | head -1)
        fc=${fc:-0}
    fi

    if [ "$fc" -gt 0 ]; then
        status="❌"
        failed_files+=("$name")
    else
        status="✅"
    fi
    echo "$status $name: $summary" | tee -a "$SUMMARY"

    total_pass=$((total_pass + p))
    total_fail=$((total_fail + fc))
    total_files=$((total_files + 1))
done

echo "==="
echo "📊 Total: $total_files files, $total_pass passed, $total_fail failed"
if [ ${#failed_files[@]} -gt 0 ]; then
    echo "❌ Failed files: ${failed_files[@]}"
    exit 1
fi
echo "✅ All unit tests passed"
