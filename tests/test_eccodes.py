#
# (C) Copyright 2017- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.
#

import os.path
import math
import numpy as np
import pytest

from eccodes import *

SAMPLE_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "sample-data")
TEST_DATA = os.path.join(SAMPLE_DATA_FOLDER, "era5-levels-members.grib")

# ANY
def test_codes_definition_path():
    df = codes_definition_path()
    assert df is not None


def test_codes_samples_path():
    sp = codes_samples_path()
    assert sp is not None


def test_codes_set_definitions_path():
    codes_set_definitions_path(codes_definition_path())


def test_codes_set_samples_path():
    codes_set_samples_path(codes_samples_path())


def test_version_info():
    vinfo = codes_get_version_info()
    assert len(vinfo) == 2


def test_codes_is_defined():
    gid = codes_grib_new_from_samples("sh_sfc_grib1")
    assert codes_is_defined(gid, "JS")


def test_new_from_file():
    samples_path = codes_samples_path()
    if not os.path.isdir(samples_path):
        return
    fpath = os.path.join(samples_path, "GRIB2.tmpl")
    with open(fpath, "rb") as f:
        msgid = codes_new_from_file(f, CODES_PRODUCT_GRIB)
        assert msgid
    fpath = os.path.join(samples_path, "BUFR4.tmpl")
    with open(fpath, "rb") as f:
        msgid = codes_new_from_file(f, CODES_PRODUCT_BUFR)
        assert msgid
    fpath = os.path.join(samples_path, "clusters_grib1.tmpl")
    with open(fpath, "rb") as f:
        msgid = codes_new_from_file(f, CODES_PRODUCT_ANY)
        assert msgid
    with open(fpath, "rb") as f:
        msgid = codes_new_from_file(f, CODES_PRODUCT_GTS)
        assert msgid is None
    with open(fpath, "rb") as f:
        msgid = codes_new_from_file(f, CODES_PRODUCT_METAR)
        assert msgid is None


def test_any_read():
    samples_path = codes_samples_path()
    if not os.path.isdir(samples_path):
        return
    fpath = os.path.join(samples_path, "GRIB1.tmpl")
    with open(fpath, "rb") as f:
        msgid = codes_any_new_from_file(f)
        assert codes_get(msgid, "edition") == 1
        assert codes_get(msgid, "identifier") == "GRIB"
        codes_release(msgid)

    fpath = os.path.join(samples_path, "BUFR3.tmpl")
    with open(fpath, "rb") as f:
        msgid = codes_any_new_from_file(f)
        assert codes_get(msgid, "edition") == 3
        assert codes_get(msgid, "identifier") == "BUFR"
        codes_release(msgid)


def test_count_in_file():
    samples_path = codes_samples_path()
    if not os.path.isdir(samples_path):
        return
    fpath = os.path.join(samples_path, "GRIB1.tmpl")
    with open(fpath, "rb") as f:
        assert codes_count_in_file(f) == 1


def test_new_from_message():
    gid = codes_grib_new_from_samples("sh_sfc_grib1")
    message = codes_get_message(gid)
    codes_release(gid)
    assert len(message) == 9358
    newgid = codes_new_from_message(message)
    assert codes_get(newgid, "packingType") == "spectral_complex"
    assert codes_get(newgid, "gridType") == "sh"
    codes_release(newgid)

    # This time read from a string rather than a file
    metar_str = "METAR LQMO 022350Z 09003KT 6000 FEW010 SCT035 BKN060 08/08 Q1003="
    newgid = codes_new_from_message(metar_str)
    cccc = codes_get(newgid, "CCCC")
    assert cccc == "LQMO"
    codes_release(newgid)


def test_gts_header():
    codes_gts_header(True)
    codes_gts_header(False)


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


def test_grib_set_error():
    gid = codes_grib_new_from_samples("regular_ll_sfc_grib1")
    with pytest.raises(TypeError):
        codes_set_long(gid, "centre", "kwbc")
    with pytest.raises(TypeError):
        codes_set_double(gid, "centre", "kwbc")


def test_grib_write(tmpdir):
    gid = codes_grib_new_from_samples("GRIB2")
    codes_set(gid, "backgroundProcess", 44)
    output = tmpdir.join("test_grib_write.grib")
    with open(str(output), "wb") as fout:
        codes_write(gid, fout)
    codes_release(gid)


