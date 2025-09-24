# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# flake8: noqa: 405

from .common import *


class RaggedArray:
    @staticmethod
    def empty(ndim=1):
        if ndim > 0:
            data = []
            for _ in range(ndim - 1):
                data = [data]
        else:
            data = None
        return RaggedArray(data, ndim)

    def __init__(self, data, ndim=None):
        self.data = data
        if ndim is None:
            self.ndim = 0
            while True:
                try:
                    data = data[0]
                except (IndexError, TypeError):
                    break
                else:
                    self.ndim += 1
        else:
            self.ndim = ndim

    def __repr__(self):
        return f"RaggedArray({self.data})"

    def __getitem__(self, index):
        try:
            value = self.data[index[0]]
        except (IndexError, TypeError):
            try:
                value = self.data[index]
            except TypeError:
                if index in ((), None):
                    value = self.data
                else:
                    raise IndexError(f"{index}")
        else:
            for i in range(1, len(index)):
                value = value[index[i]]
        return value

    def __setitem__(self, index, value):
        data = self.data
        try:
            for i in range(0, len(index) - 1):
                data = data[index[i]]
        except (IndexError, TypeError):
            try:
                self.data[index] = value
            except TypeError:
                if index in ((), None):
                    self.data = value
                else:
                    raise IndexError(f"{index}")
        else:
            data[index[-1]] = value

    def __bool__(self):
        if isinstance(self.data, list):

            def recurse(data):
                if not isinstance(data, list):
                    return True
                elif len(data) == 0:
                    return False
                elif len(data) > 1:
                    return True
                else:
                    return recurse(data[0])

            return recurse(self.data)
        else:
            return bool(self.data)

    def insert(self, index, value):
        data = self.data
        try:
            for i in range(0, len(index) - 1):
                data = data[index[i]]
            data.insert(index[-1], value)
        except (IndexError, TypeError, AttributeError):
            try:
                data.insert(index, value)
            except (IndexError, TypeError):
                if index[i] == len(data):
                    data.append([])
                    data = data[index[i]]
                    data.insert(index[-1], value)
                else:
                    raise IndexError(f"{index}")
            except AttributeError:
                if index in ((), None):
                    self.data = value
                else:
                    raise IndexError(f"{index}")


class SingletonDict:  # TODO: UserDict?
    """A dict which returns the same value, no matter the key.

    This is a helper class to optimize storage of key counts in leaf nodes
    where the counts remain the same for every replication. By using this class
    instead of the build-in dict, we save space without having to special-case
    access to the leaf nodes' counts in the rest of the code.
    """

    def __init__(self):
        self._has_value = False

    def __getitem__(self, key):
        if self._has_value:
            return self._value
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        # TODO: allow to set/update value only once
        self._value = value
        self._has_value = True


