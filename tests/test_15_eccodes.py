
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import bytes, float, int

import os.path

import pytest

from eccodes import bindings
from eccodes import eccodes


SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'sample-data')
TEST_DATA = os.path.join(SAMPLE_DATA_FOLDER, 'era5-levels-members.grib')
TEST_DATA_B = TEST_DATA.encode('ASCII')


@pytest.mark.parametrize('key, ktype, expected_value', [
    (b'numberOfDataPoints', int, 7320),
    (b'latitudeOfFirstGridPointInDegrees', float, 90.0),
    (b'gridType', bytes, b'regular_ll'),
])
def test_codes_index_get(key, ktype, expected_value):
    grib_index = bindings.codes_index_new_from_file(TEST_DATA_B, [key])

    res = eccodes.codes_index_get(grib_index, key, ktype=ktype)

    assert len(res) == 1
    assert isinstance(res[0], ktype)
    assert res[0] == expected_value


@pytest.mark.parametrize('key, value', [
    (b'numberOfDataPoints', 7320),
    (b'gridType', b'regular_ll'),
])
def test_codes_index_select(key, value):
    grib_index = bindings.codes_index_new_from_file(TEST_DATA_B, [key])

    eccodes.codes_index_select(grib_index, key, value)
    grib_handle = bindings.codes_new_from_index(grib_index)

    result = bindings.codes_get(grib_handle, key)

    assert result == value


def test_codes_set():
    message_id = bindings.codes_new_from_samples(b'regular_ll_sfc_grib2')

    eccodes.codes_set(message_id, b'endStep', 2)
    eccodes.codes_set(message_id, b'longitudeOfFirstGridPointInDegrees', 1.)
    eccodes.codes_set(message_id, b'gridType', b'regular_ll')

    with pytest.raises(TypeError):
        eccodes.codes_set(message_id, b'endStep', [])
