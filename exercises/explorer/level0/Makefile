PY ?= .venv/bin/python
DATA ?= $(shell sed -n 's/^Dataset:[[:space:]]*//p' PLAN.md)
OUT ?= out
ARGS ?=

.PHONY: explore open list test coverage status

explore:
	$(PY) -m explorer $(DATA) --out $(OUT) $(ARGS)
open:
	open $(OUT)/explorer.html
list:
	$(PY) -m explorer $(DATA) --list
test:
	$(PY) -m pytest -q
coverage:
	$(PY) -m pytest -q --cov=explorer --cov-report=term-missing
status:
	./gate status
