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

import io
import os
import re
import sys

import setuptools


def read(path):
    file_path = os.path.join(os.path.dirname(__file__), *path.split("/"))
    return io.open(file_path, encoding="utf-8").read()


# single-sourcing the package version using method 1 of:
#   https://packaging.python.org/guides/single-sourcing-package-version/
def parse_version_from(path):
    version_pattern = (
        r"^__version__ = [\"\'](.*)[\"\']"  # More permissive regex pattern
    )
    version_file = read(path)
    version_match = re.search(version_pattern, version_file, re.M)
    if version_match is None or len(version_match.groups()) > 1:
        raise ValueError("couldn't parse version")
    return version_match.group(1)


# for the binary wheel
libdir = os.path.realpath("install/lib")
incdir = os.path.realpath("install/include")
libs = ["eccodes"]

if "--binary-wheel" in sys.argv:
    sys.argv.remove("--binary-wheel")

    # https://setuptools.pypa.io/en/latest/userguide/ext_modules.html
    ext_modules = [
        setuptools.Extension(
            "eccodes._eccodes",
            sources=["eccodes/_eccodes.cc"],
            language="c++",
            libraries=libs,
            library_dirs=[libdir],
            include_dirs=[incdir],
            extra_link_args=["-Wl,-rpath," + libdir],
        )
    ]

    def shared(directory):
        result = []
        for path, dirs, files in os.walk(directory):
            for f in files:
                result.append(os.path.join(path, f))
        return result

    # Paths must be relative to package directory...
    shared_files = ["versions.txt"]
    shared_files += [x[len("eccodes/") :] for x in shared("eccodes/copying")]

    if os.name == "nt":
        for n in os.listdir("eccodes"):
            if n.endswith(".dll"):
                shared_files.append(n)

else:
    ext_modules = []
    shared_files = []


install_requires = ["numpy"]
if sys.version_info < (3, 7):
    install_requires = ["numpy<1.20"]
elif sys.version_info < (3, 8):
    install_requires = ["numpy<1.22"]
elif sys.version_info < (3, 9):
    install_requires = ["numpy<1.25"]

install_requires += [
    "attrs",
    "cffi",
    "findlibs",
    "eccodeslib;platform_system!='Windows'",
]

setuptools.setup(
    name="eccodes",
    version=parse_version_from("gribapi/bindings.py"),
    description="Python interface to the ecCodes GRIB and BUFR decoder/encoder",
    long_description=read("README.rst") + read("CHANGELOG.rst"),
    author="European Centre for Medium-Range Weather Forecasts (ECMWF)",
    author_email="software.support@ecmwf.int",
    license="Apache License Version 2.0",
    url="https://github.com/ecmwf/eccodes-python",
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={"": shared_files},
    install_requires=install_requires,
    tests_require=[
        "pytest",
        "pytest-cov",
        "pytest-flakes",
    ],
    test_suite="tests",
    zip_safe=True,
    keywords="ecCodes GRIB BUFR",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
    ],
    ext_modules=ext_modules,
)
