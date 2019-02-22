/*
 * Copyright 2005-2018 ECMWF.
 *
 * This software is licensed under the terms of the Apache Licence Version 2.0
 * which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
 *
 * In applying this licence, ECMWF does not waive the privileges and immunities granted to it by
 * virtue of its status as an intergovernmental organisation nor does it submit to any jurisdiction.
 */

/*! \file grib_api.h
  \brief grib_api C header file

*/

/*! Grib handle,   structure giving access to parsed message values by keys
    \ingroup grib_handle
*/
typedef struct grib_handle    grib_handle;

/*! Grib context,  structure containing the memory methods, the parsers and the formats.
    \ingroup grib_context
*/
typedef struct grib_context   grib_context;

/**
 *  Create a handle from a GRIB message contained in the samples directory.
 *  The message is copied at the creation of the handle
 *
 * @param c           : the context from which the handle will be created (NULL for default context)
 * @param sample_name : the name of the sample file (without the .tmpl extension)
 * @return            the new handle, NULL if the resource is invalid or a problem is encountered
 */
grib_handle* grib_handle_new_from_samples (grib_context* c, const char* sample_name);

/**
*  Frees a handle, also frees the message if it is not a user message
*  @see  grib_handle_new_from_message
* @param h           : The handle to be deleted
* @return            0 if OK, integer value on error
*/
int   grib_handle_delete   (grib_handle* h);

/*! @} */

/*! \defgroup handling_coded_messages Handling coded messages */
/*! @{ */
/**
* getting the message attached to a handle
*
* @param h              : the handle to which the buffer should be gathered
* @param message        : the pointer to be set to the handle's data
* @param message_length : On exit, the message size in number of bytes
* @return            0 if OK, integer value on error
*/
int grib_get_message(grib_handle* h ,const void** message, size_t *message_length);

/**
*  Set a long value from a key. If several keys of the same name are present, the last one is set
*  @see  grib_get_long
*
* @param h           : the handle to set the data to
* @param key         : the key to be searched
* @param val         : a long where the data will be read
* @return            0 if OK, integer value on error
*/
int grib_set_long         (grib_handle* h, const char*  key , long val);

/**
*  Set a string value from a key. If several keys of the same name are present, the last one is set
*  @see  grib_get_string
*
* @param h           : the handle to set the data to
* @param key         : the key to be searched
* @param mesg       : the address of a string where the data will be read
* @param length      : the address of a size_t that contains the length of the string on input, and that contains the actual packed length of the string on output
* @return            0 if OK, integer value on error
*/
int grib_set_string       (grib_handle* h, const char*  key , const char* mesg, size_t *length);

/**
*  Set a double array from a key. If several keys of the same name are present, the last one is set
*   @see  grib_get_double_array
*
* @param h           : the handle to set the data to
* @param key         : the key to be searched
* @param vals        : the address of a double array where the data will be read
* @param length      : a size_t that contains the length of the byte array on input
* @return            0 if OK, integer value on error
*/
int grib_set_double_array (grib_handle* h, const char*  key , const double*        vals   , size_t length);

/**
*  Get the API version
*
*  @return        API version
*/
long grib_get_api_version(void);

