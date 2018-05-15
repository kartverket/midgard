# Makefile for simple installation of the Midgard Python Library

# Programs and directories
DOCSDIR = $(CURDIR)/documents/docs
DOCSDIR_WWW = $(CURDIR)/www


# Define phony targets (targets that are not files)
.PHONY: develop install format test typing doc

# Install in developer mode (no need to reinstall after changing source)
develop:
	flit install -s

# Regular install, freezes the code so must reinstall after changing source code
install:
	flit install --deps production

# Format code
black:
	black --line-length=119 .

# Run tests
test:
	pytest --cov=midgard --cov-report=term-missing

typing:
	mypy --ignore-missing-imports midgard

# Create documentation
doc:
	( cd $(DOCSDIR) && make html && cp -R build/html $(DOCSDIR_WWW) )

