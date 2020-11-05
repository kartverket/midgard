# Makefile for simple serving and building of the Midgard web page

.PHONY: serve build

# Serve the web page locally
serve:
	firefox localhost:8000 &
	python generate_api.py --watch &
	mkdocs serve

# Build the HTML site
build:
	python generate_api.py
	mkdocs build

