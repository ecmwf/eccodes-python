# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import io
import warnings

from .common import *
from .helpers import ensure_array, missing_of
from .tables import Code, Element, Tables, Version

TEMPLATE_KEYS = dict.fromkeys(
    [
        "numberOfSubsets",
        "compressedData",
        "dataPresentIndicator",
        "delayedDescriptorAndDataRepetitionFactor",
        "delayedDescriptorReplicationFactor",
        "extendedDelayedDescriptorAndDataRepetitionFactor",
        "extendedDelayedDescriptorReplicationFactor",
        "shortDelayedDescriptorReplicationFactor",
        "unexpandedDescriptors",
    ]
)

INPUT_TEMPLATE_KEYS = dict.fromkeys(
    [  # [1]
        "numberOfSubsets",
        "compressedData",
        "inputDataPresentIndicator",
        "inputDelayedDescriptorAndDataRepetitionFactor",
        "inputDelayedDescriptorReplicationFactor",
        "inputExtendedDelayedDescriptorAndDataRepetitionFactor",
        "inputExtendedDelayedDescriptorReplicationFactor",
        "inputShortDelayedDescriptorReplicationFactor",
        "unexpandedDescriptors",
    ]
)

# [1] When creating a new message, template keys must be set in a specific
#     order. That's why we use a `dict` and not a `set`; `sets` don't
#     preserve insertion order.

ARRAY_KEYS = TEMPLATE_KEYS.copy()
ARRAY_KEYS.update(INPUT_TEMPLATE_KEYS)
ARRAY_KEYS.pop("numberOfSubsets")
ARRAY_KEYS.pop("compressedData")


