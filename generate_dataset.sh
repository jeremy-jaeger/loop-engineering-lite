#!/bin/bash
echo "Starting Autonomous Data Generation..."

mkdir -p data adapters

# Progressively harder TDD tasks (training distribution). Held-out eval tasks live in improve/evaluate.py.
tasks=(
  "Use TDD to write a Python string utility in 'str_utils.py' that checks if a string is a palindrome. Write tests for 'racecar', 'hello', and an empty string."
  "Use TDD to build a 'Temperature' class in 'temp.py' that initializes in Celsius but has a property to get Fahrenheit. Test freezing and boiling points."
  "Use TDD to write a 'fibonacci(n)' function in 'math_utils.py'. Test that fib(0) is 0, fib(1) is 1, and fib(10) is 55. Raise ValueError for negative numbers."
  "Use TDD to build a simple 'Stack' class using a Python list. Implement push, pop, and peek methods. Test that popping an empty stack raises an IndexError."
  "Use TDD to write a 'validate_email(email)' function using regex in 'validator.py'. Test 'test@test.com', 'invalid-email', and '@missingusername.com'."
)

for task in "${tasks[@]}"; do
  echo "-----------------------------------"
  echo "Running Task: $task"
  python3 main.py "$task"
done

if [ -f dataset.jsonl ]; then
  cp dataset.jsonl data/train.jsonl
  echo "[DATA CAPTURED] Verified traces in dataset.jsonl and data/train.jsonl"
else
  echo "[NO CHOSEN TRACES] Agent produced no reward=1.0 rollouts."
fi

echo "Batch generation complete."
echo "Next: python3 -m improve prepare --chosen dataset.jsonl --rejected data/rejected.jsonl"
echo "Then: python3 -m improve train && python3 -m improve eval && python3 -m improve promote"
