# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import datetime as dt
import re
import sys

from collections import Counter, abc, defaultdict
from copy import deepcopy
from dataclasses import dataclass, field, fields
from enum import auto; import enum
from functools import cached_property
from pathlib import Path

from typing import Any, BinaryIO, Callable, Dict, Iterator, List, Optional, Set
from typing import Sequence, Tuple, Union, cast
from numpy.ma import MaskedArray
from numpy.typing import DTypeLike, NDArray

import eccodes
import numpy; import numpy as np

from eccodes.eccodes import *
from eccodes.eccodes import KeyValueNotFoundError as NotFoundError

from .tables  import Element

@dataclass
class Behaviour:
    assumed_scalar_elements: Set = field(default_factory=set) # [1]
    on_assumed_scalar_element_invalid_size: str = 'warn' # [2]
    autorelease_handle: bool = True # [3]
    update_header_from_data_before_packing: bool = True # [4]

# [1] By default, values of data elements in uncompressed, multi-subset messages
#     are one-/two-dimensional arrays, even if there is only one common value for
#     all subsets. This is done in order to provide "stable" view of data elements
#     which doesn't depend on the encoding details. However, for situations where
#     the user can guarantee that an element, or a set of elements, will always
#     have only a single value (per rank), this option can be used to reduce
#     memory usage.
#
# [2] If an assumed scalar element is encoded with more than one value (per rank),
#     either print a warning ('warn'), raise an exception ('raise'), or just carry
#     on as if nothing hapened ('ignore').
#
# [3] Whether to release Coder's C handle automatically. The only reason you might
#     want to set this option to False is if you need to interoperate with the
#     low-level API, but you must know what you're doing.
#
# [4] This option controls whether to call Message's update_header_from_data()
#     method automatically before packing. This method sets some of the header
#     keys such as 'typicalYear', 'localMonth', 'localLatitude', etc.


DEFAULT_BEHAVIOUR = Behaviour(assumed_scalar_elements=set([
        # 'originatorOfRetrievedAtmosphericConstituent',
        # 'satelliteChannelBandWidth',
        # 'satelliteChannelCentreFrequency',
        # 'satelliteIdentifier',
        # 'satelliteInstruments',
    ]))

current_behaviour = deepcopy(DEFAULT_BEHAVIOUR)

def get_behaviour():
    global current_behaviour
    return deepcopy(current_behaviour)

def set_behaviour(new_behaviour):
    global current_behaviour
    for f in fields(new_behaviour):
        setattr(current_behaviour, f.name, getattr(new_behaviour, f.name))

from contextlib import contextmanager

@contextmanager
def change_behaviour():
    global current_behaviour
    saved_behaviour = get_behaviour()
    try:
        yield current_behaviour
    finally:
        set_behaviour(saved_behaviour)

MultiIndex = Tuple[int, ...]

DateLike = Union[dt.date, dt.datetime, np.datetime64, str]
TimeLike = Union[DateLike, dt.timedelta, np.timedelta64]
ValueLike = Union[bool, int, float, str, List, NDArray]

class Flags(enum.Flag):
    CODED     = auto()
    COMPUTED  = auto()
    FACTOR    = auto()
    READ_ONLY = auto()
    BITMAP    = auto()
    SCALAR    = auto()

CODED     = Flags.CODED
COMPUTED  = Flags.COMPUTED
FACTOR    = Flags.FACTOR
READ_ONLY = Flags.READ_ONLY
BITMAP    = Flags.BITMAP
SCALAR    = Flags.SCALAR

FLAGS = dict(coded=CODED, computed=COMPUTED, factor=FACTOR, read_only=READ_ONLY, bitmap=BITMAP)

FlagsLike = Optional[Union[Flags, str, Sequence[str]]]

def ensure_flags(value: FlagsLike) -> Flags:
    if value is None:
        flags = Flags(0)
    elif isinstance(value, Flags):
        flags = value
    elif isinstance(name := value, str):
        try:
            flags = FLAGS[name]
        except KeyError:
            raise ValueError(f"'{name}' is not a valid flag name")
    elif isinstance(value, Sequence):
        names = list(value)
        flags = Flags(0)
        while names:
            name = names.pop()
            try:
                flags |= FLAGS[name]
            except KeyError:
                raise ValueError(f"'{name}' is not a valid flag name")
    else:
        raise TypeError("Invalid type: %s", type(value))
    return flags

