# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from functools import cached_property

from .coder import Coder
from .common import *
from .helpers import ensure_masked_array, flatten, missing_of
from .tree import (
    AssociationNode,
    LeafNode,
    Node,
    ReplicationNode,
    WrapperNode,
    build_tree,
)
from .view import View

# flake8: noqa: F405
#   ruff: noqa: F403


class Data(View):
    _coder: Coder
    _subset_count: int = 0
    _compressed: bool = False
    _entries: Dict[str, DataEntry]
    _associations: Dict[Tuple[str, int], Association]

    def __init__(self, coder: Coder) -> None:
        self._coder = coder
        self._entries = {}

    def __contains__(self, key: str) -> bool:
        return self._top_view.__contains__(key)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Data):
            eq = self._top_view.__eq__(other._top_view)
        else:
            eq = False
        return eq

    def __getitem__(self, subscript: Union[int, str]) -> Union["DataBlock", ValueLike]:
        return self._top_view.__getitem__(subscript)

    def __iter__(self) -> Iterator["DataBlock"]:
        yield from self._top_view.__iter__()

    def __len__(self) -> int:
        return self._top_view.__len__()

    def __setitem__(self, key: str, value: ValueLike) -> None:
        return self._top_view.__setitem__(key, value)

    def __str__(self) -> str:
        return self._top_view.__str__()

    def as_dict(self, ranked=False, depth=0, **kwds) -> Dict:
        """Returns dict-like representation of the data section items."""
        return self._top_view.as_dict(ranked, depth, **kwds)

    def copy_to(self, other: "Data") -> None:
        """Copies common keys/values in this data section to `other`."""
        self._coder.unpack()
        self._commit()
        codes_bufr_copy_data(self._coder._handle, other._coder._handle)
        # Workaround for ECC-2022
        self._top_view  # [1]
        for a in self._associations.values():
            if a.element_rank > 1:
                for g in a.entries.values():
                    other[g.name][:] = self[g.name][:]

        # [1] This ensures that we have built all bitmap associations.

    def get_count(self, key: str) -> int:
        """Returns the number of ranked items designated by the given key."""
        return self._top_view.get_count(key)

    def get_shape(self, key: str) -> Tuple[int, ...]:
        return self._top_view.get_shape(key)

    def get_size(self, key: str) -> int:
        return self._top_view.get_size(key)

    def is_missing(self, key: str) -> bool:
        return self._top_view.is_missing(key)

    def items(self, ranked=False, **kwds) -> Iterator[Tuple[str, ValueLike]]:
        yield from self._top_view.items(ranked, **kwds)

    def keys(self, ranked=False, **kwds) -> Iterator[str]:
        yield from self._top_view.keys(ranked, **kwds)

    def set(self, key: str, value: ValueLike) -> None:
        self._top_view.set(key, value)

    def set_missing(self, key: str) -> None:
        self._top_view.set_missing(key)

    def _commit(self) -> None:
        for entry in self._entries.values():
            if entry.array is None or entry.flags & (READ_ONLY | COMPUTED):
                continue
            else:
                self._coder.commit(entry)
                entry.array = None

    @cached_property
    def _top_view(self):
        self._subset_count = cast(int, self._coder.get("numberOfSubsets"))
        self._compressed = cast(bool, self._coder.get("compressedData"))
        root, self._entries, self._associations = build_tree(self._coder)  # [1]
        top_level = ()
        top_view = DataBlock(self, root, top_level)
        for entry in self._entries.values():
            try:
                slice = top_view._slices[entry.name]
            except KeyError:
                continue
            if entry.association:
                entry.shape = entry.primary.shape
            elif entry.flags & SCALAR:
                entry.shape = (slice.stop, 1)
                if entry.flags & FACTOR:
                    assert entry.array is not None  # [2]
            elif entry.flags & BITMAP:
                entry.shape = (slice.stop, None)  # [3]
            else:
                if self._compressed:
                    entry.shape = (slice.stop, self._subset_count)
                else:
                    entry.shape = (slice.stop,)
        self._coder._baked_template = True
        self._coder._subset_count = self._subset_count
        self._coder._compressed = self._compressed
        return top_view

        # [1] Note that it's the call to build_tree() which triggers unpacking!
        #     Because _top_view() is a cached property (and thus initialized lazily)
        #     the unpacking will be defered until when actually needed.
        #
        # [2] Note that arrays of delayed replication factors are constructed in build_tree().
        #
        # [3] At the moment the size of bitmap arrays is determined in Coder.checkout().
        #     Is there a way to infer it earlier? TODO


