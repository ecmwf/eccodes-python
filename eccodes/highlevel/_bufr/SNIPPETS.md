# Snippets

This document seeks to compile a collection of code snippets demonstrating common
(but also less common) BUFR-handling tasks, utilising both the low-level and the
high-level interface.

## Reading from file

### The low-level way

Read a single message:

```python
bufr = codes_bufr_new_from_file(file)
```

Iterate over all messages in the file:

```python
while bufr := codes_bufr_new_from_file(file):
    ...
    codes_release(bufr)
```

### The high-level way

Read a single message:

```python
bufr = BUFRMessage(file)
```

Iterate over all messages in the file:

```python
for bufr in FileReader(path, eccodes.CODES_PRODUCT_BUFR):
    ...
```

We can also use Python's `with` statement (aka context manager) to ensure
that `BUFRMessage` resources are properly released after its use:

```python
for bufr in FileReader(path, eccodes.CODES_PRODUCT_BUFR):
    with bufr:
        ...
```

## Accessing items

### The low-level way

Get value of a header key:

```python
value = codes_get(bufr, 'numberOfSubsets')
```

Get value of a data key:

```python
codes_set(bufr, 'unpack', 1)
value = codes_get_array(bufr, 'latitude')
```

### The high-level way

Get value of a header key:

```python
value = bufr['numberOfSubsets']
```

Get value of a data key:

```python
value = bufr['latitude']
```

Note that we didn't need to do explicit unpacking in order to access data section keys.
This was done for us automatically.
However, had we had a needed for a more precise control over when and where the message
gets unpacked, we could do that manually by calling the `unpack()` method:

```python
bufr.unpack()
# guaranteed to be in the unpacked state henceforth
```

After the first invocation, subsequent calls to `unpack()` will have no effect.

## Iterating over items

### The low-level way

```python
codes_set(bufr, 'unpack', 1)
it = codes_bufr_keys_iterator_new(bufr)
while codes_bufr_keys_iterator_next(it):
    key = codes_bufr_keys_iterator_get_name(it)
    try:
        value = codes_get(bufr, key)
    except ArrayTooSmallError:
        value = codes_get_array(bufr, key)
    ...
codes_bufr_keys_iterator_release(it)
```

### The high-level way

```python
for key, value in bufr.items():
    ...
```

## Iterating over data items only

### The low-level way

```python
codes_set(bufr, 'unpack', 1)
it = codes_bufr_keys_iterator_new(bufr)
while codes_bufr_keys_iterator_next(it):
    key = codes_bufr_keys_iterator_get_name(it)
    if codes_bufr_key_is_header(bufr, key):
        continue
    try:
        value = codes_get(bufr, key)
    except ArrayTooSmallError:
        value = codes_get_array(bufr, key)
    ...
codes_bufr_keys_iterator_release(it)
```

### The high-level way

```python
for key, value in bufr.data.items():
    ...
```

## Creating a new message from samples

### The low-level way

Note that 'numberOfSubsets', 'compressedData' and 'input...ReplicationFactor' must
be set _before_ the 'unexpandedDescriptor' key!

```python
bufr = codes_bufr_new_from_samples('BUFR4_local')
codes_set('masterTablesVersionNumber', 18)
codes_set('numberOfSubsets', 5)
codes_set('compressedData', 1)
codes_set_array('inputShortDelayedDescriptorReplicationFactor', [1, 1, 1, 1, 1, 1])
codes_set_array('unexpandedDescriptors', [311010])
```

### The high-level way

The same restrictions apply in the high-level case:

```python
bufr = BUFRMessage('BUFR4_local')
bufr['masterTablesVersionNumber'] = 18
bufr['numberOfSubsets'] = 5
bufr['compressedData'] = 1
bufr['inputShortDelayedDescriptorReplicationFactor'] = [1, 1, 1, 1, 1, 1]
bufr['unexpandedDescriptors'] = [311010]
```

(In the future version of eccodes-python we are planning to relax some of these restrictions.
Specifically, the need to set 'input...ReplicationFactor' upfront.)

## Creating a message copy with ECMWF's local section 2

### The low-level way

