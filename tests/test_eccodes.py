import os.path
import numpy as np
import pytest

from eccodes import *

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'sample-data')
TEST_DATA = os.path.join(SAMPLE_DATA_FOLDER, 'era5-levels-members.grib')


# GRIB
def test_grib_read():
    gid = codes_grib_new_from_samples('regular_ll_sfc_grib1')
    assert codes_get(gid, 'Ni') == 16
    assert codes_get(gid, 'Nj') == 31
    assert codes_get(gid, 'centre', str) == 'ecmf'
    codes_release(gid)


def test_grib_write(tmpdir):
    gid = codes_grib_new_from_samples('GRIB2')
    codes_set(gid, 'backgroundProcess', 44)
    output = tmpdir.join('test_grib_write.grib')
    with open(str(output), 'wb') as fout:
        codes_write(gid, fout)
    codes_release(gid)


# BUFR
def test_bufr_read_write(tmpdir):
    bid = codes_bufr_new_from_samples('BUFR4')
    codes_set(bid, 'unpack', 1)
    assert codes_get(bid, 'typicalYear') == 2012
    assert codes_get(bid, 'centre', str) == 'ecmf'
    codes_set(bid, 'totalSunshine', 13)
    codes_set(bid, 'pack', 1)
    output = tmpdir.join('test_bufr_write.bufr')
    with open(str(output), 'wb') as fout:
        codes_write(bid, fout)
    assert codes_get(bid, 'totalSunshine') == 13
    codes_release(bid)
