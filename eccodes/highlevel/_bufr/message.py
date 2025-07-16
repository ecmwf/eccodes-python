# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import datetime as dt

from .coder   import Coder
from .common  import *
from .data    import Data
from .header  import Header
from .view    import View

class Message(View):

    def __init__(self, source) -> None:
        if isinstance(source, Coder):
            coder = source
        else:
            coder = Coder(source)
        self.header = Header(coder)
        self.data = Data(coder)
        self._coder = coder

    def __contains__(self, key: str) -> bool:
        """Return True if `key` is defined, otherwise return False.
        """
        return (key in self.header) or (key in self.data)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._coder.release()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BUFRMessage):
            eq = (self.header == other.header) and (self.data == other.data)
        else:
            eq = False
        return eq

    def __getitem__(self, key: str) -> ValueLike:
        if self._coder._unpacked:
            try:
                value = cast(ValueLike, self.data[key])
            except NotFoundError:
                value = self.header[key]
        else:
            try:
                value = self.header[key]
            except NotFoundError:
                value = cast(ValueLike, self.data[key])
        return value

    def __setitem__(self, key: str, value: ValueLike) -> None:
        if self._coder._unpacked:
            try:
                self.data[key] = value
            except NotFoundError:
                self.header[key] = value
        else:
            try:
                self.header[key] = value
            except NotFoundError:
                self.data[key] = value

    def __str__(self) -> str:
        import pprint
        d = self.as_dict()
        return pprint.pformat(d, sort_dicts=False)

    @classmethod
    def from_samples(cls, sample_name):
        """Creates a new message from the sample.
        """
        return cls(Coder(sample_name))

    def copy(self, *, subsets: Optional[Union[NDArray, Sequence, slice]] = None) -> 'BUFRMessage':
        """Returns a new copy of the message.

        If the optional argument `subsets` is specified, only the selected subsets
        will be copied. `subsets` can be a mask, an array or a sequence of (0-based)
        subset indices, or a slice. For conveniece, `subsets` can also be a slice
        with numpy's `datetime64` objects, or with the built-in `datetime` objects.
        For such slices the stop bounds are inclusive.
        """
        self._commit() # [1]
        if subsets is not None\
                and isinstance(subsets, slice) \
                and (isinstance(subsets.start, (np.datetime64, dt.datetime)) or \
                     isinstance(subsets.stop,  (np.datetime64, dt.datetime))):
            datetime = self.data.get_datetime(rank=1)
            start = dt.datetime.min if subsets.start is None else subsets.start
            stop  = dt.datetime.max if subsets.stop  is None else subsets.stop
            mask  = np.logical_and(datetime >= start, datetime <= stop)
            coder = self._coder.clone(mask)
        else:
            coder = self._coder.clone(subsets)
        message = BUFRMessage(coder)
        return message

        # [1] In theory we could avoid committing (and hence packing) if we
        #     copied the "original" data plus Data's cache and tree structure. TODO

    def copy_to(self, other: 'BUFRMessage',
                header_only=False, data_only=False,
                skip_template_keys=False) -> None:
        """Copies common keys/values from this message to `other`.
        """
        if header_only and data_only:
            raise ValueError("`header_only` and `data_only` can't both be true")
        if not data_only:
            self.header.copy_to(other.header, skip_template_keys)
        if not header_only:
            self.data.copy_to(other.data)

    def get_count(self, key: str) -> int:
        """Returns the number of elements designated by the given key.
        """
        if self._coder._unpacked:
            try:
                count = self.data.get_count(key)
            except NotFoundError:
                count = self.header.get_count(key)
        else:
            try:
                count = self.header.get_count(key)
            except NotFoundError:
                count = self.data.get_count(key)
        return count

    def get_shape(self, key: str) -> Tuple[int, ...]:
        """Returns shape of the given key.
        """
        if self._coder._unpacked:
            try:
                shape = self.data.get_shape(key)
            except NotFoundError:
                shape = self.header.get_shape(key)
        else:
            try:
                shape = self.header.get_shape(key)
            except NotFoundError:
                shape = self.data.get_shape(key)
        return shape

    def get_size(self, key: str) -> int:
        """Returns size of the given key.
        """
        if self._coder._unpacked:
            try:
                size = self.data.get_size(key)
            except NotFoundError:
                size = self.header.get_size(key)
        else:
            try:
                size = self.header.get_size(key)
            except NotFoundError:
                size = self.data.get_size(key)
        return size

    def is_missing(self, key: str) -> bool:
        """Checks the key is set to missing value.

        If the value is an array, returns true only if all elements in the array
        are set to missing value.
        """
        if self._coder._unpacked:
            try:
                is_missing = self.data.is_missing(key)
            except NotFoundError:
                is_missing = self.header.is_missing(key)
        else:
            try:
                is_missing = self.header.is_missing(key)
            except NotFoundError:
                is_missing = self.data.is_missing(key)
        return is_missing

    def set(self, key: str, value: ValueLike) -> None:
        if self._coder._unpacked:
            try:
                self.data.set(key, value)
            except NotFoundError:
                self.header.set(key, value)
        else:
            try:
                self.header.set(key, value)
            except NotFoundError:
                self.data.set(key, value)

    def set_missing(self, key: str) -> None:
        """Sets the key to missing value.

        If the value is an array, sets all elements to missing value.
        """
        if self._coder._unpacked:
            try:
                self.data.set_missing(key)
            except NotFoundError:
                self.header.set_missing(key)
        else:
            try:
                self.header.set_missing(key)
            except NotFoundError:
                self.data.set_missing(key)

    def get_buffer(self) -> bytes:
        """Returns a buffer containing the encoded message.
        """
        self._commit()
        return self._coder.get_buffer()

    def as_dict(self, ranked=False, depth=0, **kwds) -> Dict:
        """Returns dict-like representation of the message items.
        """
        header_only = kwds.pop('header_only', False)
        data_only = kwds.pop('data_only', False)
        if not data_only:
            h = self.header.as_dict(ranked, depth-1, **kwds)
        if not header_only:
            d = self.data.as_dict(ranked, depth-1, **kwds)
        if header_only:
            m = h
        elif data_only:
            m = d
        else:
            if depth > 0:
                m = {'header': h, 'data': d}
            else:
                m = h | d
        return m

    def items(self, ranked=False, **kwds) -> Iterator[Tuple[str, ValueLike]]:
        yield from self.header.items(ranked, **kwds)
        yield from self.data.items(ranked, **kwds)

    def keys(self, ranked=False, **kwds) -> Iterator[str]:
        yield from self.header.keys(ranked, **kwds)
        yield from self.data.keys(ranked, **kwds)

    def pack(self) -> None:
        """Encodes the contents of the data section into an internal buffer.

        Note that this happens automatically whenever needed (before writing
        to a file, before copying, etc.), so users don't need to call this method
        explicitly.
        """
        self._commit()
        self._coder.pack()

    def unpack(self) -> None:
        """Decodes the contents of the data section into an internal representation.

        Note that this happens automatically whenever needed (when accessing data
        section keys for the first time, before copying, etc.), so users don't need
        to call this method explicitly.
        """
        self._coder.unpack()

    def write(self, file: BinaryIO) -> int:
        import warnings
        warnings.warn("Method write() is deprecated. Use method write_to() instead.", DeprecationWarning)
        return self.write_to(file)

    def write_to(self, file: BinaryIO) -> int:
        """ Encodes the message (if not already encoded) and writes it to a file.

        Returns the size of the encoded message in bytes.

        `file` must be a file-like object.
        """
        self._commit()
        size = self._coder.write(file)
        return size

    def _commit(self) -> None:
        if current_behaviour.update_header_from_data_before_packing:
            self.update_header_from_data(skip_dirty=True)
        self.header._commit()
        self.data._commit()

    @property
    def _handle(self) -> int:
        return self._coder._handle

    def update_header_from_data(self, skip_dirty=False) -> None:
        """Updates some of the header keys based on keys from the data section.

        This method sets header keys such as 'typicalYear', 'localMonth',
        'localLatitude', etc., based on keys from the data section: 'year',
        'month', 'latitude', etc.

        If there are no datetime-related keys in message's data section, or if
        some of the keys that are needed to construct a complete datetime object
        are missing, the header keys are not updated.

        In the case of multi-subset messages we use the min value across all subsets.

        Note that this method is called automatically before packing, so users typically
        don't need to call this method explicitly. However, if this behaviour is not
        desirable, it can be switched off by setting the `Behaviour` option
        `update_header_from_data_before_packing` to `False`.
        """
        datetime_counts = {}
        for key in ('year', 'month', 'day', 'hour', 'minute'):
            try:
                entry = self.data._entries[key]
            except KeyError:
                has_datetime = False
                break
            if entry.array is None:
                has_datetime = False
                break
            else:
                datetime_counts[key] = self.data.get_count(key)
        else:
            if all(c == datetime_counts['year'] for c in datetime_counts.values()):
                datetime_array = self.data.get_datetime()
            else:
                max_common_rank = min(datetime_counts.values())
                datetime_array = self.data.get_datetime(rank=slice(1, max_common_rank + 1))
            min_datetime = np.min(datetime_array)
            if min_datetime is np.ma.masked:
                has_datetime = False
            else:
                datetime = min_datetime.item()
                has_datetime = True

        if has_datetime:
            items = ['Year', 'YearOfCentury', 'Day', 'Hour', 'Minute', 'Second']
            if not (_any_dirty(self.header, 'typical', items) and skip_dirty):
                if self.header['edition'] == 3:
                    self.header['typicalYearOfCentury'] = datetime.year % 100
                else:
                    self.header['typicalYear'] = datetime.year
                self.header['typicalMonth']  = datetime.month
                self.header['typicalDay']    = datetime.day
                self.header['typicalHour']   = datetime.hour
                self.header['typicalMinute'] = datetime.minute
                self.header['typicalSecond'] = datetime.second

        if self.header['section2Present'] and self.header['bufrHeaderCentre'] == 98:
            if has_datetime:
                items = ['Year', 'Day', 'Hour', 'Minute', 'Second']
                if not (skip_dirty and _any_dirty(self.header, 'local', items)):
                    self.header['localYear']   = datetime.year
                    self.header['localMonth']  = datetime.month
                    self.header['localDay']    = datetime.day
                    self.header['localHour']   = datetime.hour
                    self.header['localMinute'] = datetime.minute
                    self.header['localSecond'] = datetime.second
            now = dt.datetime.now(dt.UTC)
            for prefix in ('rdbtime', 'rectime'):
                items = ['Day', 'Hour', 'Minute', 'Second']
                if not (skip_dirty and _any_dirty(self.header, prefix, items)):
                    self.header[f'{prefix}Day'] = now.day
                    self.header[f'{prefix}Hour'] = now.hour
                    self.header[f'{prefix}Minute'] = now.minute
                    self.header[f'{prefix}Second'] = now.second
            try:
                lat_entry = self.data._entries['latitude']
                lon_entry = self.data._entries['longitude']
            except KeyError:
                has_latlon = False
            else:
                if has_latlon := (lat_entry.array is not None) and (lon_entry.array is not None):
                    lat = lat_entry.array.ravel()
                    lon = lon_entry.array.ravel()
            if self.header['compressedData']:
                if cast(int, self.header['numberOfSubsets']) > 1:
                    if has_latlon:
                        items = ['Latitude1', 'Latitude2', 'Longitude1', 'Longitude2']
                        if not (skip_dirty and _any_dirty(self.header, 'local', items)):
                            self.header['localLatitude1']  = numpy.min(lat)
                            self.header['localLatitude2']  = numpy.max(lat)
                            self.header['localLongitude1'] = numpy.min(lon)
                            self.header['localLongitude2'] = numpy.max(lon)
                    self.header['localNumberOfObservations'] = self.header['numberOfSubsets']
                else:
                    if has_latlon:
                        items = ['Latitude1', 'Longitude1']
                        if not (skip_dirty and _any_dirty(self.header, 'local', items)):
                            self.header['localLatitude1']  = lat[0]
                            self.header['localLongitude1'] = lon[0]
            else:
                if has_latlon:
                    items = ['Latitude1', 'Longitude1']
                    if not (skip_dirty and _any_dirty(self.header, 'local', items)):
                        self.header['localLatitude']  = lat[0]
                        self.header['localLongitude'] = lon[0]

def _any_dirty(header: Header, prefix: str, keys: Sequence[str]) -> bool:
    for key in keys:
        try:
            entry = header._cache[f'{prefix}{key}']
        except KeyError:
            continue
        else:
            if entry.dirty:
                return True
    else:
        return False

BUFRMessage = Message
