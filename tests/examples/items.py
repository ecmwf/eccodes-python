#!/usr/bin/env python3

# Copyright 2005- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# This example shows how to list all items in a BUFR message.
#
# Usage: ./items.py input.bufr

# flake8: noqa: F403
# flake8: noqa: F405

import sys

from eccodes import *
from eccodes.highlevel import *


def run_example(input, output=sys.stdout):
    reader = FileReader(input, CODES_PRODUCT_BUFR)
    for i, message in enumerate(reader, start=1):
        print("messageNumber", i, file=output)
        if message["compressedData"] or message["numberOfSubsets"] == 1:
            for k, v in message.items():
                print(k, v, file=output)
        else:
            for k, v in message.header.items():
                print(k, v, file=output)
            # For uncompressed multi-subset messages, print items one subset at a time. [1]
            for j, subset in enumerate(message.data, start=1):
                print("subsetNumber", j, file=output)
                for k, v in subset.items():
                    print(k, v, file=output)


if __name__ == "__main__":
    run_example(sys.argv[1])

# Footnotes:
#
# [1] This is not stricly necessary but, generally, it's easier to interpret
#     contents of ucompressed messages by looking at individual subsets, especially
#     so when subsets have different replication factors.
