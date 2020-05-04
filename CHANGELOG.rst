
Changelog for eccodes-python
============================

0.9.8 (2020-MM-DD)
-------------------

- ECC-1108: Python3 bindings under Windows: use of handle causes crash
- Provide missing argument to exceptions
- Fix grib_get_double_element(). Missing last argument
- Removed obsolete function codes_close_file()
- Add more tests to increase coverage


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
