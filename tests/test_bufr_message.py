# Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import datetime as dt
import numpy as np
import pytest as pt

from eccodes import *
from eccodes.highlevel._bufr import *

@pt.fixture(autouse=True)
def fixture(monkeypatch):
    import os
    this_dir = os.path.dirname(__file__)
    monkeypatch.chdir(this_dir) # always run tests from the tests directory

def unpacked(bufr):
    defined = codes_is_defined(bufr._handle, 'year')
    return bool(defined)

def compare_items(m1, m2, keys=None):
    if keys:
        keys = list(keys)
        i1 = [(k, m1[k]) for k in keys]
        i2 = [(k, m2[k]) for k in keys]
    else:
        i1 = list(m1.items())
        i2 = list(m2.items())
    for (k1, v1), (k2, v2) in zip(i1, i2):
        assert k1 == k2
        if isinstance(v1, np.ndarray):
            if v1.dtype.type == np.str_:
                equal = np.char.compare_chararrays(v1, v2, '==', rstrip=True)
            else:
                equal = v1.data == v2.data
            assert k1 and np.all(equal)
        else:
            assert k1 and v1 == v2

def test_message_uncompressed():
    bufr = BUFRMessage(open('./sample-data/synop_multi_subset.bufr'))
    assert bufr['edition'] == 4
    assert np.all(bufr['unexpandedDescriptors'] == [307079, 4025, 11042]) # is always array
    assert 'dataCategory' in bufr.header
    assert bufr.get_count('dataCategory') == 1
    bufr['dataCategory'] = 11
    assert not unpacked(bufr)
    assert not 'underfined' in bufr     # triggers unpacking
    assert unpacked(bufr)
    # Accessing undefined elements raises an exception
    with pt.raises(KeyValueNotFoundError):
        bufr['undefined']
    with pt.raises(KeyValueNotFoundError):
        bufr['undefined'] = 0
    assert 'blockNumber' in bufr
    assert bufr.get_count('blockNumber') == 12
    assert len(bufr.data) == 12    # number of subsets
    assert len(bufr.data[0]) == 19 # number of data tree nodes per subset
    assert np.all(bufr['stationNumber'].data == np.array([27,  84, 270, 272, 308, 371, 381, 382, 387, 413, 464, 485]))
    assert bufr['#1#stationNumber'] == 27
    assert bufr.data[0]['stationNumber'] == 27 # of the 1st subset
    bufr['stationNumber'][0] = missing_of(int)
    assert bufr['stationNumber'].data[0] == missing_of(int)
    bufr['stationNumber'] = missing_of(int)
    assert np.all(bufr['stationNumber'].data == missing_of(int))
    # Keys can have element attribute as a suffix (à la ecCodes)
    assert bufr['stationNumber->units'] == 'Numeric'
    # Attempting to modify element attributes raises an exception
    with pt.raises(ReadOnlyError):
        bufr['stationNumber->units'] = 'Turmeric'

def test_message_compressed():
    bufr = BUFRMessage(open('./sample-data/sral_sentinel_3a.bufr'))
    assert len(bufr.data) == 1 # this message doesn't have any replications, so the structure is flat
    year = bufr['year']
    assert year.shape == (22, 5)
    assert np.all(year[ 0].data == 2017)
    assert np.all(year[-1].data == missing_of(int))
    # Keys can have rank prefix (à la ecCodes)
    bufr['#1#year'] = 2018
    assert np.all(bufr['#1#year'].data == 2018)
    # Packing the message by setting the 'pack' key is disallowed
    with pt.raises(KeyValueNotFoundError):
        bufr['pack'] = 1
    # The same goes for unpacking
    with pt.raises(KeyValueNotFoundError):
        bufr['unpack'] = 1