@dataclass
class Key:

    name: str
    rank: Optional[int] = None
    primary: str = ""
    secondary: str = ""
    attribute: str = ""
    string: str = ""
    element: Optional[Element] = None
    flags: Flags = CODED

    @staticmethod
    def from_string(string: str):
        name, rank, primary, secondary, attribute = "", None, "", "", ""
        if string.startswith('/'):
            raise NotFoundError(f"{string}: Search keys with the '/<query>/<name>' syntax are not supported yet")
        elif string.startswith('#'):
            second_hash = string.find('#', 2)
            if second_hash == -1:
                raise NotFoundError(f"'{string}': Missing second '#' character")
            rank = int(string[1:second_hash])
            if rank <= 0:
                raise NotFoundError(f"'{string}': Rank must be a positive number")
        else:
            second_hash = -1
        last_arrow = string.rfind('->', -11, -4)
        if last_arrow != -1:
            if string[last_arrow+2:] in ('code', 'units', 'reference', 'scale', 'width'):
                attribute = string[last_arrow+2:]
            else:
                last_arrow = -1
        else:
            last_arrow = len(string)
        first_arrow = string.find('->', second_hash+1, last_arrow)
        if first_arrow != -1:
            secondary = string[first_arrow+2:last_arrow]
        else:
            first_arrow = last_arrow
        primary = string[second_hash+1:first_arrow]
        name = string[second_hash+1:last_arrow]
        key = Key(name, rank, primary, secondary, attribute, string)
        return key

    def __post_init__(self):
        if not self.string:
            if self.rank:
                self.string = f'#{self.rank}#'
            self.string += self.name
            if self.attribute:
                self.string += f'->{self.attribute}'
        if not self.primary:
            self.primary = self.name

@dataclass
class Association:

    element: Element
    element_rank: int
    element_dtype: DTypeLike
    bitmap: NDArray
    bitmap_offset: int
    indices: Dict[str, NDArray]
    slices: Dict[str, slice] = field(init=False, default_factory=dict) # [1]
    entries: Dict[str, 'DataEntry'] = field(init=False, default_factory=dict) # [2]

    # [1] Slices of elements sequence numbers which are within the scope of the bitmap.
    #
    # [2] A dict of secondary/associated entries keyed by the primary group name,.
    #     Only applies to those primary entries where at least one of the ranks is
    #     is set in the bitmap.

    def __post_init__(self) -> None:
        # Consider only those elements that are within the scope
        # of the bitmap.
        for key, indices in self.indices.items():
            bitmap_stop = self.bitmap.size + self.bitmap_offset
            start = numpy.searchsorted(indices >= self.bitmap_offset, True)
            stop = indices.size - numpy.searchsorted(indices[::-1] < bitmap_stop, True)
            self.slices[key] = slice(start, stop)

    def rank_mask(self, key: str):
        """ Returns a mask indicating which ranks of the given primary key have
            an actual associated value.
        """
        slice = self.slices[key]
        indices = self.indices[key] # all
        mask = numpy.repeat(False, len(indices)) # the default for  ranks outside bitmap's scope
        indices = indices[slice]    # only within bitmap's scope
        indices = indices - self.bitmap_offset # relative to bitmap
        mask[slice] = self.bitmap[indices]
        return mask

    def any_rank_set(self, key: str) -> bool:
        """ Returns `True` if any rank of the given primary key has an actual
            associated value.
        """
        try:
            mask = self.rank_mask(key)
        except KeyError: # key was defined *after* the bitmap association
            return False
        return bool(numpy.any(mask))

@dataclass
class DataEntry:

    name: str
    shape: Tuple = ()
    uniform_element: Optional[Element] = None
    elements: List[Element] = field(default_factory=list)
    array: Optional[NDArray] = None
    association: Optional[Association] = None
    primary: Optional['DataEntry'] = None
    flags: Flags = CODED

    @property
    def size(self) -> int:
        assert len(self.shape) == 2
        return self.shape[0] * self.shape[1]

