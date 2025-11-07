#!/bin/bash
echo "=========================================="
echo "RUNNING ALL API INTEGRATION TESTS"
echo "=========================================="
echo ""

declare -A results
tests=(
  "test_hyperliquid.py"
  "test_market_data.py"
  "test_order_operations.py"
  "test_error_handling.py"
  "test_portfolio_use_cases.py"
  "test_scale_order_use_cases.py"
)

for test in "${tests[@]}"; do
  echo "Running $test..."
  if uv run python scripts/$test > /tmp/${test}_v2.log 2>&1; then
    results[$test]="✅ PASS"
    echo "  ✅ PASS"
  else
    results[$test]="❌ FAIL"
    echo "  ❌ FAIL"
    echo ""
    echo "--- Last 30 lines of error log ---"
    tail -30 /tmp/${test}_v2.log
    echo ""
  fi
  echo ""
done

echo "=========================================="
echo "SUMMARY"
echo "=========================================="
for test in "${tests[@]}"; do
  echo "${results[$test]}: $test"
done

# Count results
pass_count=0
fail_count=0
for test in "${tests[@]}"; do
  if [[ ${results[$test]} == "✅ PASS" ]]; then
    ((pass_count++))
  else
    ((fail_count++))
  fi
done

echo ""
echo "Results: $pass_count/${#tests[@]} tests passed"
if [ $fail_count -eq 0 ]; then
  echo "🎉 ALL TESTS PASSED!"
  exit 0
else
  echo "❌ $fail_count TEST(S) FAILED"
  exit 1
fi