def test_message_sample_defaults():
    bufr = BUFRMessage('BUFR3')
    assert bufr['edition'] == 3
    assert bufr['masterTableNumber'] == 0
    assert bufr['masterTablesVersionNumber'] == 24
    assert bufr['localTablesVersionNumber'] == 0
    assert bufr['bufrHeaderCentre'] == 98
    assert bufr['bufrHeaderSubCentre'] == 0
    assert bufr['numberOfSubsets'] == 1
    assert bufr['compressedData'] == False
    assert bufr['section2Present'] == False
    assert np.all(bufr['unexpandedDescriptors'] == 307080)
    bufr = BUFRMessage('BUFR3_local')
    assert bufr['edition'] == 3
    assert bufr['masterTableNumber'] == 0
    assert bufr['masterTablesVersionNumber'] == 24
    assert bufr['localTablesVersionNumber'] == 0
    assert bufr['bufrHeaderCentre'] == 98
    assert bufr['bufrHeaderSubCentre'] == 0
    assert bufr['numberOfSubsets'] == 1
    assert bufr['compressedData'] == False
    assert bufr['section2Present'] == True
    assert np.all(bufr['unexpandedDescriptors'] == 307080)
    bufr = BUFRMessage('BUFR4_local')
    assert bufr['edition'] == 4
    assert bufr['masterTableNumber'] == 0
    assert bufr['masterTablesVersionNumber'] == 24
    assert bufr['localTablesVersionNumber'] == 0
    assert bufr['bufrHeaderCentre'] == 98
    assert bufr['bufrHeaderSubCentre'] == 0
    assert bufr['numberOfSubsets'] == 1
    assert bufr['compressedData'] == False
    assert np.all(bufr['unexpandedDescriptors'] == 307080)
    bufr = BUFRMessage('BUFR3_local_satellite')
    assert bufr['edition'] == 3
    assert bufr['masterTableNumber'] == 0
    assert bufr['masterTablesVersionNumber'] == 13
    assert bufr['localTablesVersionNumber'] == 1
    assert bufr['bufrHeaderCentre'] == 98
    assert bufr['bufrHeaderSubCentre'] == 0
    assert bufr['numberOfSubsets'] == 128
    assert bufr['compressedData'] == True
    assert np.all(bufr['unexpandedDescriptors'] == 310014)
    bufr = BUFRMessage('BUFR4_local_satellite')
    assert bufr['edition'] == 4
    assert bufr['masterTableNumber'] == 0
    assert bufr['masterTablesVersionNumber'] == 13
    assert bufr['localTablesVersionNumber'] == 1
    assert bufr['bufrHeaderCentre'] == 98
    assert bufr['bufrHeaderSubCentre'] == 0
    assert bufr['numberOfSubsets'] == 128
    assert bufr['compressedData'] == True
    assert np.all(bufr['unexpandedDescriptors'] == 310008)

def test_message_new_from_sample():
    bufr = BUFRMessage('BUFR3_local_satellite')
    # If the tables version is not set properly, eccodes fails with
    # "HashArrayNoMatchError: Hash array no match" when setting
    # unexpandedDescriptors.
    bufr['masterTablesVersionNumber'] = 18
    bufr['localTablesVersionNumber'] = 0
    bufr['numberOfSubsets'] = 2
    bufr['compressedData'] = True
    # Input replication factors are optional; will default to 0 if not set.
    bufr['inputDelayedDescriptorReplicationFactor'] = [0, 0]
    bufr['inputShortDelayedDescriptorReplicationFactor'] = [0, 0, 0, 0, 0, 0]
    bufr['unexpandedDescriptors'] = [311011]

    bufr['year'] = 2022

    # Template-related items can't be changed once the header is "baked" in
    for key in ('numberOfSubsets', 'compressedData', 'unexpandedDescriptors'):
        with pt.raises(ReadOnlyError):
            bufr[key] = 1
    # Test that common Section 2 keys are set properly
    bufr.pack()
    assert bufr['localNumberOfObservations'] == bufr['numberOfSubsets']

