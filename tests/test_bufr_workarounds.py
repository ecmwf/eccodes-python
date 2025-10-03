# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# flake8: noqa: F403
# flake8: noqa: F405
import sys

import numpy as np
import pytest as pt

import eccodes
from eccodes import *
from eccodes.highlevel._bufr import *

if sys.platform.startswith("win32"):
    pt.skip("Not applicable on Windows", allow_module_level=True)


@pt.fixture(autouse=True)
def fixture(monkeypatch):
    import os

    this_dir = os.path.dirname(__file__)
    monkeypatch.chdir(this_dir)  # always run tests from the tests directory


@pt.mark.skipif(
    eccodes.__version__ < "2.41.0",
    reason="requires eccodes 2.41.0; otherwise segfaults (see ECC-2024)",
)
def test_workaround_for_ECC_2015():
    old = BUFRMessage(open("./sample-data/hdob.bufr"))
    old.copy(subsets=[0])
    old.copy(subsets=[1])  # would fail without the workaround


def test_workaround_for_ECC_1624():
    # Consider the following message with operator 222000, and thus the 'centre'
    # key in the data section.
    bufr = BUFRMessage("BUFR3")
    bufr["numberOfSubsets"] = 1
    bufr["compressedData"] = 0
    bufr["unexpandedDescriptors"] = [
        307011,
        7006,
        10004,
        222000,
        101023,
        31031,
        1031,
        1032,
        101023,
        33007,
    ]

    # There should be only one element with key 'centre', and its
    # initial value should be missing.
    assert bufr.get_count("centre") == 1
    assert bufr["centre"] is np.ma.masked

    # Test that setting 'centre' value does the right thing, and doesn't interfere
    # with 'bufrHeaderCentre' from section 1.
    bufr["centre"] = 42
    bufr.pack()
    assert bufr["centre"] == 42
    assert bufr["bufrHeaderCentre"] == 98

    # Test that setting 'centre' on header raises an exception.
    with pt.raises(KeyValueNotFoundError):
        bufr.header["centre"]
    with pt.raises(KeyValueNotFoundError):
        bufr.header["centre"] = 42

    # Now consider a message *without* operator 222000, and thus *no* 'centre'
    # key in the data section.
    bufr = BUFRMessage("BUFR3")
    bufr["numberOfSubsets"] = 1
    bufr["compressedData"] = 0
    bufr["unexpandedDescriptors"] = [307011]

    # Test that setting 'centre' raises an exception.
    with pt.raises(KeyValueNotFoundError):
        bufr["centre"]
    with pt.raises(KeyValueNotFoundError):
        bufr["centre"] = 42


def test_workaround_for_ECC_2098():
    bufr = BUFRMessage("BUFR3")
    bufr["inputDelayedDescriptorReplicationFactor"] = 3
    bufr["unexpandedDescriptors"] = [
        104000,  # Delayed replication of 4 elements
        31001,  # Delayed replication factor
        204001,  # Operator: Add associated field
        31021,  # Associated field significance
        11001,  # Wind speed
        204000,  # Operator: Close associated field
    ]
    bufr["windDirection->associatedField"] = [0, 0, 0]  # OK
    bufr["windDirection->associatedField->associatedFieldSignificance"] = [
        1,
        1,
        1,
    ]  # Would raise ArrayTooSmallError when packing
    bufr.pack()


def test_workaround_for_ECC_2022():
    old = BUFRMessage(open("./sample-data/amv-goes-9.bufr", "rb"))
    new = old.copy()
    old.copy_to(new)
    assert old.data == new.data  # would fail without the workaround