def test_grib_codes_set_missing():
    gid = codes_grib_new_from_samples("reduced_rotated_gg_ml_grib2")
    codes_set(gid, "typeOfFirstFixedSurface", "sfc")
    codes_set_missing(gid, "scaleFactorOfFirstFixedSurface")
    codes_set_missing(gid, "scaledValueOfFirstFixedSurface")
    assert codes_is_missing(gid, "scaleFactorOfFirstFixedSurface")


def test_grib_get_message_size():
    gid = codes_grib_new_from_samples("GRIB2")
    assert codes_get_message_size(gid) == 179


def test_grib_get_message_offset():
    gid = codes_grib_new_from_samples("GRIB2")
    assert codes_get_message_offset(gid) == 0


def test_grib_clone():
    gid = codes_grib_new_from_samples("GRIB2")
    clone = codes_clone(gid)
    assert gid
    assert clone
    assert codes_get(clone, "identifier") == "GRIB"
    assert codes_get(clone, "totalLength") == 179
    codes_release(gid)
    codes_release(clone)


def test_grib_keys_iterator():
    gid = codes_grib_new_from_samples("reduced_gg_pl_1280_grib1")
    iterid = codes_keys_iterator_new(gid, "ls")
    count = 0
    while codes_keys_iterator_next(iterid):
        keyname = codes_keys_iterator_get_name(iterid)
        keyval = codes_get_string(gid, keyname)
        count += 1
    assert count == 10
    codes_keys_iterator_rewind(iterid)
    codes_keys_iterator_delete(iterid)
    codes_release(gid)


def test_grib_keys_iterator_skip():
    gid = codes_grib_new_from_samples("reduced_gg_pl_1280_grib1")
    iterid = codes_keys_iterator_new(gid, "ls")
    count = 0
    codes_skip_computed(iterid)
    # codes_skip_coded(iterid)
    codes_skip_edition_specific(iterid)
    codes_skip_duplicates(iterid)
    codes_skip_read_only(iterid)
    codes_skip_function(iterid)
    while codes_keys_iterator_next(iterid):
        keyname = codes_keys_iterator_get_name(iterid)
        keyval = codes_get_string(gid, keyname)
        count += 1
    # centre, level and dataType
    assert count == 3
    codes_keys_iterator_delete(iterid)
    codes_release(gid)


def test_grib_get_data():
    gid = codes_grib_new_from_samples("GRIB1")
    ggd = codes_grib_get_data(gid)
    assert len(ggd) == 65160
    codes_release(gid)
    gid = codes_grib_new_from_samples("reduced_gg_pl_32_grib2")
    ggd = codes_grib_get_data(gid)
    assert len(ggd) == 6114
    elem1 = ggd[0]  # This is a 'Bunch' derived off dict
    assert "lat" in elem1.keys()
    assert "lon" in elem1.keys()
    assert "value" in elem1.keys()
    codes_release(gid)


def test_grib_get_double_element():
    gid = codes_grib_new_from_samples("gg_sfc_grib2")
    elem = codes_get_double_element(gid, "values", 1)
    assert math.isclose(elem, 259.9865, abs_tol=0.001)


def test_grib_get_double_elements():
    gid = codes_grib_new_from_samples("gg_sfc_grib1")
    values = codes_get_values(gid)
    num_vals = len(values)
    indexes = [0, int(num_vals / 2), num_vals - 1]
    elems = codes_get_double_elements(gid, "values", indexes)
    assert math.isclose(elems[0], 259.6935, abs_tol=0.001)
    assert math.isclose(elems[1], 299.9064, abs_tol=0.001)
    assert math.isclose(elems[2], 218.8146, abs_tol=0.001)
    elems2 = codes_get_elements(gid, "values", indexes)
    assert elems == elems2