def test_message_new_from_bytes():
    old = BUFRMessage('BUFR3_local')
    bytes = old.get_buffer()
    new = BUFRMessage(bytes)
    compare_items(old.header, new.header, keys=old.header.keys(skip='read_only'))
    compare_items(old.data, new.data)

def test_message_context_manager():
    bufr = BUFRMessage('BUFR3_local')
    assert bufr._handle > 0
    with bufr:
        pass
    assert bufr._handle == 0

def test_message_copy():
    # Copy is the same as the original (note that copying doesn't require unpacking)
    old = BUFRMessage(open('./sample-data/synop.bufr'))
    assert unpacked(old) is False
    new = old.copy()
    assert unpacked(old) is False
    assert old['md5Data'] == new['md5Data']
    assert old._handle != new._handle
    compare_items(old, new)

    # FIXME: The following code doesnt't work because eccodes apparently doesn't
    # update typicalDate (which is computed key) when we modify typicalYearOfCentury .

    # After chainging one of the header section keys
    # old['typicalYearOfCentury'] = 25
    # new = old.copy()
    # assert old['md5Data'] == new['md5Data']
    # compare_items(old, new)

    # After changing one of the data section keys
    old['blockNumber'] = 99
    new = old.copy()
    assert old['md5Data'] == new['md5Data']
    compare_items(old, new)

def test_message_copy_subsets():
    old = BUFRMessage(open('./sample-data/ahi-himawari-8.bufr'))
    old_count = old['numberOfSubsets']
    old['second'] = range(0, old_count)
    # Copy adjacent subsets where mask is True (uses extractSubsetInterval)
    mask = np.repeat(False, old_count)
    mask[0:3] = True
    with old.copy(subsets=mask) as new:
        assert new['numberOfSubsets'] == 3
        assert np.all(new['second'] == [0, 1, 2])
    # # Copy adjacent subsets where mask is True (uses extractSubsetList)
    mask = np.repeat(False, old_count)
    mask[[0, 2, 4]] = True
    with old.copy(subsets=mask) as new:
        assert new['numberOfSubsets'] == 3
        assert np.all(new['second'] == [0, 2, 4])
    # Copy a range of adjacent subsets (uses extractSubsetInterval)
    with old.copy(subsets=range(3)) as new:
        assert new['numberOfSubsets'] == 3
        assert np.all(new['second'] == [0, 1, 2])
    # Copy a range of non-adjacent subsets (uses extractSubsetList)
    with old.copy(subsets=range(0, 5, 2)) as new:
        assert new['numberOfSubsets'] == 3
        assert np.all(new['second'] == [0, 2, 4])
    # Copy a list of adjacent subsets (uses extractSubsetInterval)
    with old.copy(subsets=[0, 1, 2]) as new:
        assert new['numberOfSubsets'] == 3
        assert np.all(new['second'] == [0, 1, 2])
    # Copy a list of non-adjacent subsets (uses extractSubsetList)
    with old.copy(subsets=[0, 2, 4]) as new:
        assert new['numberOfSubsets'] == 3
        assert np.all(new['second'] == [0, 2, 4])
    # Copy a full slice of all subsets
    # (uses extractSubsetInterval, or no extraction if there were no previous ones)
    with old.copy(subsets=slice(None, None, None)) as new: # [1]
        assert new['numberOfSubsets'] == old_count
        assert np.all(new['second'] == range(0, old_count))
    # Copy every 4th subset (uses extractSubsetInterval)
    with old.copy(subsets=slice(None, None, 4)) as new:
        assert new['numberOfSubsets'] == divmod(old_count, 4)[0]
        assert np.all(new['second'] == range(0, old_count, 4))
    # Copy every 4th subset within a range (uses extractSubsetList)
    with old.copy(subsets=slice(16, 32, 4)) as new:
        assert new['numberOfSubsets'] == divmod(32 - 16, 4)[0]
        assert np.all(new['second'] == old['second'][16:32:4])
    # Copy datetime slice (uses extractSubsetInterval)
    old_datetime = old.get_datetime()
    start = old_datetime[0].item()
    end = start + dt.timedelta(seconds=2)
    with old.copy(subsets=slice(None, end)) as new:
        assert new['numberOfSubsets'] == 3
        new_datetime = new.get_datetime()
        assert np.all(new_datetime == old_datetime[0:3])

    # [1] Note that this prints a lot of 'ECCODES ERROR' messages due to ECC-2025,
    #     but otherwise the code works OK because we work around the issue internally.