class Coder:
    _handle: int = 0
    _unpacked: bool = False
    _subset_count: int = 0
    _baked_template: bool = False
    _compressed: bool = False
    _autorelease: bool = True
    _clone_handle: int = 0  # [1]
    _clone_retry_count: int = 0
    _last_extract_method: str = ""  # [2]

    # [1] We need an extra handle so that we can work around issues with repeated
    #     subset extractions (see ECC-2015 and ECC-2016).
    #
    # [2] We are keeping track of the latest extraction method because ecCodes
    #     currently doesn't handle cases with mixed extractions correctly; that
    #     is not without creating a new clone of the original handle (see ECC-2016).

    def __init__(self, source) -> None:
        if isinstance(source, io.IOBase):
            try:
                fileno = source.fileno()
            except OSError:
                fileno = None
            if fileno is None:
                raise TypeError(
                    "Expected file-like object with a file descriptor; got %s"
                    % type(source)
                )
            handle = codes_bufr_new_from_file(source)
            if not handle:
                raise EOFError()
        elif isinstance(source, bytes):
            handle = codes_new_from_message(source)
        elif isinstance(source, str):
            handle = codes_bufr_new_from_samples(source)
        elif isinstance(source, int):
            handle = source
        else:
            raise TypeError(
                "Expected file-like object, bytes array or a sample name; got %s"
                % type(source)
            )
        self._handle = handle
        self._autorelease = current_behaviour.autorelease_handle

    def __del__(self) -> None:
        if self._autorelease:
            self.release()

    def clone(self, subsets=None) -> "Coder":
        self.pack()
        if subsets is None:
            handle = codes_clone(self._handle)
            coder = Coder(handle)
        else:
            if not self._clone_handle:  # [1]
                self._clone_handle = codes_clone(self._handle)
                codes_set_long(self._clone_handle, "unpack", 1)
            try:  # [2]
                self._extract(subsets)
                handle = codes_clone(self._clone_handle)
            except (InternalError, ArrayTooSmallError) as error:  # [3]
                if self._clone_retry_count > 1:
                    raise error
                else:
                    codes_release(self._clone_handle)
                    self._clone_handle = 0
                    self._clone_retry_count += 1
                    self._last_extract_method = ""
                    coder = self.clone(subsets)
            else:
                self._clone_retry_count = 0
                coder = Coder(handle)
        return coder

    # [1] We need an extra handle so that we can work around issues with repeated
    #     subset extractions (see ECC-2015).
    #
    # [2] This is also related to ECC-2015. If the extraction of subsets fails,
    #     we try one more time with a new clone of the original handle. If that
    #     fails too, we raise an exception.
    #
    # [3] The ArrayTooSmallError is needed because of ECC-2025.

    def _extract(self, subsets):
        if isinstance(array := subsets, np.ndarray):
            if array.dtype == bool:
                subsets = np.arange(array.size)[array]
            elif array.dtype != int:
                message = "`subsets` must be an array of bool or int; got type %s"
                raise TypeError(message % array.dtype)
            start, stop = subsets[0], subsets[-1] + 1
            is_interval = subsets.size == stop - start
            is_interval = is_interval and np.all(subsets == np.arange(start, stop))
        elif isinstance(subsets, range):
            is_interval = subsets.step == 1
        elif isinstance(subsets, Sequence):
            subsets = list(subsets)
            is_interval = True
            for s, r in zip(subsets, range(subsets[0], subsets[0] + len(subsets))):
                if s != r:
                    is_interval = False
                    break
        elif isinstance(subsets, slice):
            start = 0 if subsets.start is None else subsets.start
            stop = self._subset_count if subsets.stop is None else subsets.stop  # [1]
            step = 1 if subsets.step is None else subsets.step
            subsets = range(start, stop, step)
            is_interval = subsets.step == 1
        else:
            message = "`subsets` must be an array, sequence, or a slice; got %s"
            raise TypeError(message % type(subsets))
        if is_interval:
            method = "SubsetInterval"
            start = subsets[0] + 1
            end = subsets[-1] + 1
            codes_set_long(self._clone_handle, "extractSubsetIntervalStart", start)
            codes_set_long(self._clone_handle, "extractSubsetIntervalEnd", end)
        else:
            method = "SubsetList"
            codes_set_long_array(
                self._clone_handle, "extractSubsetList", [s + 1 for s in subsets]
            )
        codes_set_long(self._clone_handle, "doExtractSubsets", 1)
        if (last := self._last_extract_method) and method != last:
            codes_release(self._clone_handle)
            self._clone_handle = codes_clone(self._handle)
            codes_set_long(self._clone_handle, "unpack", 1)
            self._last_extract_method = ""
            self._extract(subsets)
        self._last_extract_method = method

    # [1] Note that there is a bug in ecCodes where the extraction operation
    #     resets the original value of 'numberOfSubsets' to the number of
    #     extracted subsets. That's why it's important to use the subset count
    #     from the original handle, not the clone!

    def get_buffer(self) -> bytes:
        self.pack()
        bytes = codes_get_message(self._handle)
        return bytes

    def get_bitmap(self) -> NDArray:
        """Returns bitmap array as a boolean mask.

        Note that this is a concatenation of all bitmaps into a single, large array.
        """
        self.unpack()
        try:
            bitmap = codes_get_long_array(self._handle, "dataPresentIndicator")
        except NotFoundError:
            bitmap = np.array([])
        bitmap[:] = 1 - bitmap[:]  # [1]
        bitmap = np.ma.make_mask(bitmap, copy=False, shrink=False, dtype=bitmap.dtype)
        return bitmap

        # [1] We are flipping zeros and ones to follow the standard convention
        #     of 1 meaning True, and 0 False, not the other way arround.

    def get_delayed_replication_factors(self) -> Dict[int, NDArray]:
        """Returns a `dict` of concatenated delayed replication factors."""
        self.unpack()
        factors = {}
        for code, name in [
            (31000, "shortDelayedDescriptorReplicationFactor"),
            (31001, "delayedDescriptorReplicationFactor"),
            (31002, "extendedDelayedDescriptorReplicationFactor"),
            (31011, "delayedDescriptorAndDataRepetitionFactor"),
            (31012, "extendedDelayedDescriptorAndDataRepetitionFactor"),
        ]:
            try:
                array = codes_get_long_array(self._handle, name)
            except NotFoundError:
                continue
            factors[code] = array
        return factors

    def checkout(self, entry: DataEntry):
        if entry.flags & FACTOR:
            # In principle we shouldn't need this branch as we pre-load all delayed
            # replication factor arrays in build_tree(). However, some messages
            # can have wrongly encoded bitmap where the factor ends up having an
            # associated key (e.g., delayedReplicationFactor->percentConfidence).
            # TODO: Should we hide these keys from the user?
            array = codes_get_array(self._handle, entry.name)
            array = np.reshape(array, entry.shape)
        elif entry.flags & BITMAP:
            array = codes_get_array(self._handle, entry.name)
            entry.shape = (
                entry.shape[0],
                array.size,
            )  # infer the 2nd dimension earlier TODO
        elif entry.association:
            if entry.name.find("->associatedField") > 0:
                # Note that his works reliably only for ->associatedField keys.
                # For bitmap-associated keys, if some of the ranks don't have an associated
                # value, this will either fail (ECC-1272), or worse, return an incomplete
                # array (ECC-1689).
                array = codes_get_array(self._handle, entry.name)
                # array = self._ensure_correct_size(entry, array)
            else:
                assert entry.primary
                rank_mask = entry.association.rank_mask(entry.primary.name)
                if np.count_nonzero(rank_mask) == 0:
                    raise NotFoundError(entry.name)
                assert len(rank_mask) == entry.primary.shape[0]
                dtype = entry.association.element_dtype
                array = np.empty(entry.shape, dtype)
                fill_value = missing_of(dtype)
                for rank, is_set in enumerate(rank_mask, start=1):
                    if is_set:
                        # Note: bitmap-associated keys have to be retrieved one
                        # rank at a time (see ECC-1272).
                        if not self._compressed or entry.flags & SCALAR:
                            array[rank - 1] = codes_get(
                                self._handle, f"#{rank}#{entry.name}"
                            )
                        else:
                            array[rank - 1, :] = codes_get_array(
                                self._handle, f"#{rank}#{entry.name}"
                            )
                    else:
                        array[rank - 1] = fill_value
        elif entry.uniform_element and entry.uniform_element.code == 31021:  # [0]
            array = np.empty(entry.shape, int)
            if not self._compressed or entry.flags & SCALAR:
                for rank in range(1, entry.shape[0] + 1):
                    array[rank - 1] = codes_get_long(
                        self._handle, f"#{rank}#{entry.name}"
                    )
            else:
                for rank in range(1, entry.shape[0] + 1):
                    array[rank - 1, :] = codes_get_long_array(
                        self._handle, f"#{rank}#{entry.name}"
                    )
        else:
            ktype = None
            if entry.name == "second":
                if entry.uniform_element and entry.uniform_element.scale == 0:
                    ktype = int  # [1]
            array_or_list = codes_get_array(self._handle, entry.name, ktype)
            if isinstance(array_or_list, list) and isinstance(array_or_list[0], str):
                if not entry.uniform_element:
                    raise NotImplementedError(
                        "Non-uniform string keys are not supported yet: %s" % entry.name
                    )
                element = self._tables.elements[entry.uniform_element.code]
                byte_count, remainder = divmod(element.width, 8)
                assert remainder == 0
                dtype = np.dtype(("<U", byte_count))
            else:
                dtype = None
            array = ensure_array(array_or_list, dtype)
            if entry.name == "centre":  # [2]
                for rank in range(1, entry.shape[0] + 1):
                    array[rank - 1] = codes_get_long(self._handle, f"#{rank}#centre")
                array = array[0 : entry.shape[0]]
            array = self._ensure_correct_size(entry, array)
        return array

        # [0] Currently, ecCodes doesn't allow to retrieve ...->associatedFieldSignificance
        #     values (descriptor 31021) with a single call to codes_get_array(), so
        #     we have to get the values one rank at a time. See ECC-2098.
        #
        # [1] ecCodes infers native type of key 'second' (descriptor 004006) to
        #     be float, but this is not quite right. The default scale of this
        #     descriptor is 0, meaning it can't represent floating-point values.
        #     So, in the absence of 'Change scale' operator, the default native
        #     type should be int.
        #
        # [2] To work around ECC-1624, we have to get 'centre' values rank by rank.

    def commit(self, entry) -> None:
        key = entry.name
        array = entry.array
        array.data[array.mask] = array.fill_value
        if entry.association:
            a = entry.association
            rank_mask = a.rank_mask(entry.primary.name)
            array = array.reshape(entry.shape)
            for rank, value in enumerate(array, start=1):
                if rank_mask[rank - 1]:
                    if value.ndim == 1:
                        codes_set_array(self._handle, f"#{rank}#{key}", value.data)
                    else:
                        codes_set(self._handle, f"#{rank}#{key}", value)
        else:
            if array.dtype.type == np.str_:
                if array.size == 1:  # [1]
                    codes_set(self._handle, key, array.data[0][0])
                elif array.size > 1 and not np.any(array != array.data[0][0]):
                    codes_set_array(self._handle, key, array.data[0][0:1])
                else:
                    codes_set_array(self._handle, key, array.data.ravel())
            elif self._compressed:
                rank_count = entry.shape[0]
                for rank in range(1, rank_count + 1):
                    rank_array = array.data[rank - 1]
                    if np.any(rank_array != rank_array[0]):
                        codes_set_array(self._handle, f"#{rank}#{key}", rank_array)
                    else:
                        codes_set_array(
                            self._handle, f"#{rank}#{key}", rank_array[0:1]
                        )  # [2]
            else:
                if key == "centre":  # [3]
                    for rank in range(1, array.size + 1):
                        codes_set(self._handle, f"#{rank}#{key}", array.data[rank - 1])
                else:
                    try:
                        codes_set_array(self._handle, key, array.data)
                    except ArrayTooSmallError as error:  # [4]
                        if (
                            entry.uniform_element
                            and entry.uniform_element.code == 31021
                        ):
                            for rank in range(1, array.size + 1):
                                codes_set(
                                    self._handle, f"#{rank}#{key}", array.data[rank - 1]
                                )
                        else:
                            raise error

        if self._clone_handle:  # [5]
            codes_release(self._clone_handle)
            self._clone_handle = 0

        # [1] This is a workaround for ECC-1623.
        #
        # [2] If all values in an array are the same, encode only a single scalar value.
        #
        # [3] The key 'centre' is also an alias for the header key 'headerCentre',
        #     and calling codes_set_array() on an array of data elements would treat
        #     the first element as a header value, which is not what we want.
        #     To work around this we have to set the values rank by rank. See ECC-1624.
        #
        # [4] Currently, ecCodes doesn't allow to use codes_set_array() on
        #     ...->associatedFieldSignificance keys, so we have to set the
        #     values rank by rank. See ECC-2098.
        #
        # [5] If there had been any changes to the original handle since the
        #     last time we created a clone, make sure we re-create the clone
        #     from scratch next time around so that it picks the latest changes.
        #     Note that this is only needed as a workarond for ECC-2015 and ECC-2016.

    def _ensure_correct_size(self, entry, array):
        if entry.flags & SCALAR:
            assert entry.shape[1] == 1
            if array.size == entry.shape[0]:
                array = np.reshape(array, entry.shape)
            else:
                msg = f"'{entry.name}' is assumed to be a scalar element, but it has more than one value per rank"
                action = current_behaviour.on_assumed_scalar_element_invalid_size
                if action == "raise":
                    raise ValueError(msg)
                elif action == "warn":
                    warnings.warn(msg)
                elif action == "ignore":
                    pass
                else:
                    msg = f"'{action}' is not a valid action for `on_invalid_assumed_scalar_element_size`"
                    raise ValueError(msg)
                entry.flags = entry.flags & ~Flags.SCALAR
                entry.shape = (entry.shape[0], self._subset_count)
                array = self._ensure_correct_size(entry, array)
        elif self._compressed:
            # Workaround for ECC-428
            if array.size == entry.shape[0] and entry.shape[1] > 1:
                array = np.expand_dims(array, axis=1)
                array = np.broadcast_to(array, entry.shape).copy()  # [1]
            elif array.size > entry.shape[0] and array.size < entry.size:
                new_array = np.empty(entry.shape, array.dtype)
                offset = 0
                for rank in range(1, entry.shape[0] + 1):
                    size = codes_get_size(self._handle, f"#{rank}#{entry.name}")
                    assert size == entry.shape[1] or size == 1
                    new_array[rank - 1, :] = array[offset : offset + size]
                    offset += size
                array = new_array
            elif array.size == 1 and entry.size > 1:
                array = np.full(entry.shape, array[0])  # [2]
            else:
                array = np.reshape(array, entry.shape)
        return array

        # [1], [2] Avoid creating unnecessary copies in read-only mode. TODO

    @cached_property
    def _tables(self) -> Tables:
        return self.get_tables()

    def get(
        self, key: str, header_only=False, data_only=False, validate=True
    ) -> ValueLike:
        if validate:
            if header_only and data_only:
                raise ValueError("header_only and data_only can't be both True")
            if header_only:
                if not codes_bufr_key_is_header(self._handle, key):
                    raise NotFoundError(key)
                if key == "centre":
                    raise NotFoundError(
                        f"{key}: Did you mean bufrHeaderCentre? (see ECC-1624)"
                    )
                if "->" in key:  # [1]
                    raise NotFoundError(key)
            elif data_only:
                if codes_bufr_key_is_header(self._handle, key):
                    raise NotFoundError(key)
        try:
            if key in ARRAY_KEYS:
                value = codes_get_array(self._handle, key)
            else:
                try:
                    value = codes_get(self._handle, key)
                except ArrayTooSmallError:
                    value = codes_get_array(self._handle, key)
        except NotFoundError as error:
            error.msg = key
            raise error
        return value

        # [1] Make sure we don't accidentally leak data section keys/values via
        #     the Header class. This can happen if the user tries to get attribute
        #     of an associated key, e.g., 'pressure->percentConfidence->code'.
        #     This should be captured by codes_bufr_key_is_header(), but it's not!

    def get_tables(self) -> Tables:
        version = Version()
        version.master = cast(
            int, codes_get_long(self._handle, "masterTablesVersionNumber")
        )
        version.local = cast(
            int, codes_get_long(self._handle, "localTablesVersionNumber")
        )
        version.centre = cast(int, codes_get_long(self._handle, "bufrHeaderCentre"))
        version.subcentre = cast(
            int, codes_get_long(self._handle, "bufrHeaderSubCentre")
        )
        tables = Tables(version)
        return tables

    def is_defined(self, key: str, header_only=False, data_only=False) -> bool:
        assert not (header_only and data_only)
        if defined := codes_is_defined(self._handle, key):
            if header_only:
                defined = codes_bufr_key_is_header(self._handle, key)
            elif data_only:
                defined = not codes_bufr_key_is_header(self._handle, key)
        return defined

    def is_missing(self, entry: DataEntry, slice: slice) -> bool:
        assert slice.stop - slice.start > 0
        is_missing = 1
        for rank in range(slice.start + 1, slice.stop + 1):
            if not (
                is_missing := codes_is_missing(self._handle, f"#{rank}#{entry.name}")
            ):
                break
        return bool(is_missing)

    def set_missing(self, entry: DataEntry, slice):
        assert slice.stop - slice.start > 0
        for rank in range(slice.start + 1, slice.stop + 1):
            codes_set_missing(self._handle, f"#{rank}#{entry.name}")

    def keys(self, header_only=False, data_only=False, **kwargs) -> Iterator[str]:
        assert not (header_only and data_only)
        yield from keys_of(
            self._handle, header_only=header_only, data_only=data_only, **kwargs
        )

    def pack(self) -> bool:
        if self._unpacked:
            codes_set_long(self._handle, "pack", 1)
            total_length = codes_get_long(self._handle, "totalLength")
            try:
                codes_set_long(self._handle, "messageLength", min(total_length, 65535))
            except NotFoundError:
                pass
            return True
        else:
            return False

    def release(self) -> None:
        if self._handle:
            codes_release(self._handle)
            self._handle = 0
        if self._clone_handle:
            codes_release(self._clone_handle)
            self._clone_handle = 0

    def set(
        self,
        key: str,
        value: ValueLike,
        header_only=False,
        data_only=False,
        validate=True,
        ignore_read_only_error=False,
    ) -> None:
        if validate:
            if header_only and data_only:
                raise ValueError("header_only and data_only can't be both True")
            if self._baked_template and key in INPUT_TEMPLATE_KEYS:
                raise ReadOnlyError(key)
            if key in ("pack", "unpack"):
                message = (
                    "%sing via the '%s' key is disallowed. Call %s() method istead."
                )
                raise NotFoundError(message % (key.capitalize(), key, key))
            if header_only:
                if not codes_bufr_key_is_header(self._handle, key):
                    raise NotFoundError(key)
                if key == "centre":  # [1]
                    raise NotFoundError(
                        f"{key}: Did you mean bufrHeaderCentre? (see ECC-1624)"
                    )
            elif data_only:
                if codes_bufr_key_is_header(self._handle, key):
                    raise NotFoundError(key)
        if key == "unexpandedDescriptors":
            self._unpacked = True  # for messages created from samples
        try:
            if hasattr(value, "__iter__") and not isinstance(value, str):
                codes_set_array(self._handle, key, value)
            else:
                codes_set(self._handle, key, value)
        except ReadOnlyError as error:
            if ignore_read_only_error:
                pass
            else:
                error.msg += f": {key}"
                raise error
        if not header_only:
            if self._clone_handle:  # [2]
                codes_release(self._clone_handle)
                self._clone_handle = 0

        # [1] ecCodes allows use of 'centre' as an alias for 'bufrHeaderCentre', but
        #     we disallow it because it causes ambiguity when 'centre' simultaneously
        #     appears in the data section too, such as in the presence of bitmap operator
        #     for instance. It would be confusing if we returned combined values from
        #     both the header and the data section in a single array when accessing
        #     'centre' from the Message view. Unfortunately, right now this is exactly
        #     what ecCodes does (see ECC-1624).
        #
        # [2] If there had been any changes to the original handle's data section
        #     since the last time we had created the clone, make sure we re-create
        #     the clone from scratch next time around so that it picks up those changes.
        #     Note that this is only needed because of ECC-2015 and ECC-2016.

    def unpack(self) -> bool:
        if self._unpacked:
            return False
        else:
            codes_set_long(self._handle, "skipExtraKeyAttributes", 1)  # [1]
            codes_set_long(self._handle, "unpack", 1)
            self._unpacked = True
            return True

        # [1] We don't need to extract key attributes at the library level as we can
        #     infer all attributes, lazily, from the ElementTable.

    def write(self, file: BinaryIO) -> int:
        self.pack()
        codes_write(self._handle, file)
        size = codes_get_message_size(self._handle)
        return size


