#!/usr/bin/env python3

# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# This example shows how to read key attributes.
#
# Usage: attributes.py input.bufr

import sys

from eccodes import *
from eccodes.highlevel import *

ATTRIBUTES = ['code', 'units', 'scale', 'reference', 'width'] # See BUFR Code Table B

def run_example(input, output=sys.stdout):

    # Loop over the messages in the file
    for number, bufr in enumerate(FileReader(input, CODES_PRODUCT_BUFR), start=1):

        print(f'messageNumber: {number}', file=output)

        # Loop over all keys in the message
        for name in bufr.keys():

            # Print element's attributes. Attributes themselves are keys.
            for attribute in ATTRIBUTES:
                try:
                    key = f'{name}->{attribute}'
                    value = bufr[key]
                    print(f'{key}: {value}', file=output)
                except eccodes.KeyValueNotFoundError:
                    pass

if __name__ == '__main__':
    run_example(sys.argv[1])
