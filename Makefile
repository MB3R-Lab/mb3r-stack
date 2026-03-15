PYTHON ?= python

.PHONY: lint validate smoke-generic e2e-generic k8s-smoke-generic smoke-otel-demo e2e-otel-demo package-assets chart-package release-dry-run stack-manifest

lint:
	$(PYTHON) scripts/tasks.py lint

validate:
	$(PYTHON) scripts/tasks.py validate

smoke-generic:
	$(PYTHON) scripts/tasks.py smoke-generic

e2e-generic:
	$(PYTHON) scripts/tasks.py e2e-generic

k8s-smoke-generic:
	$(PYTHON) scripts/tasks.py k8s-smoke-generic

smoke-otel-demo:
	$(PYTHON) scripts/tasks.py smoke-otel-demo

e2e-otel-demo:
	$(PYTHON) scripts/tasks.py e2e-otel-demo

package-assets:
	$(PYTHON) scripts/tasks.py package-assets

chart-package:
	$(PYTHON) scripts/tasks.py chart-package

release-dry-run:
	$(PYTHON) scripts/tasks.py release-dry-run

stack-manifest:
	$(PYTHON) scripts/tasks.py stack-manifest
