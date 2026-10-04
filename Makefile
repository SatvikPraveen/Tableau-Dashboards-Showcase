PYTHON ?= python3

.PHONY: help verify audit inventory docs test lint check

help:  ## List available targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

verify:  ## Verify checksums, schema and aggregate identities of the raw data
	$(PYTHON) -m tools.verify_data

audit:  ## Print the analytical audit of the published dashboards
	$(PYTHON) -m tools.audit

inventory:  ## Print the workbook inventory
	$(PYTHON) -m tools.inspect_workbooks

docs:  ## Regenerate docs/analytical_audit.md and docs/workbook_inventory.md
	$(PYTHON) -m tools.audit --write
	$(PYTHON) -m tools.inspect_workbooks --write

test:  ## Run the unit and regression tests
	$(PYTHON) -m unittest discover -s tests -t . -v

lint:  ## Lint and format-check the Python tooling (requires ruff)
	ruff check tools tests
	ruff format --check tools tests

check: verify test  ## Everything CI runs, except lint
	$(PYTHON) -m tools.audit --check
	$(PYTHON) -m tools.inspect_workbooks --check
