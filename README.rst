.. image:: https://img.shields.io/pypi/v/eccodes.svg
   :target: https://pypi.python.org/pypi/eccodes/

Python 3 interface to decode and encode GRIB and BUFR files via the
`ECMWF ecCodes library <https://confluence.ecmwf.int/display/ECC/>`_.

Features:

- reads and writes GRIB 1 and 2 files,
- reads and writes BUFR 3 and 4 files,
- supports all modern versions of Python 3.11, 3.10, 3.9, 3.8 and PyPy3,
- works on most *Linux* distributions and *MacOS*, the *ecCodes* C-library
  is the only system dependency,
- PyPI package can be installed without compiling,
  at the cost of being twice as slow as the original *ecCodes* module,
- an optional compile step makes the code as fast as the original module
  but it needs the recommended (the most up-to-date) version of *ecCodes*.

Limitations:

- Microsoft Windows support is untested.


Installation
============

The package is installed from PyPI with::

    $ pip install eccodes


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
https://confluence.ecmwf.int/display/ECC/ecCodes+installation

You may run a simple selfcheck command to ensure that your system is set up correctly::

    $ python -m eccodes selfcheck
    Found: ecCodes v2.27.0.
    Your system is ready.


Usage
-----

Refer to the *ecCodes* `documentation pages <https://confluence.ecmwf.int/display/ECC/Documentation>`_
for usage.


Experimental features
=====================

Fast bindings
-------------

To test the much faster *CFFI* API level, out-of-line mode you need the
*ecCodes* header files.
Then you need to clone the repo in the same folder as your *ecCodes*
source tree, make a ``pip`` development install and custom compile
the binary bindings::

    $ git clone https://github.com/ecmwf/eccodes-python
    $ cd eccodes-python
    $ pip install -e .
    $ python builder.py

To revert back to ABI level, in-line mode just remove the compiled bindings::

    $ rm gribapi/_bindings.*


Project resources
=================

============= =========================================================
Development   https://github.com/ecmwf/eccodes-python
Download      https://pypi.org/project/eccodes
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

.. |copy|   unicode:: U+000A9 .. COPYRIGHT SIGN

License
=======

|copy| Copyright 2017- ECMWF.

This software is licensed under the terms of the Apache Licence Version 2.0
which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

In applying this licence, ECMWF does not waive the privileges and immunities
granted to it by virtue of its status as an intergovernmental organisation nor
does it submit to any jurisdiction.