class KeysIterator(object):
    """A simple wrapper around `codes_keys_iterator()` function.

    This class is mostly for internal use. Generally speaking, users should
    rely on the higher-level interface provided by `Message`, `Header`
    and `Data` classes.
    """

    def __init__(self, msg_handle, bufr_only=True, skip: FlagsLike = None):
        skip_flags = ensure_flags(skip)
        if bufr_only:
            self._handle = codes_bufr_keys_iterator_new(msg_handle)
            self._next = codes_bufr_keys_iterator_next
            self._get_name = codes_bufr_keys_iterator_get_name
            self._delete = codes_bufr_keys_iterator_delete
        else:
            self._handle = codes_keys_iterator_new(msg_handle)
            self._next = codes_keys_iterator_next
            self._get_name = codes_keys_iterator_get_name
            self._delete = codes_keys_iterator_delete

        if skip_flags & Flags.CODED:
            codes_skip_coded(self._handle)
        if skip_flags & Flags.COMPUTED:
            codes_skip_computed(self._handle)
        if skip_flags & Flags.READ_ONLY:
            codes_skip_read_only(self._handle)

    def __del__(self):
        self._delete(self._handle)

    def __iter__(self):
        return self

    def __next__(self):
        if self._next(self._handle):
            return self._get_name(self._handle)
        else:
            raise StopIteration


