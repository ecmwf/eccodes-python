/*
 * Copyright 2005-2018 ECMWF.
 *
 * This software is licensed under the terms of the Apache Licence Version 2.0
 * which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
 *
 * In applying this licence, ECMWF does not waive the privileges and immunities granted to it by
 * virtue of its status as an intergovernmental organisation nor does it submit to any jurisdiction.
 */

/*! Codes handle,   structure giving access to parsed values by keys
    \ingroup codes_handle
    \struct codes_handle
*/
typedef struct grib_handle            codes_handle;

/*! Codes context,  structure containing the memory methods, the parsers and the formats.
    \ingroup codes_context
    \struct codes_context
*/
typedef struct grib_context           codes_context;

/**
*  Create a handle from a file resource.
*  The file is read until a message is found. The message is then copied.
*  Remember always to delete the handle when it is not needed anymore to avoid
*  memory leaks.
*
* @param c           : the context from which the handle will be created (NULL for default context)
* @param f           : the file resource
* @param product     : the kind of product e.g. PRODUCT_GRIB, PRODUCT_BUFR
* @param error       : error code set if the returned handle is NULL and the end of file is not reached
* @return            the new handle, NULL if the resource is invalid or a problem is encountered
*/
grib_handle* codes_handle_new_from_file(grib_context* c, FILE* f, ProductKind product, int* error);

/**
 *  Create a handle from a BUFR message contained in a samples directory.
 *  The message is copied at the creation of the handle
 *
 * @param c           : the context from which the handle will be created (NULL for default context)
 * @param sample_name : the name of the sample file (without the .tmpl extension)
 * @return            the new handle, NULL if the resource is invalid or a problem is encountered
 */
codes_handle* codes_bufr_handle_new_from_samples (codes_context* c, const char* sample_name);

/* codes_bufr_copy_data copies all the values in the data section that are present in the same position in the data tree
 * and with the same number of values to the output handle. Should not exit with error if the output handle has a different
 * structure as the aim is to copy what is possible to be copied.
 * This will allow the user to add something to a message by creating a new message with additions or changes to the
 * unexpandedDescriptors and copying what is possible to copy from the original message. */
int codes_bufr_copy_data(grib_handle* hin, grib_handle* hout);

void codes_bufr_multi_element_constant_arrays_on(codes_context* c);
void codes_bufr_multi_element_constant_arrays_off(codes_context* c);
int codes_bufr_extract_headers_malloc(grib_context* c, const char* filename, codes_bufr_header** result, int* num_messages);
