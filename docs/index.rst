

=======
CF-GRIB
=======

:Version: |release|
:Date: |today|


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


.. toctree::
    :maxdepth: 2
    :caption: Table of Contents

    messages
