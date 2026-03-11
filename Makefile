PYTHON ?= python

.PHONY: lint validate package-assets chart-package release-dry-run stack-manifest

lint:
	$(PYTHON) scripts/tasks.py lint

validate:
	$(PYTHON) scripts/tasks.py validate

package-assets:
	$(PYTHON) scripts/tasks.py package-assets

chart-package:
	$(PYTHON) scripts/tasks.py chart-package

release-dry-run:
	$(PYTHON) scripts/tasks.py release-dry-run

stack-manifest:
	$(PYTHON) scripts/tasks.py stack-manifest