class DataBlock(View):
    def __init__(self, data: Data, node, index: MultiIndex) -> None:
        self._data: Data = data
        self._node = node
        self._index: MultiIndex = index
        self._slices: Dict[str, slice] = resolve_slices(node, index)
        self._sub_blocks: Dict[int, "DataBlock"] = {}

    def __contains__(self, subscript: str) -> bool:
        key = Key.from_string(subscript)
        try:
            entry = self._get_entry(key)
        except NotFoundError:
            contains = False
        else:
            if key.rank:
                slice = self._slices[entry.name]
                contains = key.rank <= slice.stop
            else:
                contains = True
        return contains

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DataBlock):
            eq = False
            for (k1, v1), (k2, v2) in zip(self.items(), other.items()):
                if k1 != k2:
                    break
                if isinstance(v1, np.ndarray):
                    if not isinstance(v2, np.ndarray):
                        break
                    if v1.dtype.type == np.str_:
                        if not v2.dtype.type == np.str_:
                            break
                        if not np.char.compare_chararrays(v1, v2, "==", rstrip=True):
                            break
                    else:
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

    def __len__(self) -> int:
        node = self._node
        if isinstance(node, AssociationNode):
            # Has no children. Should we add an empty list? TODO
            return 0
        elif node.children and isinstance(node.children[0], ReplicationNode):
            assert len(node.children) == 1
            replication = node.children[0]
            return replication.factors[self._index]
        else:
            return len(node.children)

    def __iter__(self) -> Iterator["DataBlock"]:
        node = self._node
        if node.children and isinstance(node.children[0], ReplicationNode):
            assert len(node.children) == 1
            replication = node.children[0]
            for factor in range(replication.factors[self._index]):
                index = self._index + (factor,)
                if len(replication.children) == 1 and isinstance(
                    replication.children[0], LeafNode
                ):
                    block = DataBlock(self._data, replication.children[0], index)
                else:
                    block = DataBlock(self._data, replication, index)
                yield block
        else:
            for child in node.children:
                yield DataBlock(self._data, child, self._index)

    def __getitem__(self, subscript: Union[int, str]) -> Union["DataBlock", ValueLike]:
        if isinstance(subscript, str):
            key = Key.from_string(subscript)
            entry = self._get_entry(key)
            sub = self._get_subscript(entry, key)
            if key.attribute:
                if entry.uniform_element:
                    value = getattr(entry.uniform_element, key.attribute)
                else:
                    if not entry.elements:
                        resolve_elements(
                            self._data._entries, self._data._top_view._node
                        )
                        assert entry.elements
                    if isinstance(sub, slice):
                        value = [getattr(e, key.attribute) for e in entry.elements[sub]]
                    else:
                        value = getattr(entry.elements[sub], key.attribute)
            else:
                array = self._get_array(entry)
                value = array[sub]
            return value
        elif type(ordinal := subscript) is int:
            node = self._node
            if node.children and isinstance(node.children[0], ReplicationNode):
                assert len(node.children) == 1
                replication = node.children[0]
                factor = replication.factors[self._index]
                ordinal = factor + ordinal if ordinal < 0 else ordinal
                if ordinal < 0 or ordinal >= factor:
                    raise IndexError(f"Subscript out of range: {subscript}")
                try:
                    block = self._sub_blocks[ordinal]
                except KeyError:
                    index = self._index + (ordinal,)
                    if len(replication.children) == 1 and isinstance(
                        replication.children[0], LeafNode
                    ):
                        block = DataBlock(self._data, replication.children[0], index)
                    else:
                        block = DataBlock(self._data, replication, index)
                    self._sub_blocks[ordinal] = block
            else:
                ordinal = len(node.children) + ordinal if ordinal < 0 else ordinal
                if ordinal < 0 or ordinal >= len(node.children):
                    raise IndexError(f"Subscript out of range: {subscript}")
                try:
                    block = self._sub_blocks[ordinal]
                except KeyError:
                    block = DataBlock(self._data, node.children[ordinal], self._index)
                    self._sub_blocks[ordinal] = block
            return block
        else:
            raise TypeError(
                "subscript must be either 'int' or 'str'; got %s" % type(subscript)
            )

    def __setitem__(self, key: str, value: ValueLike) -> None:
        key = Key.from_string(key)
        value = ensure_masked_array(value)
        entry = self._get_entry(key)
        if entry.flags & READ_ONLY or key.attribute:
            raise ReadOnlyError(f"{key.string}")
        array = self._get_array(entry)
        subscript = self._get_subscript(entry, key)
        if isinstance(subscript, slice):
            array[subscript] = value
        else:
            array[subscript : subscript + 1] = value

    def __str__(self) -> str:
        import pprint

        d = self.as_dict()
        return pprint.pformat(d, sort_dicts=False)

    def as_dict(self, ranked=False, depth=0, **kwds) -> Dict:
        """Returns dict-like representation of the DataBlock items."""
        if self._node.depth < depth and len(self) > 0:
            d = {}
            for i, block in enumerate(self):
                # block = cast('DataBlock', self[i])
                d[i] = block.as_dict(ranked, depth, **kwds)
        else:
            counts_only = kwds.pop("counts_only", False)
            shapes_only = kwds.pop("shapes_only", False)
            if counts_only:
                d = {k: self.get_count(k) for k in self.keys(ranked, **kwds)}
            elif shapes_only:
                d = {k: self.get_shape(k) for k in self.keys(ranked, **kwds)}
            else:
                d = dict(self.items(ranked, **kwds))
        return d

    def get_count(self, key: str) -> int:
        """Returns the number of elements designated by the given key."""
        key = Key.from_string(key)
        try:
            slice = self._slices[key.name]
        except KeyError:
            raise NotFoundError(key.string)
        else:
            rank_count = slice.stop - slice.start
            if key.rank:
                if key.rank <= rank_count:
                    count = 1
                else:
                    raise NotFoundError(key.string)
            else:
                count = rank_count
        return count

    def get_shape(self, key: str) -> Tuple[int, ...]:
        key = Key.from_string(key)
        entry = self._get_entry(key)
        subscript = self._get_subscript(entry, key)
        if isinstance(subscript, slice):
            shape = (subscript.stop - subscript.start,)
        else:
            shape = ()
        if key.attribute:
            if entry.uniform_element:
                shape = ()
        elif self._data._compressed and not entry.flags & Flags.SCALAR:
            shape += (self._data._subset_count,)
        return shape

    def get_size(self, key: str) -> int:
        shape = self.get_shape(key)
        size = 1
        for dim in shape:
            size *= dim
        return size

    def is_missing(self, key: str) -> bool:
        key = Key.from_string(key)
        if key.attribute:
            is_missing = False
        else:
            entry = self._get_entry(key)
            slice = self._get_slice(entry, key)
            if entry.array is None:
                is_missing = self._data._coder.is_missing(entry, slice)
            else:
                array = self._get_array(entry)
                array_view = array[slice]
                is_missing = np.all(array_view.mask)
        return is_missing

    def set(self, key: str, value: ValueLike) -> None:
        self.__setitem__(self, key, value)

    def set_missing(self, key: str) -> None:
        key = Key.from_string(key)
        if key.attribute:
            raise ValueCannotBeMissingError(
                f"Attribute '{key.string}' can't have missing value"
            )
        else:
            entry = self._get_entry(key)
            slice = self._get_slice(entry, key)
            if entry.array is None:
                self._data._coder.set_missing(entry, slice)
            else:
                array = self._get_array(entry)
                array_view = array[slice]
                array_view.mask = True

    def items(self, ranked=False, **kwds) -> Iterator[Tuple[str, ValueLike]]:
        for key in self.keys(ranked, **kwds):
            yield key, cast(ValueLike, self[key])

    def keys(self, ranked=False, **kwds) -> Iterator[str]:
        only_flags = ensure_flags(kwds.get("only", Flags.CODED))
        skip_flags = ensure_flags(kwds.get("skip", Flags(0)))
        if ranked:
            ranks = Counter()
            for key in iterate_keys(self._node, self._index):
                ranks[key.name] += 1
                rank = ranks[key.name]
                yield f"#{rank}#{key.name}"
        else:
            for name, slice in self._slices.items():
                if slice.stop <= slice.start:
                    continue  # Ignore keys inside empty replications
                try:
                    entry = self._data._entries[name]
                except KeyError:
                    continue  # Ignore unset associated keys
                if not entry.flags & only_flags:
                    continue
                if entry.flags & skip_flags:
                    continue
                yield name

    def _get_entry(self, key: Key) -> DataEntry:
        try:
            entry = self._data._entries[key.name]
        except KeyError:
            raise NotFoundError(key.string)
        return entry

    def _get_array(self, entry):
        if entry.array is None:
            array = self._data._coder.checkout(entry)
            if not self._data._coder._compressed:  # TODO: correct shape in Coder
                array = array.ravel()
            if array.dtype.type == np.str_ and np.__version__ < "1.24":
                array = np.ma.masked_where(array == "", array, copy=False)  # [1]
                array.fill_value = ""
            else:
                array = np.ma.masked_equal(array, missing_of(array.dtype), copy=False)
            entry.array = array
        if entry.flags & Flags.SCALAR:
            array = entry.array.ravel()
        else:
            array = entry.array
        return array

        # [1] This is a workaround for old versions of numpy where calling masked_equal()
        #     on a string array fails with:
        #     numpy.core._exceptions.UFuncTypeError: ufunc 'equal' did not contain a loop
        #     with signature matching types (dtype('<U64'), dtype('<U64')) -> dtype('bool')

    def _get_subscript(self, entry, key):
        slice = self._get_slice(entry, key)
        slice_len = slice.stop - slice.start
        if key.rank:
            assert slice_len == 1
            subscript = slice.start
        elif slice_len == 1:
            max_level = self._node.max_levels[entry.name]
            if self._node.level == max_level:  # [1]
                subscript = slice.start
            else:
                subscript = slice
        else:
            subscript = slice
        return subscript

        # [1] Make sure we don't flatten single-rank array views unless they are
        #     accessed from the bottom-most DataBlock. This is important because
        #     otherwise shapes of array views could change depending on the values
        #     of replication factors. We want to provide 1d array views only in those
        #     cases where it's guaranteed there is always going to be only one rank for
        #     the given key in the current DataBlock, irrespective of replication
        #     factors.

    def _get_slice(self, entry, key):
        slice_ = self._slices[entry.name]
        if key.rank:
            rank_count = slice_.stop - slice_.start
            if key.rank > rank_count:
                message = (
                    "Rank %d is out of bounds; max. rank of '%s' in this view is %d"
                )
                raise NotFoundError(message % (key.rank, entry.name, rank_count))
            start = slice_.start + key.rank - 1
            slice_ = slice(start, start + 1)
        return slice_


