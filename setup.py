#!/usr/bin/env python
#
# Copyright 2017-2019 European Centre for Medium-Range Weather Forecasts (ECMWF).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import os
import re

import setuptools


def read(path):
    file_path = os.path.join(os.path.dirname(__file__), *path.split('/'))
    return io.open(file_path, encoding='utf-8').read()


# single-sourcing the package version using method 1 of:
#   https://packaging.python.org/guides/single-sourcing-package-version/
def parse_version_from(path):
    version_file = read(path)
    version_match = re.search(r"^__version__ = '(.*)'", version_file, re.M)
    if version_match is None or len(version_match.groups()) > 1:
        raise ValueError("couldn't parse version")
    return version_match.group(1)


setuptools.setup(
    name='eccodes-python',
    version=parse_version_from('gribapi/bindings.py'),
    description='Python interface to the ecCodes BUFR and GRIB de/encoder.',
    long_description=read('README.rst') + read('CHANGELOG.rst'),
    author='European Centre for Medium-Range Weather Forecasts (ECMWF)',
    author_email='software.support@ecmwf.int',
    license='Apache License Version 2.0',
    url='https://github.com/ecmwf/eccodes-python',
    packages=setuptools.find_packages(),
    include_package_data=True,
    # Uncomment to enable CFFI API level, out-of-line mode
    # setup_requires=["cffi>=1.0.0"],
    # cffi_modules=["builder.py:ffibuilder"],
    install_requires=[
        'attrs',
        'cffi',
        'numpy',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'pytest-flakes',
    ],
    test_suite='tests',
    zip_safe=True,
    keywords='eccodes GRIB',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
    ],
)
