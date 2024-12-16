# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# TODO ideally merge this with wheelmaker's setup_utils somehow

import io
import os
import re
import sys
import setuptools
from setup_utils import parse_dependencies, ext_kwargs


install_requires = [
    "numpy<1.20 ; python_version < '3.7'",
    "numpy<1.22 ; python_version >= '3.7' and python_version < '3.8'",
    "numpy<1.25 ; python_version >= '3.8' and python_version < '3.9'",
    "numpy ; python_version >= '3.9'",
    "attrs",
    "cffi",
    "findlibs", # TODO add lb here once released
]

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

setuptools.setup(
    name="eccodes",
    version=get_version(),
    packages=setuptools.find_packages(),
    package_data={"": ["**/*.h"]},
    install_requires=parse_dependencies() + install_requires,
    **ext_kwargs[sys.platform],
    # NOTE what is this? Setuptools 75.6.0 doesnt recognize. Move to extras?
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
        "Programming Language :: Python :: 3.8",
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
