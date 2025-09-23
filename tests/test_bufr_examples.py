# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import io
import pytest

from pathlib import Path

@pytest.fixture(autouse=True)
def fixture(monkeypatch):
    this_dir = Path(__file__).parent
    monkeypatch.syspath_prepend(this_dir.parent)
    # monkeypatch.chdir(this_dir.parent / 'data')
    monkeypatch.chdir(this_dir / 'sample-data')

def compare(output: str, reference: Path):
    if not reference.exists():
        reference.write_text(output)
    try:
        assert output == reference.read_text()
    except AssertionError as error:
        reference.with_suffix(reference.suffix + '.bad').write_text(output)
        raise error
    else:
        reference.with_suffix(reference.suffix + '.bad').unlink(missing_ok=True)

inputs = [
    'acars.bufr',
    'ahi-himawari-8.bufr',
    'amsu-a-noaa-19.bufr',
    'amv-goes-9.bufr',
    'amv-insat-3d.bufr',
    'amv-meteosat-9.bufr',
    'amv-noaa-20.bufr',
    'aura-omi-ak.bufr',
    'buoy-drifting.bufr',
    'geos-abi-goes-16.bufr',
    'geos-mviri-meteosat-7.bufr',
    'hdob.bufr',
    'rwp.bufr',
    'rwp_jma.bufr',
    'saral-altika.bufr',
    'sral_sentinel_3a.bufr',
    'synop.bufr',
    'synop_multi_subset.bufr',
    'temp.bufr',
    'terra-modis-aerosol.bufr',
    'wave.bufr',
]

@pytest.mark.parametrize('input', inputs)
def test_attributes_example(input):
    from examples.attributes import run_example
    input = Path(input)
    stream = io.StringIO()
    run_example(input, output=stream)
    output = stream.getvalue()
    reference = input.with_suffix('.attributes')
    compare(output, reference)


@pytest.mark.parametrize('input', inputs)
def test_items_example(input):
    from examples.items import run_example
    input = Path(input)
    stream = io.StringIO()
    run_example(input, stream)
    output = stream.getvalue()
    reference = input.with_suffix('.items')
    compare(output, reference)
