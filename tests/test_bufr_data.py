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
import warnings

import numpy as np
import pytest as pt

from eccodes import *
from eccodes.highlevel._bufr.message import *

if sys.platform.startswith("win32"):
    pt.skip("Not applicable on Windows", allow_module_level=True)


@pt.fixture(autouse=True)
def fixture(monkeypatch):
    import os

    this_dir = os.path.dirname(__file__)
    monkeypatch.chdir(this_dir)  # always run tests from the tests directory


def test_data_key():
    assert Key.from_string("year") == Key(name="year")
    assert Key.from_string("year->code") == Key(name="year", attribute="code")
    assert Key.from_string("year->units") == Key(name="year", attribute="units")
    assert Key.from_string("year->reference") == Key(name="year", attribute="reference")
    assert Key.from_string("year->scale") == Key(name="year", attribute="scale")
    assert Key.from_string("year->width") == Key(name="year", attribute="width")
    assert Key.from_string("year->percentConfidence") == Key(
        name="year->percentConfidence", primary="year", secondary="percentConfidence"
    )
    assert Key.from_string("year->percentConfidence->code") == Key(
        name="year->percentConfidence",
        primary="year",
        secondary="percentConfidence",
        attribute="code",
    )
    assert Key.from_string("#1#year") == Key(name="year", rank=1)
    assert Key.from_string("#1#year->code") == Key(
        name="year", rank=1, attribute="code"
    )
    assert Key.from_string("#1#year->percentConfidence") == Key(
        name="year->percentConfidence",
        rank=1,
        primary="year",
        secondary="percentConfidence",
    )
    assert Key.from_string("#1#year->percentConfidence->code") == Key(
        name="year->percentConfidence",
        rank=1,
        primary="year",
        secondary="percentConfidence",
        attribute="code",
    )
    assert "year" == Key(name="year").string
    assert "year->code" == Key(name="year", attribute="code").string
    assert "year->units" == Key(name="year", attribute="units").string
    assert "year->reference" == Key(name="year", attribute="reference").string
    assert "year->scale" == Key(name="year", attribute="scale").string
    assert "year->width" == Key(name="year", attribute="width").string
    assert (
        "year->percentConfidence"
        == Key(
            name="year->percentConfidence",
            primary="year",
            secondary="percentConfidence",
        ).string
    )
    assert (
        "year->percentConfidence->code"
        == Key(
            name="year->percentConfidence",
            primary="year",
            secondary="percentConfidence",
            attribute="code",
        ).string
    )
    assert "#1#year" == Key(name="year", rank=1).string
    assert "#1#year->code" == Key(name="year", rank=1, attribute="code").string
    assert (
        "#1#year->percentConfidence"
        == Key(
            name="year->percentConfidence",
            rank=1,
            primary="year",
            secondary="percentConfidence",
        ).string
    )
    assert (
        "#1#year->percentConfidence->code"
        == Key(
            name="year->percentConfidence",
            rank=1,
            primary="year",
            secondary="percentConfidence",
            attribute="code",
        ).string
    )
    with pt.raises(NotFoundError):
        Key.from_string("/pressure=85000/airTemperature")


def test_data_accessors():
    bufr = BUFRMessage(open("./sample-data/synop.bufr"))
    # Header keys (should not be accessible from the Data class)
    assert "edition" not in bufr.data
    with pt.raises(NotFoundError):
        bufr.data["edition"]
    with pt.raises(NotFoundError):
        bufr.data["edition"] = 3
    # Data keys: defined
    assert "year" in bufr.data
    assert "year->code" in bufr.data
    assert "year->percentConfidence" in bufr.data
    assert "year->percentConfidence->code" in bufr.data
    assert "#1#year" in bufr.data
    assert "#1#year->code" in bufr.data
    assert "#1#year->percentConfidence" in bufr.data
    assert "#1#year->percentConfidence->code" in bufr.data
    assert bufr.data["year"] == 2009
    assert bufr.data["year->code"] == 4001
    assert bufr.data["year->percentConfidence"] == 70
    assert np.all(
        bufr.data["cloudAmount"] == np.ma.masked_values([8, -1, -1, -1, -1], -1)
    )
    # assert bufr.data['year->percentConfidence->code'] == TODO
    assert bufr.data["#1#year"] == 2009
    assert bufr.data["#1#year->code"] == 4001
    assert bufr.data["#1#year->percentConfidence"] == 70
    assert bufr.data["#1#cloudAmount"] == 8
    # assert bufr.data['#1#year->percentConfidence->code'] == TODO
    bufr.data["year"] = 2025
    bufr.data["year->percentConfidence"] = 100
    bufr.data["cloudAmount"] = [1, 2, 3, 4, 5]
    bufr.data["#1#year"] = 2025
    bufr.data["#1#year->percentConfidence"] = 100
    bufr.data["#1#cloudAmount"] = 8
    with pt.raises(ReadOnlyError):
        bufr.data["year->code"] = 0
    with pt.raises(ReadOnlyError):
        bufr.data["#1#year->code"] = 0
    # with pt.raises(ReadOnlyError): bufr.data['#1#year->percentConfidence->code'] = TODO
    # Data keys: undefined
    assert "year->code->code" not in bufr.data
    assert "year->percentConfidence->code->code" not in bufr.data
    assert "#2#year" not in bufr.data
    assert "#2#year->percentConfidence" not in bufr.data
    assert "#2#year->percentConfidence->code" not in bufr.data
    # Negative subscripts
    bufr = BUFRMessage(open("./sample-data/temp.bufr"))
    assert "centre" in bufr.data[-1]
    assert np.all(bufr.data[-1]["centre"] == bufr.data[2]["centre"])
    assert "pressure" in bufr.data[-2]
    assert np.all(bufr.data[-2]["pressure"] == bufr.data[1]["pressure"])
    assert "blockNumber" in bufr.data[-3]
    assert bufr.data[-3]["blockNumber"] == bufr.data[0]["blockNumber"]
    with pt.raises(IndexError):
        bufr.data[-4]