```python
old = codes_bufr_new_from_file(foreign_file)
new = codes_bufr_new_from_samples('BUFR4_local_satellite')
# Copy header keys (section 1 only)
it = codes_bufr_keys_iterator_new(old)
codes_skip_read_only(it)
while codes_bufr_keys_iterator_next(it):
    key = codes_bufr_keys_iterator_get_name(it)
    if key == 'unexpandedDescriptors':
        break
    value = codes_get(old, key)
    codes_set(new, value)
# Copy template-related keys
codes_set(old, 'unpack', 1)
value = codes_get_array(old, 'dataPresentIndicator')
codes_set_array(new, 'inputDataPresentIndicator', value)
value = codes_get_array(old, 'delayedDescriptorReplicationFactor')
codes_set_array(new, 'inputDelayedDescriptorReplicationFactor', value)
value = codes_get_array(old, 'unexpandedDescriptors')
codes_set_array(new, 'unexpandedDescriptors', value)
# Copy data keys
codes_copy_data(old, new)
# Set section 2 header keys
...
value = codes_get_array(old, 'latitude')'
codes_set(new, 'localLatitude1', min(value))
codes_set(new, 'localLatitude2', max(value))
...
codes_set(new, 'satelliteID', 123)
```

### The high-level way

```python
old = BUFRMessage(foreign_file)
new = BUFRMessage('BUFR4_local_satellite')
old.copy_to(new)
new['satelliteID'] = 123
```
Note that unlike in the low-level example, we don't need to set every section 2 key
explicitly. The only exception is the 'satelliteID' (or, in the case of uncompressed
messages, the 'ident' key).
All other section 2 keys are set automatically on message packing.

## Iterating over subsets of uncompressed multi-subset messages

### The low-level way

```python
subset_count = codes_get(bufr, 'numberOfSubsets')
codes_set(bufr, 'unpack', 1)
for n in range(1, subset_count + 1):
    print(f'Working on subset {n}')
    block_number = codes_get(bufr, f'/subsetNumber={n}/blockNumber')
    ...
    # BUT THIS IS CURRENTLY NOT ALLOWED!!!
    # pressure1 = codes_get(bufr, f'/subsetNumber={n}/#1#pressure')
    ...
```

### The high-level way

```python
for n, subset in enumerate(bufr.data, start=1):
    print(f'Working on subset {n}')
    block_number = subset['blockNumber']
    ...
    pressure1 = subset['#1#pressure']
    ...
```

## Working with uncompressed multi-subset messages with nested replications

The following is an example of a wind profiler BUFR message (see tests/sample-data/rwp\_jma.bufr).
Each subset in this uncompressed BUFR message represents a unique station.
Within each subset there is one static block at the top which contains some
common metadata, followed by a doubly-nested delayed replication block with
the actual profile data.
The outer replication corresponds to profiles measured at different times, and
the inner replication contains the individual level data for each of the profiles.
The tricky part about this message is that the number of profiles and the number
of levels varies across stations, which means we can't navigate the structure by doing a simple
rank arithmetic.
We have to employ more involved calculations in order to navigate the structure correctly.

### The low-level way

```python
subset_count = codes_get(bufr, 'numberOfSubsets')
codes_set(bufr, 'unpack', 1)
for n in range(1, subset_count + 1):
    codes_set(bufr, 'extractSubset', n)
    codes_set(bufr, 'doExtractSubsets', 1)
    sbufr = codes_clone(bufr)
    codes_set(sbufr, 'unpack', 1)
    # Station info
    ...
    latitude = codes_get(sbufr, 'latitude')
    ...
    factors = codes_get_array(sbufr, 'delayedDescriptorReplicationFactor')
    station_counts = factors[0]
    level_counts = factors[1:]
    assert len(level_counts) == station_counts
    level_offsets = [0] + list(itertools.accumulate(level_counts[:-1]))
    us = codes_get_array(sbufr, 'u')
    vs = codes_get_array(sbufr, 'u')
    ...
    for prof, (off, len) in enumerate(zip(level_offsets, level_counts)):
        # Profile info
        ...
        hour = codes_get_array(sbufr, 'hour')[prof]
        ...
        # Profile data
        ...
        u = np.ma.masked_equal(us[off:off+len], CODES_MISSING_DOUBLE)
        v = np.ma.masked_equal(vs[off:off+len], CODES_MISSING_DOUBLE)
        ...
    codes_release(sbufr)
```

### The high-level way

With the high-level interface, navigating the hierarchical structure is much simpler:

```python
for subset in bufr.data:
    station_info, station_profiles = subset
    # Station info
    ...
    latitude = station_info['latitude']
    ...
    for (profile_info, profile_data) in station_profiles:
        # Profile info
        ...
        hour = profile_info['hour']
        ...
        # Profile data
        ...
        u = profile_data['u']
        ...
```

