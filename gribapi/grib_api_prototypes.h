
/* grib_handle.c */
grib_handle *grib_new_from_file(grib_context *c, FILE *f, int headers_only, int *error);
grib_handle *gts_new_from_file(grib_context *c, FILE *f, int *error);
grib_handle *metar_new_from_file(grib_context *c, FILE *f, int *error);

