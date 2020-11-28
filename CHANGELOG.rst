
Changelog for eccodes-python
============================

1.0.1 (20YY-MM-DD)
--------------------

- ECC-1171: Performance: Python bindings: remove assert statements
- ECC-1161: Python3 bindings: Do not raise exception on first failed attempt
- Remove the apparent support for Python 2 (GitHub pull request #41)
- Fix CFFI crash on windows (GitHub pull request #44)


1.0.0 (2020-10-14)
--------------------

- ECC-1143: CMake: Migration to ecbuild v3.4
- ECC-1133: C API: Propagate const char* for codes_index_new_from_file and codes_index_select_string


0.9.9 (2020-08-04)
-------------------

- Support for ecmwflibs. An additional way to find ECMWF libraries (if available)
- ECC-1140: Segfault from invalid pointer reference in grib_set_double_array()


0.9.8 (2020-06-26)
-------------------

- ECC-1110: Removed obsolete function codes_close_file()
- Provide missing argument to exceptions
- Fix codes_set_definitions_path() typo
- Fix grib_get_double_element(). Missing last argument
- Add more tests to increase coverage
- Add .__next__() method to eccodes.CodesFile class (GitHub pull request #15)
- ECC-1113: Python3 bindings under Windows: codes_get_long_array returns incorrect values
- ECC-1108: Python3 bindings under Windows: use of handle causes crash
- ECC-1121: Segfault when closing GribFile if messages are closed manually


0.9.6 (2020-03-10)
-------------------

- Update Copyright notices
- Function-argument type checks: Improve error message
- Fix C function calls for codes_gribex_mode_on/codes_gribex_mode_off


0.9.5 (2020-01-15)
-------------------

- ECC-1029: Function-argument type-checking should be disabled by default.
            To enable these checks, export ECCODES_PYTHON_ENABLE_TYPE_CHECKS=1
- ECC-1032: Added codes_samples_path() and codes_definition_path()
- ECC-1042: Python3 interface writes integer arrays incorrectly
- ECC-794: Python3 interface: Expose the grib_get_data function


0.9.4 (2019-11-27)
------------------

- Added new function: codes_get_version_info
- ECC-753: Expose the codes_grib_nearest_find_multiple function in Python
- ECC-1007: Python3 interface for eccodes cannot write large arrays


0.9.3 (2019-10-04)
------------------

- New exception added: FunctionalityNotEnabledError
- BUFR decoding: support for multi-element constant arrays (ECC-428)


0.9.2 (2019-07-09)
------------------

- All ecCodes tests now pass
- Simplify the xx_new_from_file calls
- Fix for grib_set_string_array
- Use ECCODES_DIR to locate the library
- Remove the new-style high-level interface. It is still available in
  `cfgrib <https://github.com/ecmwf/cfgrib>`_.

0.9.1 (2019-06-06)
------------------

- ``codes_get_long_array`` and ``codes_get_double_array`` now return a ``np.ndarray``.
  See: `#3 <https://github.com/ecmwf/eccodes-python/issues/3>`_.


0.9.0 (2019-05-07)
------------------

- Declare the project as **Beta**.


0.8.0 (2019-04-08)
------------------

- First public release.
