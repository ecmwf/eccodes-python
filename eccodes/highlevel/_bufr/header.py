# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# flake8: noqa: F405
#   ruff: noqa: F403

from .coder import INPUT_TEMPLATE_KEYS, TEMPLATE_KEYS, Coder
from .common import *
from .helpers import get_date, get_datetime, get_time, set_date, set_datetime, set_time
from .view import View


@dataclass
class Entry:
    name: str = ""
    value: Optional[ValueLike] = None
    dirty: bool = False
    computed: bool = False
    derive: Optional[Callable] = None
    project: Optional[Callable] = None


def derive_datetime(header, key):
    prefix = key.split("DateTime")[0]
    datetime = get_datetime(header, prefix=prefix)
    return datetime


def derive_date(header, key):
    prefix = key.split("Date")[0]
    date = get_date(header, prefix=prefix)
    return date


def derive_time(header, key):
    prefix = key.split("Time")[0]
    time = get_time(header, prefix=prefix)
    return time


def derive_rdbtime_datetime(header, key):
    date = derive_rdbtime_date(header, "rdbtimeDate")
    time = derive_time(header, "rdbtimeTime")
    datetime = date + time
    return datetime


def derive_rdbtime_date(header, key):
    assert key == "rdbtimeDate"
    string = header._coder.get(key, validate=False)
    y, m, d = string[0:4], string[4:6], string[6:8]
    date = np.datetime64(f"{y}-{m}-{d}", "D")
    return date


def project_datetime(header, key, value):
    prefix = key.split("DateTime")[0]
    set_datetime(header, value, prefix=prefix)


def project_date(header, key, value):
    prefix = key.split("Date")[0]
    set_date(header, value, prefix=prefix)


def project_time(header, key, value):
    prefix = key.split("Time")[0]
    set_time(header, value, prefix=prefix)


def project_edition_3_typical_year(header, key, value):
    assert key == "typicalYear"
    assert header["edition"] == 3
    header["typicalCentury"] = value // 100 + 1
    header["typicalYearOfCentury"] = value % 100


COMMON_COMPUTED_KEYS = set(
    [
        "typicalDateTime",
        "typicalDate",
        "typicalTime",
        "localDateTime",
        "localDate",
        "localTime",
        "rdbtimeDateTime",
        "rdbtimeDate",
        "rdbtimeTime",
        "rectimeTime",
        "md5Data",
    ]
)

_COMPUTED_ENTRIES = {
    None: [Entry(key, computed=True) for key in COMMON_COMPUTED_KEYS],
    3: [Entry("typicalYear", computed=True, project=project_edition_3_typical_year)],
    4: [
        Entry("typicalCentury", computed=True),
        Entry("typicalYearOfCentury", computed=True),
    ],
}

COMPUTED_ENTRIES = {}
for edition in _COMPUTED_ENTRIES.keys():
    COMPUTED_ENTRIES[edition] = {
        entry.name: entry for entry in _COMPUTED_ENTRIES[edition]
    }

for key, entry in COMPUTED_ENTRIES[None].items():
    if key == "rdbtimeDateTime":
        entry.derive = derive_rdbtime_datetime
    elif key == "rdbtimeDate":
        entry.derive = derive_rdbtime_date
    elif key.endswith("DateTime"):
        entry.derive = derive_datetime
        entry.project = project_datetime
    elif key.endswith("Date"):
        entry.derive = derive_date
        entry.project = project_date
    elif key.endswith("Time"):
        entry.derive = derive_time
        entry.project = project_time


