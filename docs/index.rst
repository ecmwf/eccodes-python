

=======
CF-GRIB
=======

:Version: |release|
:Date: |today|


Python interface to access and decode GRIB files via the
`ECMWF ecCodes library <https://software.ecmwf.int/wiki/display/ECC/>`_.

Features with development status **Pre-alpha**:

- reads and writes GRIB 1 and 2 files,
- supports all modern versions of Python 3.7, 3.6, 3.5 and 2.7, plus PyPy and PyPy3,
- works on most *Linux* distributions and *MacOS*, the *ecCodes* C-library is the only system dependency,
- PyPI package with no install time build (binds with *CFFI* ABI mode),
- supports writing the index of a GRIB file to disk, to save a full-file scan on open.

Limitations:

- *PyPI* binary packages do not include *ecCodes*,
- incomplete documentation, for now,
- no Windows support, for now.


.. toctree::
    :maxdepth: 2
    :caption: Table of Contents

    messages
