PY ?= .venv/bin/python
N ?= 2000
IMPL ?= fast
CAT ?=

CATALOGUES = mock_2k mock_20k mock_200k
CAT_ERROR = CAT must be one catalogue name: mock_2k or mock_20k or mock_200k
CATALOGUE_ARG = $(if $(strip $(CAT)),$(if $(or $(filter-out $(CATALOGUES),$(CAT)),$(word 2,$(CAT))),$(error $(CAT_ERROR)),--catalogue $(strip $(CAT))))

.PHONY: bench check profile fit log status

bench:
	$(PY) bench/harness.py bench --impl $(IMPL) --n $(N) $(CATALOGUE_ARG)

check:
	$(PY) bench/harness.py check --n $(N) $(CATALOGUE_ARG)

profile:
	$(PY) bench/harness.py profile

fit:
	$(PY) bench/harness.py fit

log:
	./race log

status:
	./gate status
	./race status