def iterate_keys(node, index: MultiIndex) -> Iterator[Key]:
    """Recursively iterates over keys of `node` and all of its sub-nodes given
    the replication index.
    """
    if isinstance(node, LeafNode):
        yield from node.keys
    elif isinstance(node, ReplicationNode):
        if len(index) == node.factors.ndim + 1:
            for child in node.children:
                yield from iterate_keys(child, index)
        else:
            for i in range(node.factors[index]):
                child_index = index + (i,)
                for child in node.children:
                    yield from iterate_keys(child, child_index)
    elif isinstance(node, WrapperNode):
        for child in node.children:
            yield from iterate_keys(child, index)
    elif isinstance(node, AssociationNode):
        yield from node.keys
    else:
        assert False


def resolve_slices(node, index: MultiIndex) -> Dict[str, slice]:
    """Given the replication index, resolves ranks for each entry in the node."""
    try:
        slices = node.slices[index]
    except KeyError:
        slices = {}
        starts = resolve_starts(node, index)
        counts = resolve_counts(node, index)
        for name, count in counts.items():
            start = starts[name]
            stop = start + count
            slices[name] = slice(start, stop)
        node.slices[index] = slices
    return slices


def resolve_starts(node, index: MultiIndex) -> Counter:
    """Given the replication index, resolves rank starts for each entry in the node."""
    try:
        starts = node.starts[index]
    except KeyError:
        if not node.parent:
            starts = Counter()
        elif not isinstance(node, ReplicationNode):
            if node.ordinal > 0:
                upper_sibling = node.parent.children[node.ordinal - 1]
                starts = resolve_starts(upper_sibling, index).copy()
                counts = resolve_counts(upper_sibling, index)
                starts += counts
            else:
                starts = resolve_starts(node.parent, index)
        else:
            if index[-1] == 0:
                starts = resolve_starts(node.parent, index[:-1])
            else:
                lower_index = index[:-1] + (index[-1] - 1,)
                starts = resolve_starts(node, lower_index).copy()
                counts = resolve_counts(node, lower_index)
                starts += counts
        node.starts[index] = starts
    return starts


