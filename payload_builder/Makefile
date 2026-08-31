PY ?= python3
SZL_V14 ?= ../szl-v14

.PHONY: all generate compile extract export verify idempotent test clean

all:
	$(PY) build.py all

generate:
	$(PY) build.py generate

compile:
	$(PY) build.py compile

extract:
	$(PY) build.py extract

export:
	$(PY) build.py export

verify:
	$(PY) build.py verify

# Receipts carry timestamps (they are events, not artifacts) and are excluded.
# The payload body and manifest must be byte-identical across rebuilds.
idempotent:
	rm -rf dist
	$(PY) build.py all
	mkdir -p /tmp/pb-idem && cp dist/SZL_MASTER_PAYLOAD_V14.md /tmp/pb-idem/p1.md && cp dist/manifest.json /tmp/pb-idem/m1.json
	rm -rf dist
	$(PY) build.py all
	diff -q /tmp/pb-idem/p1.md dist/SZL_MASTER_PAYLOAD_V14.md
	diff -q /tmp/pb-idem/m1.json dist/manifest.json
	@echo "IDEMPOTENT: byte-identical rebuild proven"

test:
	cd $(SZL_V14) && $(PY) -m pytest -q

clean:
	rm -rf dist
