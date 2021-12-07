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


install_requires = ["numpy"]
if sys.version_info < (3, 7):
    install_requires = ["numpy<1.20"]
elif sys.version_info < (3, 8):
    install_requires = ["numpy<1.22"]

install_requires += ["attrs", "cffi", "findlibs"]

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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
    ],
)