def resolve_counts(node, index: MultiIndex) -> Counter:
    """Given the replication index, resolves rank counts for each entry in the node."""
    try:
        counts = node.counts[index]
    except KeyError:
        if isinstance(node, (LeafNode, AssociationNode)):
            counts = Counter((k.name for k in node.keys))
            node.counts[index] = counts
        else:
            counts = Counter()
            for child in node.children:
                counts += resolve_counts(child, index)
            if len(index) == node.level:
                node.counts[index] = counts
    if (
        isinstance(node, LeafNode)
        and isinstance(node.parent, ReplicationNode)
        and len(index) < node.level
    ):
        total_factor = sum(flatten(node.parent.factors[index]))
        counts = counts.copy()
        for name in counts:
            counts[name] *= total_factor
    return counts


def resolve_elements(entries, root: Node):
    """Traverses nodes of the data tree and gathers lists of expanded elements
    for each of the entries.
    """

    def recurse(node, index):
        if isinstance(node, WrapperNode):
            for child in node.children:
                recurse(child, index)
        elif isinstance(node, ReplicationNode):
            assert node.level == len(index)
            for i in range(node.factors[index]):
                for child in node.children:
                    recurse(child, index + (i,))
        elif isinstance(node, (LeafNode, AssociationNode)):
            for key in node.keys:
                try:
                    entry = entries[key.name]
                except KeyError:  # [1]
                    continue
                if not entry.uniform_element:
                    entry.elements.append(key.element)
        else:
            assert False

    recurse(root, index=())

    # [1] Currently we append associated keys for each and every primary key
    #     of the LeafNode, but we add them to entries only if there is at least
    #     one rank covered by the bitmap. Check if this is OK or whether it needs
    #     to be optimized. TODO
