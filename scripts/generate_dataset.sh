#!/usr/bin/env bash
# Feed TDD tasks through the live loop and append successful traces to data/train.jsonl.
# Requires Ollama. Writes files into this repository's working tree on success —
# copy the repo or pass a disposable checkout if that matters.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p data
echo "Starting autonomous data generation from $ROOT"

tasks=(
  "Use TDD to write a Python string utility in 'str_utils.py' that checks if a string is a palindrome. Write tests in test_str_utils.py for 'racecar', 'hello', and an empty string. Use python3 -m pytest -q."
  "Use TDD to build a 'Temperature' class in 'temp.py' that initializes in Celsius but has a property to get Fahrenheit. Test freezing and boiling points. Tests in test_temp.py. python3 -m pytest -q."
  "Use TDD to write a 'fibonacci(n)' function in 'math_utils.py'. Test that fib(0) is 0, fib(1) is 1, and fib(10) is 55. Raise ValueError for negative numbers. Tests in test_math_utils.py. python3 -m pytest -q."
  "Use TDD to build a simple 'Stack' class using a Python list. Implement push, pop, and peek methods. Test that popping an empty stack raises an IndexError. Tests in test_stack.py must instantiate Stack(). python3 -m pytest -q."
  "Use TDD to write a 'validate_email(email)' function using regex in 'validator.py'. Test 'test@test.com', 'invalid-email', and '@missingusername.com'. Tests in test_validator.py. python3 -m pytest -q."
)

for task in "${tasks[@]}"; do
  echo "-----------------------------------"
  echo "Running task: $task"
  python3 main.py --no-reflect "$task" || true
  if [[ -f dataset.jsonl ]]; then
    cat dataset.jsonl >> data/train.jsonl
    rm dataset.jsonl
    echo "[DATA CAPTURED] Trajectory appended to data/train.jsonl"
  else
    echo "[TASK FAILED] Agent did not succeed. Check data/rejected.jsonl."
  fi
done

echo "Batch generation complete."
