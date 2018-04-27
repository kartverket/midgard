# Makefile for simple installation of the Midgard Python Library

# Programs and directories
DOCSDIR = $(CURDIR)/documents/docs
DOCSDIR_WWW = $(CURDIR)/www


# Define phony targets (targets that are not files)
.PHONY: develop install doc test


# Install in developer mode (no need to reinstall after changing source)
develop:
	flit install -s


# Regular install, freezes the code so must reinstall after changing source code
install:
	flit install --deps production


# Create documentation
doc:
	( cd $(DOCSDIR) && make html && cp -R build/html $(DOCSDIR_WWW) )


# Run tests
test:
	( cd midgard && pytest --doctest-modules )

