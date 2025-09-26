# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# flake8: noqa: F403
# flake8: noqa: F405

import numpy as np
import pytest as pt

from eccodes.highlevel._bufr.helpers import *

# Test RaggedArray


def test_ragged_array_getset():
    a0 = RaggedArray(0)
    assert a0.ndim == 0
    assert a0[None] == 0
    assert a0[()] == 0
    a1 = RaggedArray([0, 1])
    assert a1.ndim == 1
    assert a1[0] == 0
    assert a1[(1,)] == 1
    a1[0] = -0
    a1[(1,)] = -1
    assert a1[0] == -0
    assert a1[(1,)] == -1
    a2 = RaggedArray([[0], [1, 2]])
    assert a2.ndim == 2
    assert a2[(0, 0)] == 0
    assert a2[(1, 0)] == 1
    assert a2[(1, 1)] == 2
    a2[(0, 0)] = -0
    a2[(1, 0)] = -1
    a2[(1, 1)] = -2
    assert a2[(0, 0)] == -0
    assert a2[(1, 0)] == -1
    assert a2[(1, 1)] == -2


def test_ragged_array_insert():
    a0 = RaggedArray.empty(ndim=0)
    assert a0.data is None
    assert a0.ndim == 0
    a0.insert((), 0)
    assert a0[()] == 0
    a1 = RaggedArray.empty(ndim=1)
    assert a1.data == []
    assert a1.ndim == 1
    a1.insert(0, 0)
    a1.insert((1,), 1)
    assert a1.data == [0, 1]
    a2 = RaggedArray.empty(ndim=2)
    assert a2.data == [[]]
    assert a2.ndim == 2
    a2.insert((0, 0), 0)
    assert a2.data == [[0]]
    a2.insert((1, 0), 1)
    a2.insert((1, 1), 2)
    assert a2.data == [[0], [1, 2]]


def test_ragged_array_bool():
    assert not bool(RaggedArray(0))
    assert not bool(RaggedArray([]))
    assert not bool(RaggedArray([[]]))
    assert bool(RaggedArray(1))
    assert bool(RaggedArray([0]))
    assert bool(RaggedArray([[0]]))


# Test get_datetime()


def test_get_datetime_with_no_seconds():
    data = dict(year=2000, month=1, day=2, hour=3, minute=4)
    datetime = get_datetime(data)
    assert not isinstance(datetime, np.ndarray)
    assert datetime == np.datetime64("2000-01-02T03:04")


def test_get_datetime_with_missing_seconds():
    data = dict(year=2000, month=1, day=2, hour=3, minute=4)
    data.update(second=CODES_MISSING_LONG)
    datetime = get_datetime(data)
    assert datetime is np.ma.masked
    data.update(second=np.ma.masked)
    datetime = get_datetime(data)
    assert datetime is np.ma.masked
    data.update(second=[5, CODES_MISSING_LONG])
    datetime = get_datetime(data)
    assert isinstance(datetime, np.ndarray)
    assert datetime.size == 2
    assert datetime[0] == np.datetime64("2000-01-02T03:04:05")
    assert datetime[1] is np.ma.masked
    assert np.ma.all(
        datetime == np.array(["2000-01-02T03:04:05", "NaT"], dtype="M8[s]")
    )


def test_get_datetime_with_decimal_seconds():
    data = dict(year=2000, month=1, day=2, hour=3, minute=4)
    data.update(second=[5.6, CODES_MISSING_DOUBLE])
    datetime = get_datetime(data)
    assert isinstance(datetime, np.ndarray)
    assert datetime.size == 2
    assert datetime[0] == np.datetime64("2000-01-02T03:04:05.6")
    assert datetime[1] is np.ma.masked
    assert np.ma.all(
        datetime == np.array(["2000-01-02T03:04:05.6", "NaT"], dtype="M8[ms]")
    )


def test_get_datetime_with_out_of_range_seconds():
    data = dict(year=2000, month=1, day=2, hour=3, minute=4)
    data.update(second=[5, 60])
    datetime = get_datetime(data)
    assert isinstance(datetime, np.ndarray)
    assert datetime.size == 2
    assert datetime[0] == np.datetime64("2000-01-02T03:04:05")
    assert datetime[1] == np.datetime64("2000-01-02T03:04:59")


