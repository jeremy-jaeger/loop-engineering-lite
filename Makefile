.PHONY: help test run demo lint

help:
	@echo "make test   — unit tests (no Ollama)"
	@echo "make run    — python3 main.py \"$(PROMPT)\""
	@echo "make demo   — print example prompts"

test:
	python3 -m pytest -q

run:
	@test -n "$(PROMPT)" || (echo 'Usage: make run PROMPT="your task"'; exit 1)
	python3 main.py "$(PROMPT)"

demo:
	@sed -n '1,80p' examples/prompts/starter.md