def test_grib_geoiterator():
    gid = codes_grib_new_from_samples("reduced_gg_pl_256_grib2")
    iterid = codes_grib_iterator_new(gid, 0)
    i = 0
    while 1:
        result = codes_grib_iterator_next(iterid)
        if not result:
            break
        [lat, lon, value] = result
        i += 1
    assert i == 348528
    codes_grib_iterator_delete(iterid)
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
    # Cannot do more than 4 nearest neighbours
    with pytest.raises(ValueError):
        codes_grib_find_nearest(gid, lat, lon, False, 5)
    codes_release(gid)


def test_grib_nearest_multiple():
    gid = codes_new_from_samples("reduced_gg_ml_grib2", CODES_PRODUCT_GRIB)
    inlats = (30, 13)
    inlons = (-20, 234)
    is_lsm = False
    nearest = codes_grib_find_nearest_multiple(gid, is_lsm, inlats, inlons)
    codes_release(gid)
    assert nearest[0].index == 1770
    assert nearest[1].index == 2500


def test_grib_ecc_1042():
    # Issue ECC-1042: Python3 interface writes integer arrays incorrectly
    gid = codes_grib_new_from_samples("regular_ll_sfc_grib2")

    # Trying write with inferred dtype
    write_vals = np.array([1, 2, 3])
    codes_set_values(gid, write_vals)
    read_vals = codes_get_values(gid)
    length = len(read_vals)
    assert read_vals[0] == 1
    assert read_vals[length - 1] == 3

    # Trying write with explicit dtype
    write_vals = np.array([1, 2, 3,], dtype=np.float,)
    codes_set_values(gid, write_vals)
    read_vals = codes_get_values(gid)
    assert read_vals[0] == 1
    assert read_vals[length - 1] == 3

    codes_release(gid)


def test_grib_ecc_1007():
    # Issue ECC-1007: Python3 interface cannot write large arrays
    gid = codes_grib_new_from_samples("regular_ll_sfc_grib2")
    numvals = 1501 * 1501
    values = np.zeros((numvals,))
    values[0] = 12  # Make sure it's not a constant field
    codes_set_values(gid, values)
    maxv = eccodes.codes_get(gid, "max")
    minv = eccodes.codes_get(gid, "min")
    assert minv == 0
    assert maxv == 12
    codes_release(gid)


def test_gribex_mode():
    codes_gribex_mode_on()
    codes_gribex_mode_off()


def test_grib_new_from_samples_error():
    with pytest.raises(FileNotFoundError):
        gid = codes_new_from_samples("poopoo", CODES_PRODUCT_GRIB)


def test_grib_new_from_file_error(tmp_path):
    with pytest.raises(TypeError):
        codes_grib_new_from_file(None)
    p = tmp_path / "afile.txt"
    p.write_text("GRIBxxxx")
    with open(p, "rb") as f:
        with pytest.raises(UnsupportedEditionError):
            msg = codes_grib_new_from_file(f)


def test_grib_index_new_from_file(tmpdir):
    samples_path = codes_samples_path()
    if not os.path.isdir(samples_path):
        return
    fpath = os.path.join(samples_path, "GRIB1.tmpl")
    index_keys = ["shortName", "level", "number", "step"]
    iid = codes_index_new_from_file(fpath, index_keys)
    index_file = str(tmpdir.join("temp.grib.index"))
    codes_index_write(iid, index_file)

    key = "level"
    assert codes_index_get_size(iid, key) == 1
    assert codes_index_get(iid, key) == ("500",)

    codes_index_select(iid, "level", 500)
    codes_index_select(iid, "shortName", "z")
    codes_index_select(iid, "number", 0)
    codes_index_select(iid, "step", 0)
    gid = codes_new_from_index(iid)
    assert codes_get(gid, "edition") == 1
    assert codes_get(gid, "totalLength") == 107
    codes_release(gid)

    codes_index_release(iid)

    iid2 = codes_index_read(index_file)
    assert codes_index_get(iid2, "shortName") == ("z",)
    codes_index_release(iid2)


# BUFR
def test_bufr_read_write(tmpdir):
    bid = codes_new_from_samples("BUFR4", CODES_PRODUCT_BUFR)
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