def get_datetime(
    view: Union["View", abc.Mapping],
    rank: Optional[Union[int, slice]] = None,
    prefix: str = "",
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> NDArray:
    """
    Returns an array of type `datetime64` derived from datetime-related keys/values.
    """
    date = get_date(view, rank, prefix, year, month)
    time = get_time(view, rank, prefix)
    if date is np.ma.masked or time is np.ma.masked:
        datetime = np.ma.masked
    else:
        datetime = date + time
    return datetime


def get_date(
    view: Union["View", abc.Mapping],
    rank: Optional[Union[int, slice]] = None,
    prefix: str = "",
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> NDArray:
    """
    Returns a `datetime64` array derived from date-related keys/values.
    """
    names = ("year", "month", "day")
    values = (year, month, None)
    dtypes = ("M8[Y]", "m8[M]", "m8[D]")
    offsets = (1970, 1, 1)
    parts = []
    for name, value, dtype, offset in zip(names, values, dtypes, offsets):
        if prefix:
            name = name.capitalize()
        key = Key(prefix + name, rank if isinstance(rank, int) else None)
        value = view[key.string] if value is None else value
        part = ensure_masked_value(value, dtype)
        parts.append(part - offset)
    for i, part in enumerate(parts):
        if part is np.ma.masked:
            date = np.ma.masked
            break
        if isinstance(rank, slice):
            slice_ = decrement(rank)
            parts[i] = part[slice_]
    else:
        date = sum(parts)
    return date


def get_time(
    view: Union["View", abc.Mapping],
    rank: Optional[Union[int, slice]] = None,
    prefix: str = "",
) -> NDArray:
    """
    Returns a `timedelta64` array derived from time-related keys/values.
    """
    names = ("hour", "minute", "second")
    dtypes = ("m8[h]", "m8[m]", "m8[s]")
    has_seconds = True
    parts = []
    for name, dtype in zip(names, dtypes):
        if prefix:
            name = name.capitalize()
        key = Key(prefix + name, rank if isinstance(rank, int) else None)
        try:
            value = view[key.string]
        except (NotFoundError, KeyError) as error:
            if name in ("second", "Second"):
                has_seconds = False
                break
            else:
                raise error
        if name == "second":
            if value is np.ma.masked:
                part = value
            else:
                array = ensure_masked_array(value)
                if array.dtype == np.dtype("f8"):
                    dtype = "m8[ms]"
                    array.fill_value = missing_of(int)
                    array.data[array.mask] = array.fill_value
                    array = (array * 1000).astype(dtype)
                    array.fill_value = np.array("NaT", dtype)
                elif array.dtype == np.dtype("i8"):
                    array = array.view(dtype)
                else:
                    array = cast(MaskedArray, array.astype(dtype))
                if array.dtype == np.dtype("m8[s]"):
                    max_value = np.array(60 - 1, array.dtype)
                elif array.dtype == np.dtype("m8[ms]"):
                    max_value = np.array(60 * 1000 - 1, array.dtype)
                else:
                    assert False
                array[:] = np.ma.where(array > max_value, max_value, array)
                if isinstance(value, abc.Iterable):
                    part = array
                else:
                    part = array[0]
        else:
            part = ensure_masked_value(value, dtype)
        parts.append(part)
    if not prefix:
        key = Key(
            "secondsWithinAMinuteMicrosecond", rank if isinstance(rank, int) else None
        )
        try:
            value = view[key.string]
        except (NotFoundError, KeyError):
            pass
        else:
            array = ensure_masked_array(value)
            useconds = np.ma.empty(array.shape, dtype="m8[us]")
            useconds.fill_value = np.array("NaT", dtype="m8[us]")
            useconds[:] = array * 1000000
            max_useconds = np.array(60 * 1000000 - 1, dtype="m8[us]")  # [1]
            useconds[:] = np.ma.where(useconds > max_useconds, max_useconds, useconds)
            if isinstance(value, abc.Iterable):
                part = useconds
            else:
                part = useconds[0]
            if has_seconds:
                parts.pop()  # [2]
            parts.append(part)
    for i, part in enumerate(parts):
        if part is np.ma.masked:
            time = np.ma.masked
            break
        if isinstance(rank, slice):
            slice_ = decrement(rank)
            parts[i] = part[slice_]
    else:
        time = sum(parts)
    return time

    # [1] Note that 'seconds...Microsecond' is a floating-point number where the
    #     whole part is seconds and the decimal part is microseconds.
    #
    # [2] Because of [1], if the message contains both keys, the 'second' and the
    #    'seconds...Microsecond', use the latter. (Yes, such messages do exist!)


def set_datetime(
    view: Union["View", abc.MutableMapping],
    value: Union[DateLike, np.ndarray],
    rank: Optional[int] = None,
    prefix: str = "",
) -> None:
    set_date(view, value, rank, prefix)
    set_time(view, value, rank, prefix)


def set_date(
    view: Union["View", abc.MutableMapping],
    value: Union[DateLike, np.ndarray],
    rank: Optional[int] = None,
    prefix: str = "",
) -> None:
    names = ["year", "month", "day"]
    keys = []
    for i, name in enumerate(names):
        if prefix:
            name = prefix + name.capitalize()
        keys.append(Key(name, rank).string)
    year, month, day = keys
    if isinstance(value, np.ndarray):
        view[year] = value.astype("M8[Y]").astype(int) + 1970
        view[month] = value.astype("M8[M]").astype(int) % 12 + 1
        view[day] = (value.astype("M8[D]") - value.astype("M8[M]")).astype(int) + 1
    else:
        date = ensure_date(value)
        view[year] = date.year
        view[month] = date.month
        view[day] = date.day


def set_time(
    view: Union["View", abc.MutableMapping],
    value: Union[TimeLike, np.ndarray],
    rank: Optional[int] = None,
    prefix: str = "",
) -> None:
    keys = ["hour", "minute", "second"]
    for i, name in enumerate(keys):
        if prefix:
            name = prefix + name.capitalize()
        keys[i] = Key(name, rank).string
    hour, minute, second = keys
    if isinstance(value, np.ndarray):
        delta = (value - value.astype("M8[D]")).astype("timedelta64[s]").view(int)
        view[hour] = delta // 3600
        view[minute] = (delta % 3600) // 60
        try:
            view[second] = delta % 60
        except (NotFoundError, KeyError):
            pass
    else:
        time = ensure_time(value)
        view[hour] = time.hour
        view[minute] = time.minute
        try:
            view[second] = time.second
        except (NotFoundError, KeyError):
            pass


def ensure_date(value: DateLike) -> dt.date:
    """Takes a date-like value and converts it to `dt.date`."""
    date: dt.date
    if isinstance(value, dt.date):
        date = value
    elif isinstance(value, dt.datetime):
        date = value.date()
    elif isinstance(value, np.datetime64):
        date = value.astype("M8[D]").item()
    elif isinstance(value, str):
        try:
            date = dt.datetime.fromisoformat(value).date()
        except ValueError:
            try:
                date = dt.datetime.strptime(value, "%Y%m%d").date()
            except ValueError:
                raise ValueError(f"Cannot convert string '{value}' to `dt.date`")
    else:
        raise TypeError("Cannot convert value of type `%s` to `dt.time`" % type(value))
    return date


def ensure_time(value: TimeLike) -> dt.time:
    """Takes a time-like value and converts it to `dt.time`."""
    if isinstance(value, dt.time):
        time = value
    elif isinstance(value, dt.datetime):
        time = value.time()
    elif isinstance(value, dt.timedelta):
        time = (dt.datetime.min + value).time()
    elif isinstance(value, np.datetime64):
        time = value.astype("M8[s]").item().time()
    elif isinstance(value, np.timedelta64):
        total_seconds = value.astype("m8[s]").astype(int)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        time = dt.time(hours, minutes, seconds)
    elif isinstance(value, str):
        for format in ["%H:%M:%S", "%H:%M", "%H%M%S", "%H%M"]:
            try:
                time = dt.datetime.strptime(value, format).time()
            except ValueError:
                continue
            else:
                break
        else:
            raise ValueError(f"Cannot convert string '{value}' to `dt.time`")
    else:
        raise TypeError("Cannot convert value of type `%s` to `dt.time`" % type(value))
    return time


def ensure_array(
    value: Any, dtype: Optional[DTypeLike] = None
) -> Union[NDArray, MaskedArray]:
    """Takes a value and converts it to `np.ndarray`."""
    if isinstance(value, np.ndarray):
        array = value
        if dtype:
            dtype = np.dtype(dtype)
            if dtype.type in (np.datetime64, np.timedelta64):
                if array.dtype.type == np.int64:
                    array = array.view(dtype)
                else:
                    array = array.astype(dtype)
            else:
                array = array.astype(dtype, copy=False)
    elif isinstance(value, abc.Iterable):
        if isinstance(value, str):
            array = np.array([value], dtype=dtype)
        else:
            array = np.array(value, dtype=dtype)
    else:
        array = np.array([value], dtype=dtype)
    return array


def ensure_masked_value(value: Any, dtype: Optional[DTypeLike]) -> MaskedArray:
    if value is np.ma.masked:
        return value
    else:
        array = ensure_masked_array(value, dtype)
        if isinstance(value, abc.Iterable):
            return array
        else:
            assert array.size == 1
            return array[0]


def ensure_masked_array(value: Any, dtype: Optional[DTypeLike] = None) -> MaskedArray:
    """Takes a value and converts it to `np.ma.MaskedArray`."""
    array = ensure_array(value, dtype)
    if isinstance(value, np.ma.core.MaskedConstant):
        masked_array = cast(np.ma.MaskedArray, array.ravel())  # [1]
    elif isinstance(array, np.ma.MaskedArray):
        masked_array = array
    else:
        try:
            missing = missing_of(array.dtype)
        except ValueError:
            masked_array = np.ma.array(array, mask=False, copy=False)  # [2]
        else:
            masked_array = np.ma.masked_equal(array, missing, copy=False)
    if dtype and np.dtype(dtype).type in (np.datetime64, np.timedelta64):
        masked_array.fill_value = np.array("NaT", dtype)
    return masked_array

    # [1] We are converting MaskedConstant (i.e., np.ma.masked) into 1d array
    #     so that we can do a slice assignment. This reduces number of code paths
    #     later on.
    #
    # [2] Assume no masked values for non-native types which cannot accomodate
    #     missing values, such as int16, float32, etc..


def decrement(value: Union[int, range, slice]) -> Union[int, range, slice]:
    """Decrements a value by one."""
    if isinstance(value, int):
        value -= 1
    elif isinstance(value, range):
        value = range(value.start - 1, value.stop - 1, value.step)
    elif isinstance(value, slice):
        start = None if value.start is None else value.start - 1
        stop = None if value.stop is None else value.stop - 1
        value = slice(start, stop, value.step)
    else:
        raise TypeError("Cannot decrement value of type `%s`" % type(value))
    return value


def flatten(items):
    """Flattens arbitrarily nested sequences.
    Examples:
        >>> list(flatten([1, (2, (3, 4), [[5]])]))
        [1, 2, 3, 4, 5]
        >>> list(flatten(1))
        [1]
    """
    try:
        for outer in items:
            try:
                for inner in flatten(outer):
                    yield inner
            except TypeError:
                yield outer
    except TypeError:
        yield items


MISSING_OF = {
    str: "",
    int: CODES_MISSING_LONG,
    float: CODES_MISSING_DOUBLE,
    np.int32: CODES_MISSING_LONG,
    np.int64: CODES_MISSING_LONG,
    np.float64: CODES_MISSING_DOUBLE,
    np.dtype("i4"): CODES_MISSING_LONG,
    np.dtype("i8"): CODES_MISSING_LONG,
    np.dtype("f8"): CODES_MISSING_DOUBLE,
}


def missing_of(obj: Any) -> Union[int, float, str]:
    """Returns corresponding missing value for the given object or type."""
    try:
        missing = MISSING_OF[obj]
    except (KeyError, TypeError):
        if isinstance(obj, np.ndarray):
            try:
                missing = missing_of(obj.dtype)
            except KeyError:
                missing = None
        elif isinstance(obj, np.dtype):
            if obj.type == np.str_:
                missing = ""
            elif obj.type in (np.datetime64, np.timedelta64):
                missing = np.array(CODES_MISSING_LONG, dtype=obj)
            else:
                missing = None
        elif hasattr(obj, "__iter__") and len(obj) > 0:
            missing = missing_of(type(obj[0]))
        elif not isinstance(obj, type):
            missing = missing_of(type(obj))
        else:
            missing = None
    if missing is None:
        raise ValueError("Object %s has no corresponding missing value" % obj)
    return missing
