#!/usr/bin/env python
#
# (C) Copyright 2017- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.

import importlib.metadata
import io
import os
import re
import sys

import setuptools
from wheel.bdist_wheel import bdist_wheel

install_requires = [
    "numpy<1.20 ; python_version < '3.7'",
    "numpy<1.22 ; python_version >= '3.7' and python_version < '3.8'",
    "numpy<1.25 ; python_version >= '3.8' and python_version < '3.9'",
    "numpy ; python_version >= '3.9'",
    "attrs",
    "cffi",
    "findlibs>=0.1.1",
    'eccodeslib ; platform_system!="Windows"',
]

if os.environ.get("LIBDIR", None):
    ext_modules = [
        setuptools.Extension(
            "eccodes._eccodes",
            sources=["eccodes/_eccodes.cc"],
            language="c++",
            libraries=["eccodes"],
            library_dirs=[os.environ["LIBDIR"]],
            include_dirs=[os.environ["INCDIR"]],
        )
    ]
else:
    # NOTE this hack is due to downstream CI not yet supporting building
    ext_modules = []


def get_version() -> str:
    version_pattern = (
        r"^__version__ = [\"\'](.*)[\"\']"  # More permissive regex pattern
    )
    file_path = os.path.join(os.path.dirname(__file__), "gribapi", "bindings.py")
    version_file = io.open(file_path, encoding="utf-8").read()
    version_match = re.search(version_pattern, version_file, re.M)
    if version_match is None or len(version_match.groups()) > 1:
        raise ValueError("couldn't parse version")
    return version_match.group(1)


def get_eccodeslib_dep() -> list[str]:
    try:
        eccodes_version = importlib.metadata.version("eccodeslib")
        mj, mn, pt = eccodes_version.split(".", 2)
        return [
            f"eccodeslib >= {eccodes_version}, < {int(mj)+1}",
        ]
    except importlib.metadata.PackageNotFoundError:
        return []


class bdist_wheel_ext(bdist_wheel):
    # cf wheelmaker setup.py for explanation
    def get_tag(self):
        python, abi, plat = bdist_wheel.get_tag(self)
        return python, abi, "manylinux_2_28_x86_64"


ext_kwargs = {
    "darwin": {},
    "linux": {"cmdclass": {"bdist_wheel": bdist_wheel_ext}},
}

setuptools.setup(
    name="eccodes",
    version=get_version(),
    packages=setuptools.find_packages(),
    package_data={"": ["**/*.h"]},
    install_requires=get_eccodeslib_dep() + install_requires,
    zip_safe=True,
    keywords="ecCodes GRIB BUFR",
    ext_modules=ext_modules,
    **ext_kwargs[sys.platform],
)