def test_bufr_encode(tmpdir):
    ibufr = codes_bufr_new_from_samples("BUFR3_local_satellite")
    codes_set_array(ibufr, "inputDelayedDescriptorReplicationFactor", (4,))
    codes_set(ibufr, "masterTableNumber", 0)
    codes_set(ibufr, "bufrHeaderSubCentre", 0)
    codes_set(ibufr, "bufrHeaderCentre", 98)
    codes_set(ibufr, "updateSequenceNumber", 0)
    codes_set(ibufr, "dataCategory", 12)
    codes_set(ibufr, "dataSubCategory", 139)
    codes_set(ibufr, "masterTablesVersionNumber", 13)
    codes_set(ibufr, "localTablesVersionNumber", 1)
    codes_set(ibufr, "numberOfSubsets", 492)
    codes_set(ibufr, "localNumberOfObservations", 492)
    codes_set(ibufr, "satelliteID", 4)
    codes_set(ibufr, "observedData", 1)
    codes_set(ibufr, "compressedData", 1)
    codes_set(ibufr, "unexpandedDescriptors", 312061)
    codes_set(ibufr, "pixelSizeOnHorizontal1", 1.25e04)
    codes_set(ibufr, "orbitNumber", 31330)
    codes_set(ibufr, "#1#beamIdentifier", 1)
    codes_set(ibufr, "#4#likelihoodComputedForSolution", CODES_MISSING_DOUBLE)
    codes_set(ibufr, "pack", 1)
    output = tmpdir.join("test_bufr_encode.bufr")
    with open(str(output), "wb") as fout:
        codes_write(ibufr, fout)
    codes_release(ibufr)


def test_bufr_set_string_array(tmpdir):
    ibufr = codes_bufr_new_from_samples("BUFR3_local_satellite")
    codes_set(ibufr, "numberOfSubsets", 3)
    codes_set(ibufr, "unexpandedDescriptors", 307022)
    inputVals = ("ARD2-LPTR", "EPFL-LPTR", "BOU2-LPTR")
    codes_set_array(ibufr, "stationOrSiteName", inputVals)
    codes_set(ibufr, "pack", 1)
    outputVals = codes_get_string_array(ibufr, "stationOrSiteName")
    assert len(outputVals) == 3
    assert outputVals[0] == "ARD2-LPTR"
    assert outputVals[1] == "EPFL-LPTR"
    assert outputVals[2] == "BOU2-LPTR"
    codes_release(ibufr)


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
    codes_bufr_keys_iterator_rewind(iterid)
    codes_bufr_keys_iterator_delete(iterid)
    codes_release(bid)


def test_bufr_multi_element_constant_arrays():
    codes_bufr_multi_element_constant_arrays_off()
    bid = codes_bufr_new_from_samples("BUFR3_local_satellite")
    codes_set(bid, "unpack", 1)
    assert codes_get_size(bid, "satelliteIdentifier") == 1
    codes_release(bid)

    codes_bufr_multi_element_constant_arrays_on()
    bid = codes_bufr_new_from_samples("BUFR3_local_satellite")
    codes_set(bid, "unpack", 1)
    numSubsets = codes_get(bid, "numberOfSubsets")
    assert codes_get_size(bid, "satelliteIdentifier") == numSubsets
    codes_release(bid)


def test_bufr_new_from_samples_error():
    with pytest.raises(FileNotFoundError):
        gid = codes_new_from_samples("poopoo", CODES_PRODUCT_BUFR)


def test_bufr_get_message_size():
    gid = codes_bufr_new_from_samples("BUFR3_local")
    assert codes_get_message_size(gid) == 279


def test_bufr_get_message_offset():
    gid = codes_bufr_new_from_samples("BUFR3_local")
    assert codes_get_message_offset(gid) == 0


# Experimental feature
def test_bufr_extract_headers():
    samples_path = codes_samples_path()
    if not os.path.isdir(samples_path):
        return
    print("Samples path = ", samples_path)
    fpath = os.path.join(samples_path, "BUFR4_local.tmpl")
    headers = list(codes_bufr_extract_headers(fpath))
    # Sample file contains just one message
    assert len(headers) == 1
    header = headers[0]
    assert header["edition"] == 4
    assert header["internationalDataSubCategory"] == 255
    assert header["masterTablesVersionNumber"] == 24
    assert header["ident"] == "91334   "
    assert header["rdbtimeSecond"] == 19
    assert math.isclose(header["localLongitude"], 151.83)
