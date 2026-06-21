#!/bin/bash
# demo_walkthrough.sh — US-012 完整走查脚本

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$SKILL_DIR/tests/integration"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/walkthrough_$(date +%Y%m%d_%H%M%S).log"
SCRIPTS_DIR="$SKILL_DIR/scripts"
DB_PATH="$SKILL_DIR/../../data/etf.db"

cd "$SKILL_DIR/../.."

echo "===========================================" | tee "$LOG_FILE"
echo "US-012 完整走查：$(date)" | tee -a "$LOG_FILE"
echo "===========================================" | tee -a "$LOG_FILE"

run_step() {
    local desc="$1"
    shift
    echo "" | tee -a "$LOG_FILE"
    echo "[$desc]" | tee -a "$LOG_FILE"
    echo "  命令: $*" | tee -a "$LOG_FILE"
    python3 "$@" 2>&1 | head -20 | tee -a "$LOG_FILE"
}

# Step 1: 重置
run_step "1/10 reset" "$SCRIPTS_DIR/run_onboard.py" reset

# Step 2: 看 universe 默认池
run_step "2/10 universe default" "$SCRIPTS_DIR/run_universe.py" default

# Step 3: 改 universe 池
run_step "3/10 universe modify" \
    "$SCRIPTS_DIR/run_universe.py" modify --add 159915 --remove 512170

# Step 4: 推进到 alpha
run_step "4/10 onboard --confirm (universe → alpha)" \
    "$SCRIPTS_DIR/run_onboard.py" onboard --confirm

# Step 5: 看 alpha 因子
run_step "5/10 alpha factors" "$SCRIPTS_DIR/run_alpha.py" factors

# Step 6: 加 alpha 因子
run_step "6/10 alpha add" "$SCRIPTS_DIR/run_alpha.py" add --factor WALKTHROUGH_TEST

# Step 7: 推进到 risk
run_step "7/10 onboard --confirm (alpha → risk)" \
    "$SCRIPTS_DIR/run_onboard.py" onboard --confirm

# Step 8: 改 risk 纪律
run_step "8/10 risk modify" \
    "$SCRIPTS_DIR/run_risk.py" modify --stop_loss -0.05 --max_position_pct 0.30

# Step 9: 完成 risk
run_step "9/10 onboard --confirm (risk → done)" \
    "$SCRIPTS_DIR/run_onboard.py" onboard --confirm

# Step 10: 状态总览
run_step "10/10 status" "$SCRIPTS_DIR/run_onboard.py" status

echo "" | tee -a "$LOG_FILE"
echo "===========================================" | tee -a "$LOG_FILE"
echo "走查完成：$LOG_FILE" | tee -a "$LOG_FILE"
echo "===========================================" | tee -a "$LOG_FILE"

# 清理测试数据
if [ -f "$DB_PATH" ]; then
    python3 -c "
import sqlite3
c = sqlite3.connect('$DB_PATH')
c.execute(\"UPDATE etf_names SET pool_role='reference' WHERE code='159915'\")
c.execute(\"UPDATE etf_names SET pool_role='core' WHERE code='512170'\")
c.commit()
print('rolled back 159915/512170')
" | tee -a "$LOG_FILE"
fi
rm -f "$SKILL_DIR/state/"*.json "$SKILL_DIR/state.json" 2>/dev/null
echo "state 清理完成" | tee -a "$LOG_FILE"