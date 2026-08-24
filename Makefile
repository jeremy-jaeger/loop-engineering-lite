.PHONY: help run demo

help:
	@echo "make run    — python3 main.py \"$(PROMPT)\""
	@echo "make demo   — print example prompts"

run:
	@test -n "$(PROMPT)" || (echo 'Usage: make run PROMPT="your task"'; exit 1)
	python3 main.py "$(PROMPT)"

demo:
	@sed -n '1,80p' examples/prompts/starter.md
