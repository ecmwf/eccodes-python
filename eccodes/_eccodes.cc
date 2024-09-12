/*
 * (C) Copyright 2024- ECMWF.
 *
 * This software is licensed under the terms of the Apache Licence Version 2.0
 * which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
 *
 * In applying this licence, ECMWF does not waive the privileges and immunities granted to it by
 * virtue of its status as an intergovernmental organisation nor does it submit to any jurisdiction.
 */

#include <stdio.h>
#include <Python.h>

#include <eccodes.h>

static PyObject *versions(PyObject *self, PyObject *args)
{
    long s = grib_get_api_version(); // Force linking

    return Py_BuildValue("{s:s}",
                         "eccodes", ECCODES_VERSION_STR);
}

static PyMethodDef eccodes_methods[] = {
    {
        "versions",
        versions,
        METH_NOARGS,
        "Versions",
    },
    {
        0,
    }};

static struct PyModuleDef eccodes_definition = {
    PyModuleDef_HEAD_INIT,
    "eccodes",
    "Load ecCodes library.",
    -1,
    eccodes_methods};

PyMODINIT_FUNC PyInit__eccodes(void)
{
    Py_Initialize();
    return PyModule_Create(&eccodes_definition);
}
