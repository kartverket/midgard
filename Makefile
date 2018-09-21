# Makefile for simple installation of the Midgard Python Library

# Programs and directories
DOCSDIR = $(CURDIR)/documents/docs
DOCSDIR_WWW = $(CURDIR)/www


# Define phony targets (targets that are not files)
.PHONY: develop install format test typing doc

# Install in developer mode (no need to reinstall after changing source)
develop:
	python -m flit install -s

# Regular install, freezes the code so must reinstall after changing source code
install:
	python -m flit install --deps production

# Format code
black:
	python -m black --line-length=119 .

# Run tests
test:
	python -m pytest --doctest-modules --cov=midgard --cov-report=term-missing

typing:
	python -m mypy --ignore-missing-imports --disallow-untyped-defs --disallow-untyped-calls midgard

# Create documentation
doc:
	( cd $(DOCSDIR) && make html && cp -R build/html $(DOCSDIR_WWW) )

