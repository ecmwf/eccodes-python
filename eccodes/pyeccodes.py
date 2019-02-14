#
# Copyright 2017-2019 European Centre for Medium-Range Weather Forecasts (ECMWF).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors:
#   Alessandro Amici - B-Open - https://bopen.eu
#

from __future__ import absolute_import, division, print_function, unicode_literals

import functools
import inspect

from . import bindings


def _encode(obj, encoding='ascii'):
    if isinstance(obj, str):
        return obj.encode(encoding=encoding)
    elif isinstance(obj, tuple):
        return tuple(_encode(item, encoding=encoding) for item in obj)
    elif isinstance(obj, list):
        return [_encode(item, encoding=encoding) for item in obj]
    elif isinstance(obj, dict):
        return {key: _encode(value, encoding=encoding) for key, value in obj.items()}
    return obj


def _decode(obj, encoding='ascii'):
    if isinstance(obj, bytes):
        return obj.decode(encoding=encoding)
    elif isinstance(obj, tuple):
        return tuple(_encode(item, encoding=encoding) for item in obj)
    elif isinstance(obj, list):
        return [_encode(item, encoding=encoding) for item in obj]
    elif isinstance(obj, dict):
        return {key: _encode(value, encoding=encoding) for key, value in obj.items()}
    return obj


def _str_to_bytes_args(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bargs = _encode(args, bindings.ENC)
        bkwargs = _encode(kwargs, bindings.ENC)
        retval = func(*_encode(bargs), **bkwargs)
        return _decode(retval, bindings.ENC)
    return wrapper


def _fix_args(source_items, target_namespace):
    for name, obj in source_items:
        if (name.startswith('codes_') or name.startswith('grib_')) and callable(obj):
            target_namespace[name] = _str_to_bytes_args(obj)
        elif name.startswith('CODES_') or name.startswith('GRIB_'):
            target_namespace[name] = obj


_fix_args(inspect.getmembers(bindings), globals())


@_str_to_bytes_args
def codes_index_get(indexid, key, ktype=bytes):
    # type: (cffi.FFI.CData, bytes, type) -> list
    if ktype is int:
        result = bindings.codes_index_get_long(indexid, key)  # type: T.List[T.Any]
    elif ktype is float:
        result = bindings.codes_index_get_double(indexid, key)
    elif ktype is bytes:
        result = bindings.codes_index_get_string(indexid, key)
    else:
        raise TypeError("ktype not supported %r" % ktype)
    return result


@_str_to_bytes_args
def codes_index_get_autotype(indexid, key):
    # type: (cffi.FFI.CData, bytes) -> list
    try:
        return bindings.codes_index_get_long(indexid, key)
    except bindings.EcCodesError:
        pass
    try:
        return bindings.codes_index_get_double(indexid, key)
    except bindings.EcCodesError:
        return bindings.codes_index_get_string(indexid, key)


@_str_to_bytes_args
def codes_index_select(indexid, key, value):
    # type: (cffi.FFI.CData, bytes, T.Any) -> None
    """
    Select the message subset with key==value.

    :param indexid: id of an index created from a file.
        The index must have been created with the key in argument.
    :param bytes key: key to be selected
    :param bytes value: value of the key to select
    """
    if isinstance(value, int):
        bindings.codes_index_select_long(indexid, key, value)
    elif isinstance(value, float):
        bindings.codes_index_select_double(indexid, key, value)
    elif isinstance(value, bytes):
        bindings.codes_index_select_string(indexid, key, value)
    else:
        raise RuntimeError("Key value not recognised: %r %r (type %r)" % (key, value, type(value)))


@_str_to_bytes_args
def codes_set(handle, key, value):
    """"""
    if isinstance(value, int):
        bindings.codes_set_long(handle, key, value)
    elif isinstance(value, float):
        bindings.codes_set_double(handle, key, value)
    elif isinstance(value, bytes):
        bindings.codes_set_string(handle, key, value)
    else:
        raise TypeError("Unsupported type %r" % type(value))


def codes_grib_new_from_file(fileobj, context=None):
    try:
        return bindings.codes_handle_new_from_file(fileobj, bindings.CODES_PRODUCT_GRIB, context)
    except EOFError:
        return None


def codes_release(handle):
    return bindings.codes_handle_delete(handle)
