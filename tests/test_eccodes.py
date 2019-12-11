import os.path
import math
import numpy as np
import pytest

from eccodes import *

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")
TEST_DATA = os.path.join(SAMPLE_DATA_FOLDER, "era5-levels-members.grib")


# GRIB
def test_grib_read():
    gid = codes_grib_new_from_samples("regular_ll_sfc_grib1")
    assert codes_get(gid, "Ni") == 16
    assert codes_get(gid, "Nj") == 31
    assert codes_get(gid, "const") == 1
    assert codes_get(gid, "centre", str) == "ecmf"
    assert codes_get(gid, "packingType", str) == "grid_simple"
    assert codes_get(gid, "gridType", str) == "regular_ll"
    codes_release(gid)
    gid = codes_grib_new_from_samples("sh_ml_grib2")
    assert codes_get(gid, "const") == 0
    assert codes_get(gid, "gridType", str) == "sh"
    assert codes_get(gid, "typeOfLevel", str) == "hybrid"
    assert codes_get_long(gid, "avg") == 185
    codes_release(gid)


def test_grib_write(tmpdir):
    gid = codes_grib_new_from_samples("GRIB2")
    codes_set(gid, "backgroundProcess", 44)
    output = tmpdir.join("test_grib_write.grib")
    with open(str(output), "wb") as fout:
        codes_write(gid, fout)
    codes_release(gid)


def test_grib_keys_iterator():
    gid = codes_grib_new_from_samples("reduced_gg_pl_1280_grib1")
    iterid = codes_keys_iterator_new(gid, "ls")
    count = 0
    while codes_keys_iterator_next(iterid):
        keyname = codes_keys_iterator_get_name(iterid)
        keyval = codes_get_string(gid, keyname)
        count += 1
    assert count == 10
    codes_keys_iterator_delete(iterid)
    codes_release(gid)


def test_grib_get_data():
    gid = codes_grib_new_from_samples("GRIB1")
    ggd = eccodes.codes_grib_get_data(gid)
    assert len(ggd) == 65160
    codes_release(gid)
    gid = codes_grib_new_from_samples("reduced_gg_pl_32_grib2")
    ggd = eccodes.codes_grib_get_data(gid)
    assert len(ggd) == 6114
    codes_release(gid)


def test_grib_nearest():
    gid = codes_grib_new_from_samples("reduced_gg_ml_grib2")
    lat, lon = 30, -20
    nearest = codes_grib_find_nearest(gid, lat, lon)[0]
    assert nearest.index == 1770
    lat, lon = 10, 0
    nearest = codes_grib_find_nearest(gid, lat, lon)[0]
    assert nearest.index == 2545
    lat, lon = 10, 20
    nearest = codes_grib_find_nearest(gid, lat, lon, False, 4)
    expected_indexes = (2553, 2552, 2425, 2424)
    returned_indexes = (
        nearest[0].index,
        nearest[1].index,
        nearest[2].index,
        nearest[3].index,
    )
    assert sorted(expected_indexes) == sorted(returned_indexes)
    codes_release(gid)


# BUFR
def test_bufr_read_write(tmpdir):
    bid = codes_bufr_new_from_samples("BUFR4")
    codes_set(bid, "unpack", 1)
    assert codes_get(bid, "typicalYear") == 2012
    assert codes_get(bid, "centre", str) == "ecmf"
    codes_set(bid, "totalSunshine", 13)
    codes_set(bid, "pack", 1)
    output = tmpdir.join("test_bufr_write.bufr")
    with open(str(output), "wb") as fout:
        codes_write(bid, fout)
    assert codes_get(bid, "totalSunshine") == 13
    codes_release(bid)


def test_bufr_keys_iterator():
    bid = codes_bufr_new_from_samples("BUFR3_local_satellite")
    # Header keys only
    iterid = codes_bufr_keys_iterator_new(bid)
    count = 0
    while codes_bufr_keys_iterator_next(iterid):
        keyname = codes_bufr_keys_iterator_get_name(iterid)
        assert "#" not in keyname
        count += 1
    assert count == 53

    codes_set(bid, "unpack", 1)
    codes_bufr_keys_iterator_rewind(iterid)
    count = 0
    while codes_bufr_keys_iterator_next(iterid):
        keyname = codes_bufr_keys_iterator_get_name(iterid)
        count += 1
    assert count == 156

    codes_bufr_keys_iterator_delete(iterid)
    codes_release(bid)


# Experimental feature
def _test_bufr_extract_headers():
    samples_path = codes_samples_path()
    fpath = os.path.join(samples_path, "BUFR4_local.tmpl")
    headers = list(codes_bufr_extract_headers(fpath))
    # Sample file contains just one message
    assert len(headers) == 1
    header = headers[0]
    assert header['edition'] == 4
    assert header['internationalDataSubCategory'] == 255
    assert header['masterTablesVersionNumber'] == 24
    assert header['ident'] == "91334   "
    assert header['rdbtimeSecond'] == 19
    assert math.isclose(header['localLongitude'], 151.83)