def test_data_get_count():
    bufr = BUFRMessage(open("./sample-data/synop.bufr"))
    with pt.raises(KeyValueNotFoundError):
        bufr.data.get_count("edition")
    assert bufr.get_count("year") == 1
    assert bufr.get_count("year->code") == 1
    assert bufr.get_count("year->percentConfidence") == 1
    assert bufr.get_count("year->percentConfidence->code") == 1
    assert bufr.get_count("#1#year") == 1
    assert bufr.get_count("#1#year->code") == 1
    assert bufr.get_count("#1#year->percentConfidence") == 1
    assert bufr.get_count("#1#year->percentConfidence->code") == 1
    with pt.raises(KeyValueNotFoundError):
        bufr.get_count("#2#year")
    assert bufr.get_count("cloudAmount") == 5
    assert bufr.get_count("cloudAmount->code") == 5
    assert bufr.get_count("cloudAmount->percentConfidence") == 5
    assert bufr.get_count("cloudAmount->percentConfidence->code") == 5
    assert bufr.get_count("#1#cloudAmount") == 1
    assert bufr.get_count("#1#cloudAmount->code") == 1
    assert bufr.get_count("#1#cloudAmount->percentConfidence") == 1
    assert bufr.get_count("#1#cloudAmount->percentConfidence->code") == 1
    with pt.raises(KeyValueNotFoundError):
        bufr.get_count("#6#cloudAmount")
    bufr = BUFRMessage(open("./sample-data/terra-modis-aerosol.bufr"))
    assert bufr.get_count("opticalDepth") == 10
    assert bufr.data[0].get_count("opticalDepth") == 2
    assert bufr.data[1].get_count("opticalDepth") == 8
    assert bufr.data.get_count("#1#opticalDepth") == 1
    assert bufr.data[0].get_count("#1#opticalDepth") == 1
    assert bufr.data[1].get_count("#1#opticalDepth") == 1
    with pt.raises(KeyValueNotFoundError):
        bufr.data.get_count("#11#opticalDepth")
    with pt.raises(KeyValueNotFoundError):
        bufr.data[0].get_count("#3#opticalDepth")
    with pt.raises(KeyValueNotFoundError):
        bufr.data[1].get_count("#9#opticalDepth")


def test_data_is_missing():
    bufr = BUFRMessage("BUFR3_local_satellite")
    bufr["numberOfSubsets"] = 3
    with pt.raises(KeyValueNotFoundError):
        bufr.data.is_missing("edition")
    assert bufr.is_missing("pressure")
    assert bufr.is_missing("#1#pressure")
    assert bufr.is_missing("#2#pressure")
    array = bufr["pressure"]
    assert np.all(array.mask)
    assert array.shape[0] > 1
    array[0, :] = 1013.25
    assert not np.all(array.mask)
    assert not bufr.is_missing("pressure")
    assert not bufr.is_missing("#1#pressure")
    assert bufr.is_missing("#2#pressure")
    bufr.pack()
    assert not bufr.is_missing("pressure")
    assert not bufr.is_missing("#1#pressure")
    assert bufr.is_missing("#2#pressure")


