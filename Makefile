
.PHONY: clean
CAT:= cat
PYTHON:= python3

bfc: bf.py
	{ \
		echo "#!/usr/bin/env sh"; \
		echo "python3 -- - \"\$$@\" <<\"__BREAK__\""; \
		cat $<; \
		echo "__BREAK__"; \
	} > $@
	chmod +x $@
bf.py: $(wildcard src/*.py)
	$(CAT) $^ > $@

clean:
	$(RM) bfc bf.py

