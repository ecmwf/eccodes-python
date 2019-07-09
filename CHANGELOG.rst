
Changelog for eccodes-python
============================

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
