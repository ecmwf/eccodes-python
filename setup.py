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

import setuptools

try:
    from Cython.Distutils import build_ext

    has_cython = True
except ImportError:
    has_cython = False


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


if has_cython:

    class NumpyBuildExtCommand(build_ext):
        """
        build_ext command for use when numpy headers are needed.
        from https://stackoverflow.com/questions/2379898/
        and https://stackoverflow.com/questions/48283503/
        """

        def run(self):
            self.distribution.fetch_build_eggs(["numpy"])
            import numpy

            self.include_dirs.append(numpy.get_include())
            build_ext.run(self)

    cmdclass = {"build_ext": NumpyBuildExtCommand}

    redtoregext = setuptools.Extension(
        "redtoreg", ["eccodes/high_level/redtoreg.pyx"]
    )
    searchdirs = []
    if os.environ.get("ECCODES_DIR"):
        searchdirs.append(os.environ["ECCODES_DIR"])
    if os.environ.get("CONDA_PREFIX"):
        searchdirs.append(os.environ["CONDA_PREFIX"])
    searchdirs += [
        os.path.expanduser("~"),
        "/usr",
        "/usr/local",
        "/opt/local",
        "/opt",
        "/sw",
    ]
    # look for grib_api.h in searchdirs
    eccdir = None
    for d in searchdirs:
        try:
            incpath = os.path.join(os.path.join(d, "include"), "grib_api.h")
            f = open(incpath)
            eccdir = d
            print("eccodes found in %s" % eccdir)
            break
        except IOError:
            continue
    if eccdir is not None:
        incdirs = [os.path.join(eccdir, "include")]
        libdirs = [os.path.join(eccdir, "lib"), os.path.join(eccdir, "lib64")]
    else:
        print("eccodes not found, build may fail...")
        incdirs = []
        libdirs = []
    pygribext = setuptools.Extension(
        "pygrib",
        ["eccodes/high_level/pygrib.pyx"],
        include_dirs=incdirs,
        library_dirs=libdirs,
        runtime_library_dirs=libdirs,
        libraries=["eccodes"],
    )
    ext_modules = [redtoregext, pygribext]
else:  # if cython not installed, don't build C extensions in high-level API
    ext_modules = []
    cmdclass = {}


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
    cmdclass=cmdclass,
    include_package_data=True,
    ext_modules=[redtoregext, pygribext],
    setup_requires=["cython"],
    install_requires=[
        "attrs",
        "cffi",
        "numpy",
    ],
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
    ],
)
