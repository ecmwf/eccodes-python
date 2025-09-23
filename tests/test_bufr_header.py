# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest as pt

from eccodes.highlevel._bufr.message import *


@pt.fixture(autouse=True)
def fixture(monkeypatch):
    import os

    this_dir = os.path.dirname(__file__)
    monkeypatch.chdir(this_dir)  # always run tests from the tests directory


def test_header_accessors():
    bufr = BUFRMessage(open("./sample-data/synop.bufr"))
    # Make sure we can access header section keys
    assert "localYear" in bufr.header
    bufr.header["localYear"] = 2025
    assert bufr.header["localYear"] == 2025
    # Make sure we can't access data section keys
    assert "year" not in bufr.header
    assert "year->code" not in bufr.header
    assert "year->percentConfidence" not in bufr.header
    assert "year->percentConfidence->code" not in bufr.header
    with pt.raises(KeyValueNotFoundError):
        bufr.header["year"]
    with pt.raises(KeyValueNotFoundError):
        bufr.header["year->code"]
    with pt.raises(KeyValueNotFoundError):
        bufr.header["year->percentConfidence"]
    with pt.raises(KeyValueNotFoundError):
        bufr.header["year->percentConfidence->code"]
    with pt.raises(KeyValueNotFoundError):
        bufr.header["year"] = 2025
    with pt.raises(KeyValueNotFoundError):
        bufr.header["year->percentConfidence"] = 100


def test_header_get_count():
    bufr = BUFRMessage("BUFR3_local")
    assert bufr.get_count("edition") == 1
    with pt.raises(KeyValueNotFoundError):
        bufr.header.get_count("year")
    with pt.raises(KeyValueNotFoundError):
        bufr.header.get_count("#1#year")


def test_header_is_missing():
    bufr = BUFRMessage("BUFR3_local")
    assert not bufr.is_missing("edition")
    with pt.raises(KeyValueNotFoundError):
        bufr.header.is_missing("year")


def test_header_set_missing():
    bufr = BUFRMessage("BUFR3_local")
    with pt.raises(ValueCannotBeMissingError):
        bufr.set_missing("edition")
    with pt.raises(KeyValueNotFoundError):
        bufr.header.set_missing("year")


def test_header_computed_keys():
    bufr = BUFRMessage("BUFR3")
    bufr["typicalDate"] = dt.date(2000, 1, 2)
    bufr["typicalTime"] = dt.time(3, 4)
    assert bufr["typicalDateTime"] == np.datetime64("2000-01-02T03:04")
    assert bufr["typicalDate"] == np.datetime64("2000-01-02")
    assert bufr["typicalTime"] == np.timedelta64(3 * 60 + 4, "m")
    bufr["typicalDate"] = dt.datetime(2000, 1, 2)
    bufr["typicalTime"] = dt.timedelta(hours=3, minutes=4)
    assert bufr["typicalDateTime"] == np.datetime64("2000-01-02T03:04")
    bufr["typicalDate"] = np.datetime64("2000-01-02", "D")
    bufr["typicalTime"] = np.timedelta64(3 * 60 + 4, "m")
    assert bufr["typicalDateTime"] == np.datetime64("2000-01-02T03:04")
    bufr["typicalDate"] = "2000-01-02"
    bufr["typicalTime"] = "03:04"
    assert bufr["typicalDateTime"] == np.datetime64("2000-01-02T03:04")
    with pt.raises(NotFoundError):
        bufr["localDateTime"]
    bufr = BUFRMessage("BUFR3_local")
    bufr["localYear"] = 2000
    bufr["localMonth"] = 1
    bufr["localDay"] = 2
    bufr["localHour"] = 3
    bufr["localMinute"] = 4
    assert bufr["localDateTime"] == np.datetime64("2000-01-02T03:04")
    assert bufr["localDate"] == np.datetime64("2000-01-02")
    assert bufr["localTime"] == np.timedelta64(3 * 60 + 4, "m")
