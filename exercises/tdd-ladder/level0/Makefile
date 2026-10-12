PY ?= .venv/bin/python

.PHONY: test plot status

test:
	$(PY) -m pytest -q

plot:
	PYTHONPATH=src $(PY) -c "from hzbin.plot import main; main()"

status:
	./gate status
	./tdd status
