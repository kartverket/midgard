"""Generate API documentation from source files

The script will create Markdown files for all packages in the Midgard source
tree. These can be used, for instance by mkdocs, to create API documentation on
web pages.

Example:
--------

Create the API documentation by running the following:

    $ python generate_api.py

The script discovers packages by walking the directory tree starting at
SRC_ROOT (see below). Midgard must be installed for the script to be able to
gather API information.

During development, it might be useful to run with the `--watch` option:

    $ python generate_api.py --watch

After generating the API documentation, the script will watch all the source
code files, and when changes are detected the documentation is rebuilt.
"""

import importlib
import inspect
import pathlib
import re
import sys
import textwrap
import time

# Midgard imports
from midgard.dev import log


TEMPLATE = "mkdocs.yml_template"
OUTPUT = "mkdocs.yml"
SRC_ROOT = pathlib.Path(__file__).resolve().parent.parent / "midgard"
DST_ROOT = pathlib.Path(__file__).resolve().parent / "docs"
WATCH_SLEEP = 5  # Seconds to sleep between checking if files have changed


def main():
    log.init("info")

    packages = find_modules(SRC_ROOT, "midgard")
    out_paths = dict()
    timestamps = dict()

    # Create separate markdown api files for each package
    for package_name, modules in sorted(packages.items()):
        out_path, module_paths = document_package(package_name, modules)
        out_paths[package_name] = out_path
        for module_path in module_paths:
            timestamps[module_path] = module_path.stat().st_mtime, package_name

    # Update mkdocs.yml with paths to api files
    mkdocs_tpl = pathlib.Path(TEMPLATE).read_text()
    api_paths = "\n".join(f"        - {m}: {p.relative_to(DST_ROOT)}" for m, p in out_paths.items())
    mkdocs = mkdocs_tpl.format(api=api_paths)
    pathlib.Path(OUTPUT).write_text(mkdocs)

    if "--watch" in sys.argv:
        watch_files(timestamps, packages)


def watch_files(timestamps, packages):
    """Automatically refresh documentation at given intervals"""
    refresh = set()
    for path, (timestamp, package) in timestamps.items():
        if path.stat().st_mtime > timestamp:
            refresh.add(package)

    for package_name in refresh:
        modules = packages[package_name]
        for module_name in modules:
            del sys.modules[module_name]
        _, module_paths = document_package(package_name, modules)
        for module_path in module_paths:
            timestamps[module_path] = module_path.stat().st_mtime, package_name

    time.sleep(WATCH_SLEEP)
    return watch_files(timestamps, packages)


def document_package(package_name, modules):
    """Write documentation of one package to file"""
    module_paths = list()

    out_path = (DST_ROOT / "api" / package_name.replace(".", "-")).with_suffix(".md")
    module_docs = list()
    for module_name in sorted(modules):
        module = importlib.import_module(module_name)
        module_docs.append(document_module(module))
        module_paths.append(pathlib.Path(module.__file__))

    out_path.write_text("\n\n".join(module_docs))
    return out_path, module_paths


def find_modules(root_dir, root_mod):
    """Find all modules inside the root_dir"""
    packages = dict()
    for path in root_dir.glob("**/*.py"):
        rel_path = path.relative_to(root_dir)
        module = ".".join((root_mod,) + rel_path.with_suffix("").parts)
        if module.endswith(".__init__"):
            module = module[:-9]

        # Store module inside package
        package = ".".join(module.split(".")[:2])
        packages.setdefault(package, list()).append(module)

    return packages


def document_module(module):
    """Collect the full documentation of a module"""
    log.info(f"Adding documentation for {module.__name__}")
    docs = [_get_module_doc(module)]
    for obj_name in dir(module):
        obj = getattr(module, obj_name)
        if not _do_doc(obj_name, obj, module):
            continue
        docs.append(_get_doc(obj_name, obj, module))
    return "\n".join(docs)


def _get_module_doc(module):
    """Get and format the documentation for a module"""
    doc = module.__doc__ or ""

    # Replace headlines with bold text
    doc = re.sub(r"([\w ]+:)\n-+", r"**\1**", doc)
    num_hash = min(2, module.__name__.count("."))

    return f"{'#' * num_hash} {module.__name__}\n{doc}"


def _get_doc(obj_name, obj, module):
    """Get and format the documentation for an object"""
    list_headers = ["Args", "Attributes", "Returns", "Examples"]
    member_docs = list()

    if not callable(obj):
        return f"\n### {obj_name} ({obj.__class__.__name__})\n`{obj_name} = {obj!r}`\n"

    if not obj.__doc__:
        log.warn(f"No docstring found for {obj.__qualname__}")

    doc = textwrap.dedent((" " * 100) + (obj.__doc__ or "")).lstrip()

    paragraphs = doc.split("\n\n")
    doc_w_lists = list()
    for paragraph in paragraphs:
        if paragraph.split(":")[0] in list_headers:
            paragraph = re.sub(r"^(\w+:)", r"**\1**\n", paragraph)  # Bold header
            paragraph = re.sub(r"\n    (\w+):", r"\n- `\1`:", paragraph)
            paragraph = re.sub(r"\n    (\w)", r"\n\1", paragraph)
        doc_w_lists.append(paragraph)
    doc = "\n\n".join(doc_w_lists)

    if inspect.isclass(obj) and not isinstance(obj, type):
        for member_name in dir(obj):
            member = getattr(obj, member_name)
            if not _do_doc(member_name, member, module):
                continue
            member_doc = _get_doc(member_name, member, module)
            member_doc = re.sub(r"\n### ", rf"\n#### {obj_name}.", member_doc)
            member_docs.append(member_doc)
        doc += "\n".join(member_docs)

    try:
        signature = inspect.signature(obj)
    except (ValueError, TypeError):
        signature = "()"

    headline = f"### **{obj_name}**{'' if inspect.isclass(obj) else '()'}"
    qualname = f"Full name: `{module.__name__}.{obj_name}`"
    signature_str = f"Signature: `{signature}`"

    return f"\n{headline}\n\n{qualname}\n\n{signature_str}\n\n{doc}"


def _do_doc(name, obj, module):
    """Check if object should be documented"""

    # Do not document private objects
    if name.startswith("_"):
        return False

    # Do not document no_doc types
    no_docs = ["datadescriptor", "module", "memberdescriptor", "methoddescriptor", "getsetdescriptor"]
    for no_doc in no_docs:
        isfunc = getattr(inspect, f"is{no_doc}")
        if isfunc(obj):
            return False

    # Only document the current module, not modules imported inside the current module
    if hasattr(obj, "__module__"):
        return obj.__module__ == module.__name__

    return True


if __name__ == "__main__":
    main()