def test_data_set_missing():
    bufr = BUFRMessage("BUFR3_local_satellite")
    bufr["numberOfSubsets"] = 3
    with pt.raises(KeyValueNotFoundError):
        bufr.data.set_missing("edition")
    with pt.raises(ValueCannotBeMissingError):
        bufr.set_missing("pressure->units")
    bufr["pressure"] = 1013.25
    bufr.pack()
    bufr.set_missing("pressure")
    array = bufr["pressure"]
    assert np.all(array.mask)
    bufr["pressure"] = 1013.25
    bufr.pack()
    bufr.set_missing("#1#pressure")
    array = bufr["pressure"]
    assert np.all(array[0, :].mask)
    assert not np.any(array[1:, :].mask)
    bufr.set_missing("#2#pressure")
    assert np.all(array[1, :].mask)
    assert not np.any(array[2:, :].mask)
    bufr.set_missing("pressure")
    assert np.all(array.mask)


def test_data_type_of_seconds():
    # With default, zero scale -> int
    bufr = BUFRMessage("BUFR3_local_satellite")
    bufr["numberOfSubsets"] = 3
    bufr["unexpandedDescriptors"] = [4006]
    assert bufr["second->scale"] == 0
    assert bufr["second"].dtype == np.dtype(int)
    assert bufr["second"].data[0] == CODES_MISSING_LONG
    assert bufr["second"][0] is np.ma.masked
    # With changed, non-zero scale -> float
    bufr = BUFRMessage("BUFR3_local_satellite")
    bufr["numberOfSubsets"] = 3
    bufr["unexpandedDescriptors"] = [202131, 4006, 202000]
    assert bufr["second->scale"] == 3
    assert bufr["second"].dtype == np.dtype(float)
    assert bufr["second"].data[0] == CODES_MISSING_DOUBLE
    assert bufr["second"][0] is np.ma.masked


def test_data_assumed_scalar_elements():
    bufr = BUFRMessage("BUFR3_local_satellite")
    bufr["numberOfSubsets"] = 3
    bufr["unexpandedDescriptors"] = [1007]
    bufr.data["satelliteIdentifier"] = [1, 2, 3]
    bytes = bufr.get_buffer()
    bufr = BUFRMessage(bytes)
    with change_behaviour() as behaviour:
        behaviour.assumed_scalar_elements.add("satelliteIdentifier")
        with pt.warns(UserWarning):
            assert np.all(bufr.data["satelliteIdentifier"] == [1, 2, 3])
        with change_behaviour() as behaviour:
            behaviour.on_assumed_scalar_element_invalid_size = "raise"
            bufr = BUFRMessage(bytes)
            with pt.raises(ValueError):
                assert np.all(bufr.data["satelliteIdentifier"] == [1, 2, 3])
        with change_behaviour() as behaviour:
            behaviour.on_assumed_scalar_element_invalid_size = "ignore"
            bufr = BUFRMessage(bytes)
            with warnings.catch_warnings(record=True) as ws:
                assert np.all(bufr.data["satelliteIdentifier"] == [1, 2, 3])
                assert not ws
    with change_behaviour() as behaviour:
        behaviour.assumed_scalar_elements.add("satelliteIdentifier")
        # Single rank
        bufr = BUFRMessage("BUFR3_local_satellite")
        bufr["numberOfSubsets"] = 3
        bufr["unexpandedDescriptors"] = [1007]
        assert bufr.data["satelliteIdentifier"] is np.ma.masked
        assert bufr.data["#1#satelliteIdentifier"] is np.ma.masked
        bufr.data["satelliteIdentifier"] = 1
        bufr.data["#1#satelliteIdentifier"] = 1
        bufr.pack()
        assert bufr.data["satelliteIdentifier"] == 1
        with pt.raises(ValueError):
            bufr.data["satelliteIdentifier"] = [1, 2, 3]
        # Multiple ranks
        bufr = BUFRMessage("BUFR3_local_satellite")
        bufr["numberOfSubsets"] = 3
        bufr["unexpandedDescriptors"] = [1007, 1007]
        value = bufr.data["satelliteIdentifier"]
        assert isinstance(value, np.ndarray)
        assert value.shape == (2,)
        assert value.all() is np.ma.masked
        value1 = bufr.data["#1#satelliteIdentifier"]
        assert value1 is np.ma.masked
        bufr.data["satelliteIdentifier"] = [0, 0]
        assert np.all(bufr.data["satelliteIdentifier"] == 0)
        bufr.data["#1#satelliteIdentifier"] = 1
        bufr.data["#2#satelliteIdentifier"] = 2
        assert np.all(bufr.data["satelliteIdentifier"] == [1, 2])


def test_data_assignment_with_non_native_types():
    bufr = BUFRMessage("BUFR3_local_satellite")
    bufr["satelliteIdentifier"] = np.int8(0)
    bufr["satelliteIdentifier"] = np.int16(0)
    bufr["satelliteIdentifier"] = np.int32(0)
    bufr["latitude"] = np.float32(0)
