# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from copy import copy
from itertools import repeat

from .common  import *
from .helpers import RaggedArray, SingletonDict
from .tables  import Code, Element

INT_UNITS = re.compile(r'%|.*CODE TABLE.*|.*FLAG TABLE.*|Numeric|a|d|h|min|mon|s')

@dataclass
class Node:
    parent: Any = field(repr=False)
    ordinal: int = 0 # [1]
    level: int = 0 # [2]
    depth: int = 0 # [3]
    children: List = field(default_factory=list)
    starts: Dict[MultiIndex, Counter] = field(default_factory=dict)
    slices: Dict[MultiIndex, slice]   = field(default_factory=dict)
    max_levels: Dict[str, int] = field(default_factory=dict) # [4]

    def __post_init__(self):
        if self.parent:
            self.depth = self.parent.depth + 1

    # [1] Node's (0-based) ordinal number in its parent's list of children.
    #
    # [2] Replication level: leaf node(s) of the outer-most replication have
    #     level=0, in the next inner replication level=1, etc. This level
    #     also corresponds to the `ndim` of the RaggedArray of replication
    #     factors.
    #
    # [3] Distance from the root node. Note that this is not the same as the
    #     (replication) level!
    #
    # [4] A dictionary of the max. (replication) level of each key accessible
    #     from this node. For WrapperNodes this includes keys from all children
    #     subnodes, and their subnotes, transitively. This is used in DataView
    #     objects to infer shapes of the respective array views.

@dataclass
class WrapperNode(Node):
    counts: Dict[MultiIndex, Counter] = field(default_factory=dict)

@dataclass
class ReplicationNode(Node):
    counts: Dict[MultiIndex, Counter] = field(default_factory=dict)
    element: Element = field(default_factory=Element)
    factors: RaggedArray = field(default_factory=RaggedArray.empty)
    reset: bool = True

    def __post_init__(self):
        super().__post_init__();
        self.factors = RaggedArray.empty(self.level)

@dataclass
class LeafNode(Node):
    keys: List[Key] = field(default_factory=list)
    counts: SingletonDict = field(default_factory=SingletonDict)

@dataclass
class AssociationNode(Node):
    operator: int = 0
    reuse_bitmap: bool = False
    for_reuse: bool = False
    bitmap_size: Optional[int] = None
    center: Element = field(default_factory=Element)
    generating_application: Element = field(default_factory=Element)
    code_table: int = 0
    value_factor: Optional[Code] = None
    value_size: Optional[int] = None
    element: Element = field(default_factory=Element)
    bitmap: Optional[NDArray] = None
    bitmap_end: int = 0
    keys: List[Key] = field(default_factory=list)
    counts: Dict[MultiIndex, Counter] = field(default_factory=dict)