## Extracting subsets by index

### The low-level way

```python
codes_set(bufr, 'unpack', 1)
codes_set(bufr, 'extractSubsetList',  [2, 4, 8])
codes_set(bufr, 'doExtractSubsets', 1)
new = codes_clone(bufr)
```

### The high-level way

```python
new = bufr.copy(subsets=[1, 3, 7])
```
Note that unlike in the low-level example where we used 1-based subset
numbers, here we use subset indices which are 0-based!

## Extracting subsets by range / slice

### The low-level way

```python
codes_set(bufr, 'unpack', 1)
codes_set(bufr, 'extractSubsetIntervalStart', 2)
codes_set(bufr, 'extractSubsetIntervalEnd',   8)
codes_set(bufr, 'doExtractSubsets', 1)
new = codes_clone(bufr)
```

### The high-level way

```python
new = bufr.copy(subsets=range(1, 9))
```
or
```python
new = bufr.copy(subsets=slice(1, 9))
```
Note that the bounds in the high-level example follow standard Python
convention, whereas in the low-level example they are 1-based and inclusive!

## Extracting subsets by date & time

### The low-level way

```python
codes_set(bufr, 'unpack', 1)
start = datetime(2000, 2, 4, 8, 16)
end = start + timedelta(seconds=32)
for suffix, value in zip(('Start', 'End'), (start, end)):
    codes_set(bufr, 'extractDateTimeYear'   + suffix, value.year)
    codes_set(bufr, 'extractDateTimeMonth'  + suffix, value.month)
    codes_set(bufr, 'extractDateTimeDay'    + suffix, value.day)
    codes_set(bufr, 'extractDateTimeHour'   + suffix, value.hour)
    codes_set(bufr, 'extractDateTimeMinute' + suffix, value.minute)
    codes_set(bufr, 'extractDateTimeSecond' + suffix, value.second)
codes_set(bufr, 'doExtractDateTime', 1)
new = codes_clone(bufr)
```

### The high-level way

```python
start = datetime(2000, 2, 4, 8, 16)
end = start + timedelta(seconds=32)
new = bufr.copy(subsets=slice(start, end))
```
Note that the bounds of datetime slices are inclusive on both sides!

## Extracting subsets within a lat-lon area

### The low-level way

```python
codes_set(bufr, 'unpack', 1)
codes_set(bufr, 'extractAreaNorthLatitude', 64.0)
codes_set(bufr, 'extractAreaSouthLatitude', 32.0)
codes_set(bufr, 'extractAreaEastLongitude', 16.0)
codes_set(bufr, 'extractAreaWestLongitude',  8.0)
codes_set(bufr, 'doExtractArea', 1)
new = codes_clone(bufr)
```

### The high-level way

Unlike in the previous examples, there is no built-in option to extract subsets by area.
However, we can pass an arbitrary boolean mask argument to the `copy()`
method, which provides unlimited flexibility:

```python
lat = bufr['latitude']
lon = bufr['longitude']
lat_mask = np.logical_and(lat <= 64.0, lat >= 32.0)
lon_mask = np.logical_and(lon <= 16.0, lon >=  8.0)
mask = np.logical_and(lat_mask, lon_mask)
new = bufr.copy(subsets=mask)
```

## Thinning subsets

### The low-level way

```python
codes_set(bufr, 'unpack', 1)
codes_set(bufr, 'simpleThinningSkip', 4)
codes_set(bufr, 'doSimpleThinning', 1)
new = codes_clone(bufr)
```
This will extract subset numbers 1, 6, 11, etc.

### The high-level way

Although the high-level interface doesn't provide bespoke option for
the thinning, we can achieve the same by using slices:

```python
new = bufr.copy(subsets=slice(None, None, 5))
```
Note that the slice step must be 1 larger than the thinning step to get the
same result.

## Writing to file

### The low-level way

```python
file = open('output.bufr', 'wb')
codes_set(bufr, 'pack', 1)
codes_write(bufr, file)
```

### The high-level way

```python
file = open('output.bufr', 'wb')
bufr.write_to(file)
```
Notice that in contrast to the low-level example, we didn't need to
pack the message explicitly before writing.
This was done for us automatically.
But, if needed, packing can also be triggered manually at any time by calling
the `pack()` method.
