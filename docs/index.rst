

=======
CF-GRIB
=======

:Version: |release|
:Date: |today|


Python 3 interface to encode and decode GRIB and BUFR files via the
`ECMWF ecCodes library <https://confluence.ecmwf.int/display/ECC/>`_.

Features:

- reads and writes GRIB 1 and 2 files,
- reads and writes BUFR 3 and 4 files,
- supports all modern versions of Python 3.8, 3.7, 3.6, 3.5 and PyPy3,
- works on most *Linux* distributions and *MacOS*, the *ecCodes* C-library is the only system dependency,
- PyPI package can be installed without compiling,
  at the cost of being twice as slow as the original *ecCodes* module,
- an optional compile step makes the code as fast as the original module
  but it needs the recommended (the most up-to-date) version of *ecCodes*.

Limitations:

- Microsoft Windows support is untested.


.. toctree::
    :maxdepth: 2
    :caption: Table of Contents

