# Testing

It will be shortly described how the source code testing is done in Midgard. `pytest` is used by Midgard for testing the library modules. 

All module tests of Midgard are located in directory **./midgard/tests**. The **tests** directory mirrors the official directory structure under **./midgard/midgard**. For example the test for the modul **./midgard/midgard/math/interpolation.py** can be found under **./midgard/tests/math/test_interpolation.py**. In Midgard the test files follow the naming convention **test_<module name\>.py** (e.g. **test_interpolation.py**). Information about how to write `pytest` tests can be found under <https://pytest.org/>. 

The written test can be excecuted as follows:

* All Midgard tests can be excecuted by calling `make test` in main directory **./midgard**.
* If no arguments are specified `pytest` searches recursively after `test_*.py` files starting from the current directory.
* A single modul test can be carried out for example by `pytest tests/ionosphere/test_klobuchar.py`.

An overview over passed and failed tests are given after excecuting `pytest`.
