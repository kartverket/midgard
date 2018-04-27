# Makefile for simple installation of the Midgard Python Library
#
# Authors:
# --------
#
# * Geir Arne Hjelle <geir.arne.hjelle@kartverket.no>
#
# $Revision: 13568 $
# $Date: 2017-10-25 11:07:40 +0200 (Wed, 25 Oct 2017) $
# $LastChangedBy: fauing $

# Programs and directories
DOCSDIR = $(CURDIR)/documents/docs
DOCSDIR_WWW = /home/geosat/doc-midgard

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
	( cd midgard && py.test --doctest-modules )

