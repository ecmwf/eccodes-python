
Changelog for eccodes-python
============================

1.6.0 (2023-mm-dd)
--------------------

- ECC-1467: GRIB: Support data values array decoded as "floats" (single-precision) to reduce memory consumption

1.5.2 (2023-04-04)
--------------------

- Add support for Python versions 3.10 and 3.11
- ECC-1555: 2D numpy array incorrectly handled
- ECC-1539: Use the 'warnings' library for selfcheck
- ECC-1538: Add support for CODES_TYPE_BYTES
- ECC-1524: Check values in High-level Message.set function should retrieve based on value type
- ECC-1527: Handle floats in high-level Message.set function check values


1.5.1 (2023-01-25)
--------------------

- ECC-1446: Data file era5-levels-members.grib not included in released tar file
- ECC-1460: Cannot import eccodes on M1 MacBook Pro
- ECC-1505: High-level Message.set function should allow dictionary and check result

1.5.0 (2022-08-25)
--------------------

- ECC-1404: Add the grib_get_gaussian_latitudes() function
- ECC-1405: Add new function: codes_any_new_from_samples
- ECC-1415: Implement a higher-level Python interface (still experimental)
- ECC-1429: Remove the file 'eccodes/messages.py'
- GitHub pull request #62: add pypi badge

1.4.2 (2022-05-20)
--------------------

- ECC-1389: Drop Python version 3.5 and 3.6
- ECC-1390: NameError: name 'GribInternalError' is not defined
- Add test for GRIB bitmap


1.4.1 (2022-03-03)
--------------------

- ECC-1351: Support numpy.int64 in codes_set() and codes_set_long()
- ECC-1317: Data file tiggelam_cnmc_sfc.grib2 not included in released tar file


1.4.0 (2021-12-03)
--------------------

- ECC-1234: Remove the experimental high-level interface
- ECC-1282: Add codes_dump()


1.3.4 (2021-08-27)
--------------------

- Update documentation


1.3.3 (2021-06-21)
--------------------

- ECC-1246: UnicodeDecodeError when parsing BUFR file


1.3.2 (2021-04-16)
--------------------

- Restore the experimental high-level interface


1.3.1 (2021-04-16)
--------------------

- Fix the recommended version


1.3.0 (2021-04-09)
--------------------

- ECC-1231: Remove the experimental high-level interface
- Added the "findlibs" module
- Fix tests/test_high_level_api.py when MEMFS enabled
- ECC-1226: Python3 bindings: Typo causes AttributeError when calling codes_index_get_double


1.2.0 (2021-03-23)
--------------------

- Added test for multi-field GRIBs
- Fix deprecation warning: `np.float` is a deprecated alias for the builtin `float`
- Experimental feature: grib_nearest_find


1.1.0 (2021-01-20)
--------------------

- ECC-1171: Performance: Python bindings: remove assert statements
- ECC-1161: Python3 bindings: Do not raise exception on first failed attempt
- ECC-1176: Python3 bindings: float32 recognised as int instead of float
- GitHub pull request #41: Remove the apparent support for Python 2
- GitHub pull request #44: Fix CFFI crash on windows
- GitHub pull request #42: Add unit testing with GitHub actions (linux, macos and windows)


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
- GitHub pull request #15: Add .__next__() method to eccodes.CodesFile class
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
