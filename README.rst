
Python 3 interface to encode and decode GRIB and BUFR files via the
`ECMWF ecCodes library <https://software.ecmwf.int/wiki/display/ECC/>`_.

Features with development status **Beta**:

- reads and writes GRIB 1 and 2 files,
- reads and writes BUFR 3 and 4 files,
- supports all modern versions of Python 3.7, 3.6, 3.5 and PyPy3,
- works on most *Linux* distributions and *MacOS*, the *ecCodes* C-library is the only system dependency,
- PyPI package with no install time build (binds with *CFFI* ABI level, in-line mode),
- supports writing the index of a GRIB file to disk, to save a full-file scan on open.

Limitations:

- *CFFI* ABI level, in-line mode is almost twice as slow as the original *ecCodes* bindings,
- only experimental support for the much faster *CFFI* API level, out-of-line mode,
- *PyPI* binary packages do not include *ecCodes*,
- incomplete documentation, for now,
- no Windows support, for now.


Installation
============

The package is installed from PyPI with::

    $ pip install eccodes-python


System dependencies
-------------------

The Python module depends on the ECMWF *ecCodes* library
that must be installed on the system and accessible as a shared library.
Some Linux distributions ship a binary version that may be installed with the standard package manager.
On Ubuntu 18.04 use the command::

    $ sudo apt-get install libeccodes0

On a MacOS with HomeBrew use::

    $ brew install eccodes

Or if you manage binary packages with *Conda* use::

    $ conda install -c conda-forge eccodes

As an alternative you may install the official source distribution
by following the instructions at
https://software.ecmwf.int/wiki/display/ECC/ecCodes+installation

You may run a simple selfcheck command to ensure that your system is set up correctly::

    $ python -m eccodes selfcheck
    Found: ecCodes v2.7.0.
    Your system is ready.


Usage
=====

First, you need a well-formed GRIB file, if you don't have one at hand you can download our
`ERA5 on pressure levels sample <http://download.ecmwf.int/test-data/cfgrib/era5-levels-members.grib>`_::

    $ wget http://download.ecmwf.int/test-data/cfgrib/era5-levels-members.grib




GRIB index file
---------------

By default *eccodes-python* saves the index of the GRIB file to disk appending ``.idx``
to the GRIB file name.
Index files are an **experimental** and completely optional feature, feel free to
remove them and try again in case of problems. Index files saving can be disable passing
adding ``indexpath=''`` to the keyword argument.


Project resources
=================

============= =========================================================
Development   https://github.com/ecmwf/eccodes-python
Download      https://pypi.org/project/eccodes-python
Code quality  .. image:: https://api.travis-ci.org/ecmwf/eccodes-python.svg?branch=master
                :target: https://travis-ci.org/ecmwf/eccodes-python/branches
                :alt: Build Status on Travis CI
              .. image:: https://coveralls.io/repos/ecmwf/eccodes-python/badge.svg?branch=master&service=github
                :target: https://coveralls.io/github/ecmwf/eccodes-python
                :alt: Coverage Status on Coveralls
============= =========================================================


Contributing
============

The main repository is hosted on GitHub,
testing, bug reports and contributions are highly welcomed and appreciated:

https://github.com/ecmwf/eccodes-python

Please see the CONTRIBUTING.rst document for the best way to help.

Lead developer:

- `Alessandro Amici <https://github.com/alexamici>`_ - `B-Open <https://bopen.eu>`_

See also the list of `contributors <https://github.com/ecmwf/eccodes-python/contributors>`_
who participated in this project.


License
=======

Copyright 2017-2019 European Centre for Medium-Range Weather Forecasts (ECMWF).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0.
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
