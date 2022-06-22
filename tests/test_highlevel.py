import collections
import pathlib

import numpy as np
import pytest

import eccodes

SAMPLE_DATA_FOLDER = pathlib.Path(__file__).parent / "sample-data"
TEST_GRIB_DATA = SAMPLE_DATA_FOLDER / "tiggelam_cnmc_sfc.grib2"
TEST_GRIB_DATA2 = SAMPLE_DATA_FOLDER / "era5-levels-members.grib"


def test_filereader():
    with eccodes.FileReader(TEST_GRIB_DATA) as reader:
        count = len([None for _ in reader])
    assert count == 7


def test_read_message():
    with eccodes.FileReader(TEST_GRIB_DATA) as reader:
        message = next(reader)
        assert isinstance(message, eccodes.GRIBMessage)


def test_message_get():
    dummy_default = object()
    known_missing = "scaleFactorOfSecondFixedSurface"
    with eccodes.FileReader(TEST_GRIB_DATA) as reader:
        message = next(reader)
        assert message.get("edition") == 2
        assert message.get("nonexistent") is None
        assert message.get("nonexistent", dummy_default) is dummy_default
        assert message.get("centre", ktype=int) == 250
        vals = message.get("values")
        assert len(vals) == message.get("numberOfValues")
        vals2 = message.data
        assert np.all(vals == vals2)
        assert message["Ni"] == 511
        with pytest.raises(KeyError):
            message["invalid"]
        # keys set as MISSING
        assert message.is_missing(known_missing)
        assert message.get(known_missing) is None
        assert message.get(known_missing, dummy_default) is dummy_default
        with pytest.raises(KeyError):
            message[known_missing]


def test_message_set():
    missing_key = "scaleFactorOfFirstFixedSurface"
    with eccodes.FileReader(TEST_GRIB_DATA) as reader:
        message = next(reader)
        message.set("centre", "ecmf")
        vals = np.arange(message.get("numberOfValues"), dtype=np.float32)
        message.set_array("values", vals)
        message.set_missing(missing_key)
        assert message.get("centre") == "ecmf"
        assert np.all(message.get("values") == vals)
        assert message.is_missing(missing_key)


def test_message_iter():
    with eccodes.FileReader(TEST_GRIB_DATA2) as reader:
        message = next(reader)
        keys = list(message)
        assert len(keys) == 192
        assert keys[-1] == "7777"
        assert "centre" in keys
        assert "shortName" in keys

        keys2 = list(message.keys())
        assert keys == keys2

        items = collections.OrderedDict(message.items())
        assert list(items.keys()) == keys
        assert items["shortName"] == "z"
        assert items["centre"] == "ecmf"

        values = list(message.values())
        assert values[keys.index("shortName")] == "z"
        assert values[keys.index("centre")] == "ecmf"
        assert values[-1] == "7777"


def test_message_iter_missingvalues():
    missing_key = "level"
    with eccodes.FileReader(TEST_GRIB_DATA2) as reader:
        message = next(reader)
        message[missing_key] = 42
        message.set_missing(missing_key)

        assert missing_key not in set(message)
        assert missing_key not in set(message.keys())
        assert missing_key not in dict(message.items())


def test_message_copy():
    with eccodes.FileReader(TEST_GRIB_DATA2) as reader:
        message = next(reader)
        message2 = message.copy()
        assert list(message.keys()) == list(message2.keys())
