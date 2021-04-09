import os
from eccodes import GribFile
from eccodes import codes_samples_path


def test_iterating_through_grib_file():
    sample_path = os.path.join(codes_samples_path(), "GRIB2.tmpl")
    if not os.path.isfile(sample_path):
        return
    with GribFile(sample_path) as grib:
        count = 0
        for msg in grib:
            count += 1
    assert count == 1


def test_iterating_through_grib_file_manual_close():
    sample_path = os.path.join(codes_samples_path(), "GRIB2.tmpl")
    if not os.path.isfile(sample_path):
        return
    with GribFile(sample_path) as grib:
        count = 0
        for msg in grib:
            count += 1
        msg.close()
    assert count == 1
