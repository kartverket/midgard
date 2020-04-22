# Midgard, the Python Geodesy library

Midgard is a collection of useful Python utilities used by the Geodetic
institute at the Norwegian Mapping Authority (Kartverket). Although some of
these are geodesy-specific, many are also useful in more general settings.

**Note:** Midgard is still in pre-alpha status. Its functionality will change,
  and it should not be depended on in any production-like setting.

[![Latest version](https://img.shields.io/pypi/v/midgard.svg)](https://pypi.org/project/midgard/)
[![Python versions](https://img.shields.io/pypi/pyversions/midgard.svg)](https://pypi.org/project/midgard/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


## Installing Midgard

Midgard is available at [PyPI](https://pypi.org/project/midgard/). You can
install it by simply running

    python -m pip install midgard


## Installing Midgard from source

Midgard depends on several other brilliant Python packages, like for instance
numpy, scipy, etc. We recommend using the Anaconda distribution to ease
the installation of these dependencies.

### Install Anaconda

Go to [www.anaconda.com/download](https://www.anaconda.com/download), and
download Anaconda for Python 3.


### Download the Midgard source code

If you have not already done so, download the Midgard source code from Github:
[github.com/kartverket/midgard](https://github.com/kartverket/midgard). Then
enter the main `midgard` directory before running the install command below.

    cd midgard


### Install dependencies

You should now install the necessary dependencies using the
`environment.yml`-file. You can do this either in your current conda
environment, or choose to create a new `midgard`-environment. In order to use
`midgard` in other projects you need to install `midgard` in the same
environment as those projects.

To install `midgard` in your current environment, do

    conda env update -f environment.yml

To install `midgard` in a new environment named `midgard` and activate it, do

    conda env create -n midgard -f environment.yml
    conda activate midgard


### Install the Midgard package

To do the actual installation of Midgard, use the `flit` packaging tool:

    python -m flit install --dep production

If you want to develop the Midgard package, install it in editable mode using

    python -m flit install -s

On Windows, you can install in editable mode using

    python -m flit install --pth-file


## Using Midgard

Midgard comes organized into different subpackages. To see info about the
different subpackages, use the Python help system:

    >>> import midgard
    >>> help(midgard)

Information about individual subpackages is also available on the
[Midgard website](https://kartverket.github.io/midgard/).