def test_message_copy_to():
    old = BUFRMessage(open('./sample-data/aura-omi-ak.bufr'))
    new = BUFRMessage('BUFR3_local_satellite')
    old.copy_to(new)
    compare_items(old.header, new.header, keys=old.header.keys(skip='read_only'))
    compare_items(old.data, new.data)

def test_message_eq():
    bufr1 = BUFRMessage(open('./sample-data/synop.bufr'))
    bufr2 = BUFRMessage(open('./sample-data/synop.bufr'))
    assert bufr1 == bufr2
    bufr1['typicalDay'] = 1
    bufr2['typicalDay'] = 2
    assert bufr1.header != bufr2.header
    assert bufr1.data == bufr2.data

def test_message_update():
    bufr = BUFRMessage('BUFR3')
    bufr.update(year=2000)
    bufr.update({'month': 2})
    bufr.update([('day', 4)])
    bufr.update(dict(hour=8, minute=16).items())
    assert bufr['year'] == 2000
    assert bufr['month'] == 2
    assert bufr['day'] == 4
    assert bufr['hour'] == 8
    assert bufr['minute'] == 16

def test_message_get_datetime_compressed():
    bufr = BUFRMessage('BUFR4_local_satellite')
    bufr.update(numberOfSubsets=2)
    datetime = bufr.get_datetime()
    assert isinstance(datetime, np.ndarray)
    assert datetime.size == 2
    assert datetime.all() is np.ma.masked
    bufr.update(year=2000, month=1, day=2, hour=3, minute=4)
    bufr.update(second=[5, CODES_MISSING_LONG])
    datetime = bufr.get_datetime()
    assert isinstance(datetime, np.ndarray)
    assert datetime.size == 2
    assert np.ma.all(datetime == np.array(['2000-01-02T03:04:05', 'NaT'], dtype='M8[s]'))

def test_message_get_datetime_uncompressed():
    bufr = BUFRMessage('BUFR3')
    datetime = bufr.get_datetime()
    assert datetime is np.ma.masked
    bufr.update(year=2000, month=1, day=2, hour=3, minute=4)
    datetime = bufr.get_datetime()
    assert not isinstance(datetime, np.ndarray)
    assert datetime == np.datetime64('2000-01-02T03:04:00')
    datetime = bufr.get_datetime(prefix='typical')
    assert datetime == np.datetime64('2012-10-31T00:02:00')