def test_get_datetime_with_int32_seconds():
    data = dict(year=2000, month=1, day=2, hour=3, minute=4)
    data.update(second=np.array([5, 6], dtype="int32"))
    datetime = get_datetime(data)
    assert isinstance(datetime, np.ndarray)
    assert datetime.size == 2
    assert datetime[0] == np.datetime64("2000-01-02T03:04:05")
    assert datetime[1] == np.datetime64("2000-01-02T03:04:06")


def test_get_datetime_with_microseconds():
    data = dict(
        year=2000,
        month=1,
        day=2,
        hour=3,
        minute=4,
        secondsWithinAMinuteMicrosecond=5.6789,
    )
    datetime = get_datetime(data)
    assert not isinstance(datetime, np.ndarray)
    assert datetime == numpy.datetime64("2000-01-02T03:04:05.6789")


def test_get_datetime_with_seconds_and_microseconds():
    data = dict(
        year=2000,
        month=1,
        day=2,
        hour=3,
        minute=4,
        second=5,
        secondsWithinAMinuteMicrosecond=5.6789,
    )
    datetime = get_datetime(data)
    assert not isinstance(datetime, np.ndarray)
    assert datetime == numpy.datetime64("2000-01-02T03:04:05.6789")


def test_get_datetime_with_prefix():
    header = dict(rdbtimeDay=2, rdbtimeHour=3, rdbtimeMinute=4, rdbtimeSecond=5)
    with pt.raises(KeyError):
        datetime = get_datetime(header, prefix="rdbtime")
    datetime = get_datetime(header, prefix="rdbtime", year=2000, month=1)
    assert not isinstance(datetime, np.ndarray)
    assert datetime == numpy.datetime64("2000-01-02T03:04:05")


def test_get_datetime_with_rank():
    data = dict(year=[2000, 2001, 2002], month=[1, 2, 3], day=[2, 3, 4])
    data.update(hour=[3, 4, 5], minute=[4, 5, 6], second=[5, 6, 7])
    for name, values in list(data.items()):
        # data.pop(name)
        for rank, value in enumerate(values, 1):
            data[f"#{rank}#{name}"] = value
    # Number
    datetime = get_datetime(data, rank=2)
    assert not isinstance(datetime, np.ndarray)
    assert datetime == np.datetime64("2001-02-03T04:05:06")
    # Slice
    datetime = get_datetime(data, rank=slice(2, None))
    assert isinstance(datetime, np.ndarray)
    assert np.all(
        datetime
        == np.array(["2001-02-03T04:05:06", "2002-03-04T05:06:07"], dtype="M8[s]")
    )


# Test missing_of()


def test_missing_of():
    with pt.raises(ValueError):
        missing_of(np.int8)
    with pt.raises(ValueError):
        missing_of(np.int16)
    assert CODES_MISSING_LONG == missing_of(np.int32)
    assert CODES_MISSING_LONG == missing_of(np.int64)
    with pt.raises(ValueError):
        missing_of(np.dtype("i2"))
    with pt.raises(ValueError):
        missing_of(np.dtype("f4"))
    assert CODES_MISSING_LONG == missing_of(np.dtype("i4"))
    assert CODES_MISSING_LONG == missing_of(np.dtype("i8"))
    assert CODES_MISSING_LONG == missing_of(np.array([1]))
    assert CODES_MISSING_LONG == missing_of([1])
    assert CODES_MISSING_LONG == missing_of(1)
    with pt.raises(ValueError):
        missing_of(np.float16)
    with pt.raises(ValueError):
        missing_of(np.float32)
    assert CODES_MISSING_DOUBLE == missing_of(np.float64)
    assert CODES_MISSING_DOUBLE == missing_of(np.dtype("f8"))
    assert CODES_MISSING_DOUBLE == missing_of(np.array([1.0]))
    assert CODES_MISSING_DOUBLE == missing_of([1.0])
    assert CODES_MISSING_DOUBLE == missing_of(1.0)
    assert "" == missing_of(np.dtype("U"))
    assert "" == missing_of(np.array(["one"]))
    assert "" == missing_of(["one"])
    assert "" == missing_of("one")
    assert np.array(CODES_MISSING_LONG, "M8[D]") == missing_of(np.dtype("M8[D]"))
    assert np.array(CODES_MISSING_LONG, "M8[D]") == missing_of(np.array(1, "M8[D]"))
    assert np.array(CODES_MISSING_LONG, "m8[h]") == missing_of(np.dtype("m8[h]"))
    assert np.array(CODES_MISSING_LONG, "m8[h]") == missing_of(np.array(1, "m8[h]"))
