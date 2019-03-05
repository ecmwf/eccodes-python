
/* grib_handle.c */
grib_handle *grib_new_from_file(grib_context *c, FILE *f, int headers_only, int *error);
grib_handle *gts_new_from_file(grib_context *c, FILE *f, int *error);
grib_handle *metar_new_from_file(grib_context *c, FILE *f, int *error);

int parse_keyval_string(const char *grib_tool, char *arg, int values_required, int default_type, grib_values values[], int *count);