def test_message_set_datetime_compressed():
    bufr = BUFRMessage('BUFR4_local_satellite')
    # bufr.update(numberOfSubsets=3, unexpandedDescriptors=310008)
    bufr.update(numberOfSubsets=3)
    # Built-in datetime object
    datetime = np.datetime64('2000-01-02T03:04:05', 's').item()
    bufr.set_datetime(datetime)
    assert np.all(bufr['year'] == 2000)
    assert np.all(bufr['month'] == 1)
    assert np.all(bufr['day'] == 2)
    assert np.all(bufr['hour'] == 3)
    assert np.all(bufr['minute'] == 4)
    assert np.all(bufr['second'] == 5)
    # Numpy datetime64 array
    values = ['2000-01-02T03:04:05', '2000-01-02T06:07:08', 'NaT']
    array = np.ma.array(values, dtype='M8[s]', mask=[False, False, True])
    bufr.set_datetime(array)
    assert np.all(bufr['year'] == 2000)
    assert np.all(bufr['month'] == 1)
    assert np.all(bufr['day'] == 2)
    assert np.all(bufr['hour'] == np.array([3, 6, -1]))
    assert np.all(bufr['minute'] == np.array([4, 7, -1]))
    assert np.all(bufr['second'] == np.array([5, 8, -1]))
    # Unless explicitly set by the user, all datetime-related keys from the header
    # section (i.e., typicalYear, typicalMonth, etc.) get updated automatically,
    # whilst packing, based on values from the data section.
    bufr['typicalYear']
    bufr['localYear']
    bufr.pack()
    assert bufr['typicalYear'] == 2000
    assert bufr['typicalMonth'] == 1
    assert bufr['typicalDay'] == 2
    assert bufr['typicalHour'] == 3
    assert bufr['typicalMinute'] == 4
    assert bufr['typicalSecond'] == 5
    assert bufr['localYear'] == 2000
    assert bufr['localMonth'] == 1
    assert bufr['localDay'] == 2
    assert bufr['localHour'] == 3
    assert bufr['localMinute'] == 4
    assert bufr['localSecond'] == 5
    # But respect values of section 1 keys if explicitly set by the user.
    bufr.update(typicalMinute=0, typicalSecond=0)
    bufr.update(localMinute=0, localSecond=0)
    bufr.pack()
    assert bufr['typicalMinute'] == 0
    assert bufr['typicalSecond'] == 0
    assert bufr['localMinute'] == 0
    assert bufr['localSecond'] == 0

def test_message_set_datetime_compressed_irregular():
    bufr = BUFRMessage('BUFR3_local_satellite')
    bufr.update(numberOfSubsets=3)
    assert bufr.get_count('year') == 2
    assert bufr.get_count('month') == 2
    assert bufr.get_count('day') == 2
    assert bufr.get_count('hour') == 10
    assert bufr.get_count('minute') == 9
    assert bufr.get_count('second') == 9
    values = ['2000-01-02T03:04:05', '2000-01-02T06:07:08', 'NaT']
    array = np.ma.array(values, dtype='M8[s]', mask=[False, False, True])
    bufr.set_datetime(array, rank=1)
    assert np.all(bufr['#1#year'] == 2000)
    assert np.all(bufr['#1#month'] == 1)
    assert np.all(bufr['#1#day'] == 2)
    assert np.all(bufr['#1#hour'] == np.array([3, 6, -1]))
    assert np.all(bufr['#1#minute'] == np.array([4, 7, -1]))
    assert np.all(bufr['#1#second'] == np.array([5, 8, -1]))
    assert np.all(bufr['year'][1:]) is np.ma.masked
    assert np.all(bufr['month'][1:]) is np.ma.masked
    assert np.all(bufr['day'][1:]) is np.ma.masked
    assert np.all(bufr['hour'][1:]) is np.ma.masked
    assert np.all(bufr['minute'][1:]) is np.ma.masked
    assert np.all(bufr['second'][1:]) is np.ma.masked
    # Section 1 keys updated whilst packing
    bufr['typicalYearOfCentury']
    bufr.pack()
    assert bufr.get_datetime(prefix='typical') == np.datetime64(values[0])
    assert bufr.get_datetime(prefix='local')   == np.datetime64(values[0])

def test_message_set_datetime_uncompressed():
    bufr = BUFRMessage('BUFR3_local')
    datetime = np.datetime64('2000-01-02T03:04:05', 's').item()
    bufr.set_datetime(datetime)
    assert bufr['year'] == 2000
    assert bufr['month'] == 1
    assert bufr['day'] == 2
    assert bufr['hour'] == 3
    assert bufr['minute'] == 4
    # Section 1 keys updated whilst packing
    bufr['typicalYearOfCentury']
    bufr.pack()
    assert bufr['typicalYearOfCentury'] == 0
    assert bufr['typicalMonth'] == 1
    assert bufr['typicalDay'] == 2
    assert bufr['typicalHour'] == 3
    assert bufr['typicalMinute'] == 4
    assert bufr['typicalSecond'] == 0