def keys_of(
    msg_handle,
    bufr_only=True,
    header_only=False,
    data_only=False,
    skip: FlagsLike = None,
) -> Iterator[str]:
    """Returns an iterator over the keys of the message.

    By default, the iteration runs over all keys, which includes keys from both
    the header and the data section. Optionally, user can constrain the
    iterator to only return keys from one of the sections by setting
    `header_only` or `data_only` keyword argument.

    Note that in order to access data section keys, the message must be
    unpacked. It's user's responsibility to do so before calling this function.
    If the message hasn't been unpacked, trying to access data keys will raise
    an exception.

    When `bufr_only` is True, the iterator returns BUFR-specific keys only; if
    False, all generic keys are returned instead.

    This function is mostly for internal use. Generally speaking, users should
    rely on the higher-level interface provided by `Message`, `Header`
    and `Data` classes.
    """
    if header_only and data_only:
        raise ValueError(
            "Keyword arguments `header_only` and `data_only` can't both be True"
        )

    data_keys = False
    keys = KeysIterator(msg_handle, bufr_only, skip)
    data_keys_unaccessible = (
        "Cannot access data keys because message hasn't been unpacked. "
    )
    data_keys_unaccessible += "If you want to access header keys only, set keyword argument `header_only` to True."

    if bufr_only:
        for key in keys:
            if key == "unexpandedDescriptors":
                next_key = next(keys, None)
                if next_key == None:
                    if not header_only:
                        raise RuntimeError(data_keys_unaccessible)
                else:
                    data_keys = True
                if header_only:
                    yield key
                    break
                elif data_only:
                    key = next_key
                else:
                    yield key
                    key = next_key
            if data_only and not data_keys:
                continue
            yield key
    else:
        for key in keys:
            if key == "dataKeys":
                next_key = next(keys, None)
                if next_key == "section4Padding":
                    if not header_only:
                        raise RuntimeError(data_keys_unaccessible)
                else:
                    data_keys = True
                if header_only:
                    yield key
                    key = next_key
                elif data_only:
                    key = next_key
                else:
                    yield key
                    key = next_key
            elif key == "section4Padding":
                data_keys = False
            if (header_only and data_keys) or (data_only and not data_keys):
                continue
            yield key
