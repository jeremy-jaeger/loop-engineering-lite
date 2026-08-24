.PHONY: help test demo run

help:
	@echo "make test   — unit tests (no Ollama)"
	@echo "make demo   — offline VFS walkthrough (no Ollama)"
	@echo "make run    — python3 main.py \"$(PROMPT)\""

test:
	python3 -m pytest -q

demo:
	python3 examples/offline_vfs_demo.py

run:
	@test -n "$(PROMPT)" || (echo 'Usage: make run PROMPT="your task"'; exit 1)
	python3 main.py "$(PROMPT)"