class Header(View):
    """Provides access to BUFR header entries."""

    _coder: Coder
    _cache: Dict[str, Entry]

    def __init__(self, coder: Coder) -> None:
        self._coder = coder
        edition = cast(int, coder.get("edition", validate=False))
        self._cache = COMPUTED_ENTRIES[None].copy()
        self._cache.update(COMPUTED_ENTRIES[edition])

    def __contains__(self, key: str) -> bool:
        return (key in self._cache) or self._coder.is_defined(key, header_only=True)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Header):
            eq = False
            items1 = self.items(skip="read_only")
            items2 = other.items(skip="read_only")
            for (k1, v1), (k2, v2) in zip(items1, items2):
                if k1 != k2:
                    break
                if isinstance(v1, np.ndarray):
                    if not isinstance(v2, np.ndarray):
                        break
                    if not np.all(v1.data == v2.data):
                        break
                else:
                    if v1 != v2:
                        break
            else:
                eq = True
        else:
            eq = False
        return eq

    def __getitem__(self, key: str) -> ValueLike:
        try:
            entry = self._cache[key]
        except KeyError:
            value = self._coder.get(key, header_only=True)
            self._cache[key] = Entry(key, value)
        else:
            if entry.computed:
                assert entry.value is None
                if entry.derive:
                    value = entry.derive(self, key)
                else:
                    value = self._coder.get(key, validate=False)
            else:
                assert entry.value is not None
                value = entry.value
        return value

    def __setitem__(self, key: str, value: ValueLike) -> None:
        if key == "edition":
            current_edition = cast(int, self._coder.get("edition", validate=False))
            if value != current_edition:
                for k in COMPUTED_ENTRIES[current_edition].keys():
                    self._cache.pop(k, None)
                assert isinstance(value, int)
                self._cache.update(COMPUTED_ENTRIES[value])
        try:
            entry = self._cache[key]
        except KeyError:
            self._coder.set(key, value, header_only=True)
            self._cache[key] = Entry(key, value, dirty=True)
        else:
            if entry.computed:
                if entry.project:
                    entry.project(self, key, value)
                else:
                    self._coder.set(key, value, header_only=True)
            else:
                self._coder.set(key, value, header_only=True)
                entry.value = value
                entry.dirty = True

    def __str__(self) -> str:
        import pprint

        d = self.as_dict()
        return pprint.pformat(d, sort_dicts=False)

    def copy_to(self, other: "Header", skip_template_keys=False) -> None:
        """Copies common items from this header to `other`."""
        for key, value in self.items(skip="read_only"):
            if key == "unexpandedDescriptors":
                break
            try:
                other[key] = value
            except NotFoundError:
                continue
        if not skip_template_keys:
            if other._coder._baked_template:
                raise EncodingError("Cannot change baked template")
            self._coder.unpack()
            for skey, okey in zip(TEMPLATE_KEYS, INPUT_TEMPLATE_KEYS):
                if okey not in other._cache:
                    try:
                        value = self._coder.get(skey, validate=False)
                    except NotFoundError:
                        continue
                    else:
                        other._coder.set(okey, value)

    def get_count(self, key: str) -> int:
        """Returns the number of elements designated by the given key."""
        self.__getitem__(key)
        return 1

    def get_shape(self, key: str) -> Tuple[int, ...]:
        value = self.__getitem__(key)
        if isinstance(value, np.ndarray):
            shape = value.shape
        else:
            shape = ()
        return shape

    def get_size(self, key: str) -> int:
        value = self.__getitem__(key)
        if isinstance(value, np.ndarray):
            size = value.size
        else:
            size = 1
        return size

    def is_missing(self, key: str) -> bool:
        self.__getitem__(key)
        return False

    def items(self, ranked=False, **kwds) -> Iterator[Tuple[str, ValueLike]]:
        for key in self.keys(**kwds):
            yield key, self._coder.get(key, validate=False)

    def keys(self, ranked=False, **kwds) -> Iterator[str]:
        yield from self._coder.keys(header_only=True, **kwds)

    def set(self, key: str, value: ValueLike) -> None:
        self.__setitem__(key, value)

    def set_missing(self, key: str):
        self.__getitem__(key)
        raise ValueCannotBeMissingError(f"Header key '{key}' can't have missing value'")

    def as_dict(self, ranked=False, depth=0, **kwds) -> Dict:
        """Returns dict-like representation of the header items."""
        counts_only = kwds.pop("counts_only", False)
        shapes_only = kwds.pop("shapes_only", False)
        if counts_only:
            d = {k: self.get_count(k) for k in self.keys(ranked, **kwds)}
        elif shapes_only:
            d = {k: self.get_shape(k) for k in self.keys(ranked, **kwds)}
        else:
            d = dict(self.items(ranked, **kwds))
        return d

    def _commit(self) -> None:
        return  # [1]
        if self._cache:
            for key in [
                "edition",
                "bufrHeaderCentre",
                "masterTableNumber",
            ]:  # must be set first
                try:
                    value = self._cache.pop(key)
                except KeyError:
                    continue
                self._coder.set(key, value, validate=False)  # [2]
            for key, value in self._cache.items():
                self._coder.set(
                    key, value, validate=False, ignore_read_only_error=True
                )  # [2]

        # [1] Currently, when setting header keys, we pass the values right through
        #     into the coder, so there is no need to flush the cache before packing.
        #     But we will probably need this in the future when adding support for
        #     dynamically resizeable replication blocks, which will require full
        #     virtualisation of BUFR messages. TODO
        #
        # [2] Just a reminder that we don't need to use header_only=True here
        #     because the keys in the cache are header-only by definition.
