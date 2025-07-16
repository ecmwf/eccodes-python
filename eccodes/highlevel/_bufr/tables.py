# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import csv
import re

from collections import ChainMap, UserDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

import eccodes


class Code(int):

    def __new__(cls, code: int):
        return int.__new__(cls, code)

    def __repr__(self) -> str:
        return "'%s'" % str(int(self)).zfill(6)

    @property
    def F(self) -> int:
        return int(self) // 100000

    @property
    def X(self) -> int:
        return int(self) // 1000 % 100

    @property
    def Y(self) -> int:
        return int(self) %  1000

    @property
    def FX(self) -> Tuple[int, int]:
        return self.F, self.X

CodeLike = Union[Code, int]

@dataclass
class Descriptor:
    code: Code = 0
    name: str = ''

@dataclass
class Element(Descriptor):
    units: str = ''
    scale: int = 0
    reference: int = 0
    width: int = 0

@dataclass(unsafe_hash=True)
class Version:
    master: int = 0
    local: int = 0
    centre: int = 0
    subcentre: int = 0

class _Singleton(type(UserDict)):

    cache = {}

    def __call__(cls, *args):
        try:
            obj = cls.cache[cls, args]
        except KeyError:
            obj = super().__call__(*args)
            cls.cache[cls, args] = obj
        return obj

class Table(UserDict, metaclass=_Singleton):

    def __init__(self, version: Version, local: bool) -> None:
        base_path = Path(eccodes.codes_definition_path(), 'bufr', 'tables', '0')
        if local:
            dashed_version_number = '%d-%d' % (version.master, version.local)
            path = base_path.joinpath('local', dashed_version_number, str(version.centre), str(version.subcentre))
            if not codes_has_file(path / 'element.table'):
                path = base_path.joinpath('local', str(version.local), str(version.centre), str(version.subcentre))
        else:
            path = base_path.joinpath('wmo', str(version.master))
        self.version = version
        self.path = path
        self.data = {}

class ElementTable(Table):

    def __init__(self, version: Version, local: bool) -> None:
        super().__init__(version, local)
        self.path /= 'element.table'
        try:
            text = codes_read_file(self.path)
        except RuntimeError as e:
            if local:
                return # ignore non-existing local tables
            else:
                raise e
        reader = csv.reader(text.splitlines(), delimiter='|')
        next(reader) # skip header row
        for r in reader:
            c = Code(int(r[0]))
            e = Element(c, r[1], r[4], int(r[5]), int(r[6]), int(r[7]))
            self.data[c] = e

    def __getitem__(self, code: CodeLike) -> Element:
        try:
            return self.data[code]
        except KeyError:
            message = "No such element in tables version %s (%s): %s"
            raise KeyError(message % (self.version, self.path, code))

class SequenceTable(Table):

    def __init__(self, version: Version, local: bool) -> None:
        super().__init__(version, local)
        self.path /= 'sequence.def'
        try:
            text = codes_read_file(self.path)
        except RuntimeError as e:
            if local:
                return # ignore non-existing local tables
            else:
                raise e
        tokens = re.split(']\n?', text)
        tokens = tokens[:-1] # strip the last, empty token
        for token in tokens:
            pair = token.split('= [')
            code = int(pair[0].strip().strip('"'))
            sequence = [Code(c) for c in pair[1].split(',')]
            self.data[code] = sequence

    def __getitem__(self, code: CodeLike) -> List[Code]:
        try:
            return self.data[code]
        except KeyError:
            message = "No such element in tables version %s (%s): %s"
            raise KeyError(message % (self.version, self.path, code))

class CombinedTable(Table):

    def __init__(self, table_class, version):
        self.master  = table_class(version, False)
        self.local   = table_class(version, True)
        self.version = version
        self.data    = ChainMap(self.local.data, self.master.data) # [1]

    # [1] Note that the individual mappings in the ChainMap are searched from first to last.

class Tables:

    def __init__(self, version):
        self.sequences = CombinedTable(SequenceTable, version)
        self.elements  = CombinedTable(ElementTable, version)
        self.version  = version

    def expand_codes(self, code_s: Union[CodeLike, List[CodeLike]], recursive=True) -> Iterator[Code]:
        if isinstance(code_s, int):
            codes = [code_s]
        else:
            codes = code_s
        for c in map(Code, codes):
            if c.F == 3:
                sequence_codes = self.sequences[c]
                if recursive:
                    yield from self.expand_codes(sequence_codes)
                else:
                    yield from sequence_codes
            else:
                yield c

    def expand_descriptors(self, codes_s: Union[CodeLike, List[CodeLike]], recursive=True) -> Iterator[Descriptor]:
        previous_code = Code(0)
        for code in self.expand_codes(codes_s, recursive):
            name = None
            if code.F == 0:
                try:
                    name = self.elements[code].name
                except KeyError as error:
                    if previous_code.FX == (2, 6): # Operator: Signify data width
                        # TODO: raise warning
                        name = ''
                    else:
                        raise error
                previous_code = code
            yield Descriptor(code, name)

import ctypes
import os

libc = ctypes.CDLL(None) # automatically finds and loads the C standard library

fseek = libc.fseek
fseek.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.c_int]
fseek.restype = ctypes.c_int
SEEK_SET, SEEK_END = 0, 2

ftell = libc.ftell
ftell.argtypes = [ctypes.c_void_p]
ftell.restype = ctypes.c_long

fread = libc.fread
fread.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_void_p]
fread.restype = ctypes.c_size_t

fclose = libc.fclose
fclose.argtypes = [ctypes.c_void_p]
fclose.restype = ctypes.c_int

libeccodes = ctypes.CDLL(eccodes.codes_get_library_path())

codes_fopen = libeccodes.codes_fopen
codes_fopen.restype = ctypes.c_void_p

def codes_has_file(path: Union[str, os.PathLike]) -> bool:
    stream = libeccodes.codes_fopen(str(path).encode(), b'r')
    if stream:
        libc.fclose(stream)
        has = True
    else:
        has = False
    return has

def codes_read_file(path: Union[str, os.PathLike]) -> str:
    stream = libeccodes.codes_fopen(str(path).encode(), b'r')
    if not stream:
        raise RuntimeError(f'Tables path does not exist: {path}')
    try:
        fseek(stream, 0, SEEK_END)
        buffer_size = ftell(stream)
        buffer = ctypes.create_string_buffer(buffer_size)
        fseek(stream, 0, SEEK_SET)
        read_size = fread(buffer, ctypes.sizeof(ctypes.c_char), buffer_size, stream)
        string = buffer.raw[:read_size].decode()
    finally:
        fclose(stream)
    return string

