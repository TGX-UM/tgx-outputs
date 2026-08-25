# Everything a contributor needs, without reading the CI files.
.PHONY: help install check offline collect derive build serve record fixtures clean

help:
	@echo "make install   install the package and dev tools into the current environment"
	@echo "make check     config validation, lint, and the offline test suite"
	@echo "make offline   build the whole site from fixtures with no network at all"
	@echo "make collect   fetch every enabled source live"
	@echo "make serve     build and serve the site at http://localhost:8000"
	@echo "make record    re-record HTTP fixtures from live APIs, then trim them"

install:
	pip install -e ".[dev]"

check:
	@for f in sources roster exclusions metric_semantics; do \
		check-jsonschema --schemafile schemas/$$f.schema.json config/$$f.yml; done
	tgx doctor
	ruff check src tests scripts
	pytest -q

# The important target. If this passes, the build has no hidden network dependency and
# needs no credential -- which is what makes the project safe to fork and to hand over.
offline:
	TGX_HTTP_MODE=replay tgx collect --replay
	tgx derive
	tgx build
	mkdocs build --strict
	@echo "\n  built offline, with no network and no secrets"

collect:
	tgx collect

derive:
	tgx derive

build:
	tgx build
	mkdocs build

serve: build
	mkdocs serve

record:
	tgx collect --record
	$(MAKE) fixtures

# Recorded responses are what upstream actually returned -- for Bioconductor that is a
# 12 MB table. Trim before committing.
fixtures:
	python scripts/trim_fixtures.py

clean:
	rm -rf site includes/*.md docs/data/*.csv
