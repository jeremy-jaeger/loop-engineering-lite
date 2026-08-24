These Python files were produced by live TDD runs of the harness.
They are examples of *output*, not of the runtime itself.

Quality is intentionally mixed: tests may be incomplete, classes may be
defined in the wrong file, comments may disagree with the code. That is
why the loop simulates `pytest` before it commits.

Notable verified run: `money.py` + `test_money.py` (checkout
`dollars_to_cents`) — live Ollama TDD that only committed after pytest
passed. See [../real_world/checkout_money.md](../real_world/checkout_money.md).