def build_tree(coder):
    tables = coder.get_tables()
    operators = {4: []} # key: Code.X, value: a stack of Code.Y values (aka operands)

    def parse(parent, codes, level=0):
        keys = []
        children = []
        change_scale = None
        change_width = None
        while True:
            if not codes:
                if keys:
                    leaf = LeafNode(parent, len(children), level, keys=keys)
                    children.append(leaf)
                break
            next = codes.pop(0)
            # Sequence
            if next.F == 3:
                sequence_codes = list(tables.expand_codes(next, recursive=False))
                codes = sequence_codes + codes
            # Operator: Cancel reuse of bitmap
            elif next == 223255:
                next = codes.pop(0)
            # Operator: Quality information follows
            elif next in (222000, 223000, 224000, 225000):
                if keys:
                    leaf = LeafNode(parent, len(children), level, keys=keys)
                    children.append(leaf)
                    keys = []
                node = AssociationNode(parent, len(children), level, operator=next)
                next = codes.pop(0)
                assert next in [236000, 237000] or next.F == 1
                # Operator: Define bitmap for possible reuse
                if next == 236000:
                    node.for_reuse = True
                    next = codes.pop(0)
                # Process bitmap
                if next != 237000:
                    if next.F == 1: # replication
                        assert next.X == 1 # replicate only one element
                        if next.Y == 0: # delayed replication
                            next = codes.pop(0)
                            assert next.FX == (0, 31) # delayed replication factor
                            element = tables.elements[next]
                            node.keys.append(Key(element.name, element=element, flags=CODED|SCALAR|FACTOR|READ_ONLY))
                        else: # fixed replication
                            node.bitmap_size = next.Y
                        next = codes.pop(0)
                    else: # no replication
                        node.bitmap_size = 1
                    assert next == 31031 # dataPresentIndicator
                    element = tables.elements[next]
                    # TODO node.keys.append(Key(element.name, element=element, flags=CODED|BITMAP|READ_ONLY))
                # Operator: Reuse bitmap
                else:
                    node.reuse_bitmap = True
                # The next element is expected to be 'centre'
                next = codes.pop(0)
                element = tables.elements[next]
                assert element.name == 'centre'
                node.center = element
                node.keys.append(Key(element.name, element=element, flags=CODED))
                # The next elements are expected to be 'generatingApplication'
                # Note that the generalApplication element can show up in
                # the local table too (e.g. 001201 from local/1/98/0).
                next = codes.pop(0)
                element = tables.elements[next]
                assert element.name == 'generatingApplication'
                node.generating_application = element
                node.keys.append(Key(element.name, element=element, flags=CODED))
                next = codes.pop(0)
                # Class 8 element (optional)
                if next.X == 8:
                    node.code_table = next
                    element = tables.elements[next]
                    node.keys.append(Key(element.name, element=element, flags=CODED))
                    next = codes.pop(0)
                # Process the actual quality element (e.g. percentConfidence)
                if next.F == 1: # replication
                    assert next.X == 1 # replicate only one element
                    if next.Y == 0: # delayed replication
                        next = codes.pop(0)
                        node.value_factor = next
                        assert next.FX == (0, 31) # delayed replication factor
                        element = tables.elements[next]
                        node.keys.append(Key(element.name, element=element, flags=CODED|SCALAR|FACTOR|READ_ONLY))
                    else: # fixed replication
                        node.value_size = next.Y
                    next = codes.pop(0)
                else: # no replication
                    pass
                if node.operator == 222000:
                    assert next.FX == (0, 33) # expecting Class 33 element
                    node.element = tables.elements[next]
                else:
                    if node.operator == 223000:
                        assert next == 223255
                        name = 'substitutedValue'
                    elif node.operator == 224000:
                        assert next == 224255
                        name = 'firstOrderStatisticalValue'
                    elif node.operator == 225000:
                        assert next == 225255
                        name = 'differenceStatisticalValue'
                    node.element = Element(next, name, '', 0, 0, 0)
                # When there is no prior replication, the associated element can
                # appear two or more times (aka "inlined" replication).
                if not node.value_factor and node.value_size is None:
                    node.value_size = 1
                    while codes and codes[0] == node.element.code:
                        next = codes.pop(0)
                        node.value_size += 1
                children.append(node)
            # Operator
            elif next.F == 2:
                # Operator: Change width
                if next.X == 1:
                    if next.Y > 0:
                        change_width = next.Y - 128
                    else:
                        change_width = None
                # Operator: Change scale
                if next.X == 2:
                    if next.Y > 0:
                        change_scale = next.Y - 128
                    else:
                        change_scale = None
                # Operator: Add associated field
                elif next.X == 4:
                    if next.Y > 0:
                        if codes[0] != 31021: # Associated field significance
                            # TODO: malformed message: raise warning
                            operators[4].append(8)
                        else:
                            next = codes.pop(0)
                            operators[4].append(next.Y)
                    else:
                        operators[4].pop()
                # Operator: Signify data width for the following local descriptor
                elif next.X == 6:
                    if codes[0] not in tables.elements:
                        codes.pop(0)
            # Replication
            elif next.F == 1:
                span  = next.X
                # Delayed replication
                if next.Y == 0:
                    next = codes.pop(0)
                    assert next.FX == (0, 31) and next.Y in (0, 1, 2, 11, 12) # delayed repl. factor
                    element = tables.elements[next]
                    key = Key(element.name, element=element, flags=CODED|SCALAR|FACTOR|READ_ONLY)
                    keys.append(key)
                    leaf = LeafNode(parent, len(children), level, keys=keys)
                    children.append(leaf)
                    wrapper = WrapperNode(parent, len(children), level)
                    replication = ReplicationNode(wrapper, 0, level, element=element)
                    wrapper.children.append(replication)
                    parse(replication, codes[:span], level + 1)
                    children.append(wrapper)
                    codes = codes[span:]
                    keys = []
                # Fixed replication
                else:
                    assert next.X <= len(codes)
                    codes = codes[:next.X] * next.Y + codes[next.X:]
            # Element
            elif next.F == 0:
                element = tables.elements[next]
                if change_width or change_scale:
                    element = copy(element)
                    if change_width:
                        element.width += change_width
                    if change_scale:
                        element.scale += change_scale
                key = Key(element.name, element=element)
                keys.append(key)
                # Append associated field keys
                for Y in operators[4]:
                    name = f'{element.name}->associatedField'
                    key = Key(name, element=Element(0, name, 'associated units', 0, 0, 2))
                    keys.append(key)
                    name = f'{name}->associatedFieldSignificance'
                    key = Key(name, element=tables.elements[31021])
                    keys.append(key)
            else:
                assert False
        parent.children = children

    # Parse (unexpanded) descriptors

    codes = coder.get('unexpandedDescriptors')
    codes = [Code(c) for c in codes.tolist()]
    subset_count = coder.get('numberOfSubsets')
    compressed = coder.get('compressedData')
    root = WrapperNode(parent=None)

    if compressed or subset_count == 1:
        parse(root, codes)
    else:
        for ordinal in range(subset_count):
            node = WrapperNode(root, ordinal)
            parse(node, codes.copy())
            root.children.append(node)

    # Assign (delayed replication) factors

    global_factors = coder.get_delayed_replication_factors()

    def assign_factors(root: Node, global_factors: Dict[int, NDArray]) -> None:
        counter = Counter()
        def recurse(node, index):
            if isinstance(node, WrapperNode):
                for child in node.children:
                    recurse(child, index)
            elif isinstance(node, ReplicationNode):
                assert len(index) == node.level
                code = node.element.code
                at = counter[code]
                counter[code] += 1
                factor = global_factors[code][at]
                node.factors.insert(index, factor)
                for i in range(factor):
                    for child in node.children:
                        recurse(child, index + (i,))
            elif isinstance(node, LeafNode):
                pass
            elif isinstance(node, AssociationNode):
                assert node.level == 0
                if node.reuse_bitmap:
                    pass
                else:
                    if node.bitmap_size is None:
                        code = node.keys[0].element.code
                        assert code.FX == (0, 31)
                        at = counter[code]
                        counter[code] += 1
                        node.bitmap_size = global_factors[code][at]
                if node.value_size is None: 
                    code = node.value_factor
                    assert code.FX == (0, 31)
                    at = counter[code]
                    counter[code] += 1
                    node.value_size = global_factors[code][at]
            else:
                assert False
        recurse(root, ())
        for code, count in counter.items():
            if (remaining := len(global_factors[code]) - count):
                raise RuntimeError(f'There are {remaining} unprocessed replication factors')

    assign_factors(root, global_factors)

    # Make entries

    def make_entries(root: Node) -> Dict[str, DataEntry]:
        entries: Dict[str, DataEntry] = {}
        def recurse(node):
            if isinstance(node, (WrapperNode, ReplicationNode)):
                for child in node.children:
                    recurse(child)
            elif isinstance(node, (LeafNode, AssociationNode)):
                for key in node.keys:
                    try:
                        entry = entries[key.name]
                    except:
                        entry = DataEntry(key.name, flags=key.flags)
                        if entry.name in current_behaviour.assumed_scalar_elements:
                            entry.flags |= SCALAR
                        entry.uniform_element = key.element
                        entries[entry.name] = entry
                    else:
                        if entry.uniform_element:
                            if entry.uniform_element != key.element:
                                entry.uniform_element = None
            else:
                assert False
        recurse(root)
        return entries

    entries = make_entries(root)

    for code, array in global_factors.items():
        element = tables.elements[code]
        entry = entries[element.name]
        entry.shape = (array.size, 1)
        entry.array = np.reshape(array, entry.shape)

    # Assign bitmaps

    global_bitmap = coder.get_bitmap()

    def assign_bitmaps(root: Node, global_bitmap: NDArray) -> None:
        bitmap_for_reuse = None
        global_bitmap = copy(global_bitmap) # parameter must be copied to be used as nonlocal
        for node in root.children:
            if not isinstance(node, AssociationNode):
                continue
            if node.reuse_bitmap:
                assert bitmap_for_reuse is not None
                node.bitmap = bitmap_for_reuse
            else:
                node.bitmap = global_bitmap[:node.bitmap_size]
                global_bitmap = global_bitmap[node.bitmap_size:]
                if node.for_reuse:
                    bitmap_for_reuse = node.bitmap
            assert node.bitmap is not None
            bitmap_count = numpy.count_nonzero(node.bitmap)
            assert node.value_size is not None
            if node.value_size > bitmap_count:
                # Although incorrect, assuming we can access bitmap_count
                # associated keys this shouldn't be a problem.
                pass
                # TODO: Issue a warning?
            elif node.value_size < bitmap_count:
                indices = numpy.arange(node.bitmap.size)
                cutoff = indices[node.bitmap][node.value_size]
                node.bitmap[cutoff:] = False
                # TODO: Maybe print a warning?

    assign_bitmaps(root, global_bitmap)

    # Resovle elements' (0-based) indices

    def resolve_indices(root: Node) -> Tuple[Dict[str, NDArray], int]:
        def extend(this, other):
            for k, v in other.items():
                this[k].extend(v)
            return this
        def recurse(node, counter, index):
            indices = defaultdict(list)
            if isinstance(node, WrapperNode):
                for child in node.children:
                    child_indices, counter = recurse(child, counter, index)
                    indices = extend(indices, child_indices)
            elif isinstance(node, ReplicationNode):
                assert node.level == len(index)
                for i in range(node.factors[index]):
                    for child in node.children:
                        child_indices, counter = recurse(child, counter, index + (i,))
                        indices = extend(indices, child_indices)
            elif isinstance(node, LeafNode):
                for k in node.keys:
                    indices[k.name].append(counter)
                    counter += 1
            elif isinstance(node, AssociationNode):
                node.bitmap_end = counter
            else:
                assert False
            return indices, counter
        indices, counter = recurse(root, 0, ())
        indices = {k: numpy.array(v) for k, v in indices.items()}
        return indices, counter

    if len(global_bitmap) > 0:
        indices, next_index = resolve_indices(root)

    # Make associations

    def make_associations(root: Node) -> Dict[Tuple[str, int], Association]:
        ranks = Counter()
        associations = {}
        for node in root.children:
            if not isinstance(node, AssociationNode):
                continue
            dtype: DTypeLike = numpy.dtype(float)
            if node.operator == 222000:
                e = node.element
                if e.scale == 0 and INT_UNITS.match(e.units):
                    dtype = numpy.dtype(int)
            ranks[node.element.name] += 1
            rank = ranks[node.element.name]
            assert node.bitmap is not None
            bitmap_offset = node.bitmap_end - len(node.bitmap)
            a = Association(node.element, rank, dtype, node.bitmap, bitmap_offset, indices)
            associations[node.element.name, rank] = a
        return associations

    associations = make_associations(root)

    # Do we still need this? TODO
    bitmap_nodes = [(i, c) for i, c in enumerate(root.children) if isinstance(c, AssociationNode)]
    if bitmap_nodes:
        for i, node in reversed(bitmap_nodes):
            for element in (node.center, node.generating_application):
                if element.name not in indices:
                    indices[element.name] = numpy.array([next_index])
                else:
                    indices[element.name] = numpy.append(indices[element.name], next_index)
                next_index += 1

    # Append associated entries

    for a in associations.values():
        for pg in list(entries.values()):
            a_name = '->'.join(repeat(a.element.name, a.element_rank))
            # if pg.flags & SCALAR:
            #     continue # TODO: are there cases where 'center' and 'originatingApplication' appear outside of bitmap sequence?
            if a.any_rank_set(pg.name):
                name = f'{pg.name}->{a_name}'
                ag = DataEntry(name, association=a, primary=pg)
                ag.flags = pg.flags
                if pg.uniform_element:
                    if a.element.code.FX != (0, 33):
                        ag.uniform_element = copy(a.element)
                        ag.uniform_element.units = pg.uniform_element.units
                    else:
                        ag.uniform_element = a.element
                entries[name] = ag
                a.entries[pg.name] = ag

    # Insert associated keys

    def insert_associated_keys(root: Node, associations) -> None:
        def recurse(node, associated):
            if isinstance(node, (WrapperNode, ReplicationNode)):
                for child in node.children:
                    recurse(child, associated)
            elif isinstance(node, LeafNode):
                name_suffix = '->'.join(repeat(associated.element.name, associated.element_rank))
                copy_units = associated.element.code.FX != (0, 33)
                keys = []
                for key in node.keys:
                    keys.append(key)
                    if key.name in associated.entries:
                        if copy_units:
                            element = copy(associated.element)
                            assert key.element
                            element.units = key.element.units
                        else:
                            element = associated.element
                        key = Key(f'{key.name}->{name_suffix}', secondary=name_suffix, element=element)
                        keys.append(key)
                node.keys = keys
            elif isinstance(node, AssociationNode):
                pass
            else:
                assert False
        for each in associations:
            recurse(root, each)

    insert_associated_keys(root, associations.values())

    # Resolve max. replication levels

    def resolve_max_levels(node: Node) -> None:
        if isinstance(node, (WrapperNode, ReplicationNode)):
            for child in node.children:
                resolve_max_levels(child)
                for name, child_max_level in child.max_levels.items():
                    max_level = node.max_levels.get(name, 0)
                    node.max_levels[name] = max(max_level, child_max_level)
        elif isinstance(node, (LeafNode, AssociationNode)):
            for key in node.keys:
                node.max_levels[key.name] = node.level
        else:
            assert False

    resolve_max_levels(root)

    # Return

    return root, entries, associations

