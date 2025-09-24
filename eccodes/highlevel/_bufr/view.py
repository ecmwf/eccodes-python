# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# flake8: noqa: 405

from .common import *
from .helpers import get_datetime, set_datetime


class View:
    """A base class with some common methods: getters, setters, etc."""

    def __contains__(self, key: str) -> bool:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    def __getitem__(self, subscript):
        raise NotImplementedError

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __setitem__(self, key: str, value) -> None:
        raise NotImplementedError

    def get_count(self, key: str) -> int:
        raise NotImplementedError

    def as_dict(self, ranked=False, depth=0, **kwds) -> Dict:
        raise NotImplementedError

    def get(self, key: str, default: Optional[ValueLike] = None) -> Optional[ValueLike]:
        """Returns value of `key`. If `key` is not defined, returns `default`.

        Note this method doesn't raise exception.
        """
        try:
            value = self[key]
        except NotFoundError:
            value = default
        return value

    def get_datetime(
        self,
        rank: Optional[Union[int, slice]] = None,
        prefix: str = "",
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> NDArray:
        """
        Returns an array of type `datetime64` derived from datetime-related keys/values.

        The keys used are: 'year', 'month', 'day', 'hour', 'minute' and 'second'. If
        'second' is not present then the key 'secondsWithinAMinuteMicrosecond' is
        tried instead. The presence of keys 'second' and 'seconds...Microsecond' is
        optional.

        If `prefix` is specified, the datetime is derived from keys '{prefix}Year',
        '{prefix}Month', etc.

        Optionally, the year and the month can be overwritten/forced to a specific value.
        This can be useful, for instance, if there is no dedicated year or month key.
        For example, ECMWF's section 2 defines 'rdbtimeDay', 'rdbtimeHour', etc.,
        but not 'rdbtimeYear' or 'rdbtimeMonth'.
        """
        return get_datetime(self, rank, prefix, year, month)

    def items(self, ranked=False, **kwds) -> Iterator[Tuple[str, ValueLike]]:
        raise NotImplementedError

    def keys(self, ranked=False, **kwds) -> Iterator[str]:
        raise NotImplementedError

    def set(self, key: str, value: ValueLike) -> None:
        raise NotImplementedError

    def set_datetime(
        self,
        value: Union[DateLike, np.ndarray],
        rank: Optional[int] = None,
        prefix: str = "",
    ) -> None:
        """
        Sets datetime-related keys (i.e., 'year', 'month', etc.).

        If `prefix` is specified, use the keys '{prefix}Year', '{prefix}Month', etc.
        """
        set_datetime(self, value, rank, prefix)

    def update(self, *args, **kwargs) -> None:
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, View):
                for key, value in arg.items(skip="read_only"):
                    self[key] = value
            if isinstance(arg, abc.Mapping):
                for key, value in arg.items():
                    self[key] = value
            elif isinstance(arg, abc.Iterable):
                for key, value in arg:
                    self[key] = value
            else:
                raise TypeError(
                    "Expected a mapping or an iterable of key-value pairs; got %s"
                    % type(arg)
                )
        elif len(args) > 1:
            raise ValueError("Expected 1 positional argument; got %d" % len(args))
        else:
            self.update(kwargs)
