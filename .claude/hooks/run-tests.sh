#!/bin/bash
# 分层递进测试脚本：unit → integration → e2e
# 任一层失败即停止，返回格式化结果

set -eo pipefail

cd "${CLAUDE_PROJECT_DIR:?CLAUDE_PROJECT_DIR not set}" || exit 1

# 激活虚拟环境（如果存在）
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

UNIT_RESULT="--"
INTEG_RESULT="--"
E2E_RESULT="--"
OVERALL_EXIT_CODE=0

# 运行指定标记的测试，处理 exit code 5（无测试=通过）
run_tests() {
    local marker=$1
    pytest -m "$marker" -v --tb=short 2>&1
    local exit_code=$?
    if [ $exit_code -eq 0 ] || [ $exit_code -eq 5 ]; then
        return 0
    fi
    return 1
}

# 1. 单元测试
echo "=== 单元测试 ==="
if run_tests unit; then
    UNIT_RESULT="[PASS] 通过"
    echo ""
    echo "=== 集成测试 ==="
    if run_tests integration; then
        INTEG_RESULT="[PASS] 通过"
        echo ""
        echo "=== 端到端测试 ==="
        if run_tests e2e; then
            E2E_RESULT="[PASS] 通过"
        else
            E2E_RESULT="[FAIL] 失败"
            OVERALL_EXIT_CODE=1
        fi
    else
        INTEG_RESULT="[FAIL] 失败"
        E2E_RESULT="[SKIP] 跳过（集成测试未通过）"
        OVERALL_EXIT_CODE=1
    fi
else
    UNIT_RESULT="[FAIL] 失败"
    INTEG_RESULT="[SKIP] 跳过（单元测试未通过）"
    E2E_RESULT="[SKIP] 跳过（单元测试未通过）"
    OVERALL_EXIT_CODE=1
fi

echo ""
echo "=== 测试报告 ==="
echo "单元测试: $UNIT_RESULT"
echo "集成测试: $INTEG_RESULT"
echo "端到端测试: $E2E_RESULT"

exit $OVERALL_EXIT_CODE
