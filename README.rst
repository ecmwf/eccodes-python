
Python 3 interface to encode and decode GRIB and BUFR files via the
`ECMWF ecCodes library <https://software.ecmwf.int/wiki/display/ECC/>`_.

Features:

- reads and writes GRIB 1 and 2 files,
- reads and writes BUFR 3 and 4 files,
- supports all modern versions of Python 3.7, 3.6, 3.5 and PyPy3,
- works on most *Linux* distributions and *MacOS*, the *ecCodes* C-library is the only system dependency,
- PyPI package can be installed without compiling,
  at the cost of being twice as slow as the original *ecCodes* module,
- an optional compile step makes the code as fast as the original module
  but it needs a recent version of *ecCodes* `>= 2.17.0`.

Limitations:

- Microsoft Windows support is untested.


Installation
============

The package is installed from PyPI with::

    $ pip install eccodes-python


System dependencies
-------------------

The Python module depends on the ECMWF *ecCodes* library
that must be installed on the system and accessible as a shared library.

On a MacOS with HomeBrew use::

    $ brew install eccodes

Or if you manage binary packages with *Conda* use::

    $ conda install -c conda-forge eccodes

As an alternative you may install the official source distribution
by following the instructions at
https://software.ecmwf.int/wiki/display/ECC/ecCodes+installation

You may run a simple selfcheck command to ensure that your system is set up correctly::

    $ python -m eccodes selfcheck
    Found: ecCodes v2.17.0.
    Your system is ready.


Usage
-----

Refer to the *ecCodes* `documentation pages <https://confluence.ecmwf.int/display/ECC/Documentation>`_
for usage.


Experimental features
=====================

Fast bindings
-------------

To test the much faster *CFFI* API level, out-of-line mode you need the *ecCodes*
header files.
Then you need to clone the repo in the same folder as your *ecCodes* source tree,
make a ``pip`` development install and custom compile the binary bindings::

    $ git clone https://github.com/ecmwf/eccodes-python
    $ cd eccodes-python
    $ pip install -e .
    $ python builder.py

To revert back to ABI level, in-line more just remove the compiled bindings::

    $ rm gribapi/_bindings.*


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

Maintainer:

- `Shahram Najm <https://github.com/shahramn>`_ - `ECMWF <https://ecmwf.int>`_

Contributors:

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
