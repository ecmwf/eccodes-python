#!/usr/bin/env python
#
# (C) Copyright 2017- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.
#

import json
import re
import sys

import requests
from html2text import html2text


def identity(x):
    return x


ENTRIES = {
    "libeccodes": {
        "home": "https://github.com/ecmwf/eccodes",
        "copying": "https://raw.githubusercontent.com/ecmwf/eccodes/develop/LICENSE",
    },
    "libpng": {
        "home": "https://github.com/glennrp/libpng",
        "copying": "https://raw.githubusercontent.com/glennrp/libpng/libpng16/LICENSE",
    },
    "libaec": {
        "home": "https://github.com/MathisRosenhauer/libaec",
        "copying": "https://raw.githubusercontent.com/MathisRosenhauer/libaec/master/LICENSE.txt",
    },
    "libjasper": {
        "home": "https://github.com/jasper-software/jasper",
        "copying": "https://raw.githubusercontent.com/jasper-software/jasper/master/LICENSE.txt",
    },
    "libopenjp2": {
        "home": "https://github.com/uclouvain/openjpeg",
        "copying": "https://raw.githubusercontent.com/uclouvain/openjpeg/master/LICENSE",
    },
    "libopenjpeg": {
        "home": "https://code.google.com/archive/p/openjpeg/",
        "copying": "https://raw.githubusercontent.com/uclouvain/openjpeg/master/LICENSE",
    },
    "libjpeg": {
        "home": "http://ijg.org",
        "copying": "https://jpegclub.org/reference/libjpeg-license/",
        "html": True,
    },
}

PATTERNS = {
    r"^libpng\d+$": "libpng",
    r"^libproj(_\d+)+$": "libproj",
}

ALIASES = {
    "libeccodes_memfs": "libeccodes",
}

if False:
    for e in ENTRIES.values():
        if isinstance(e, dict):
            copying = e["copying"]
            if copying.startswith("http"):
                requests.head(copying).raise_for_status()

libs = {}
missing = []
seen = set()

for line in open(sys.argv[1], "r"):  # noqa: C901
    lib = "-no-regex-"
    lib = line.strip().split("/")[-1]
    lib = lib.split("-")[0].split(".")[0]

    if lib == "":
        continue

    if not lib.startswith("lib"):
        lib = f"lib{lib}"

    for k, v in PATTERNS.items():
        if re.match(k, lib):
            lib = v

    lib = ALIASES.get(lib, lib)

    if lib not in ENTRIES:
        missing.append((lib, line))
        continue

    if lib in seen:
        continue

    seen.add(lib)

    e = ENTRIES[lib]
    if e is None:
        continue

    libs[lib] = dict(path=f"copying/{lib}.txt", home=e["home"])
    copying = e["copying"]

    filtering = identity
    if e.get("html"):
        filtering = html2text

    with open(f"eccodes/copying/{lib}.txt", "w") as f:
        if copying.startswith("http://") or copying.startswith("https://"):
            r = requests.get(copying)
            r.raise_for_status()
            for n in filtering(r.text).split("\n"):
                print(n, file=f)
        else:
            for n in copying.split("\n"):
                print(n, file=f)

    with open("eccodes/copying/list.json", "w") as f:
        print(json.dumps(libs), file=f)


assert len(missing) == 0, json.dumps(missing, indent=4, sort_keys=True)
