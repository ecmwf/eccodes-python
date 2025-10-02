# BUFR Tour

This document showcases some of the features of the high-level BUFR interface.

To follow along make sure you've imported `eccodes.highlevel` module:

```python
>>> from eccodes.highlevel import *
```

### Reading messages from a file

To read a BUFR message from a file, pass the file object to the `BUFRMessage` constructor:

```python
>>> file = open('sample-data/temp.bufr', 'rb'):
>>> bufr = BUFRMessage(file)
>>> bufr
<eccodes.highlevel.BUFRMessage object at 0x7f01e8d52820>
```

Each time we call the `BUFRMessage` constructor (on the same file) we will get
the next BUFR message; that is until we reached the EOF.

A more idiomatic way to iterate through a file is to use the `FileReader` class:

```python
>>> for bufr in FileReader('file.bufr', eccodes.CODES_PRODUCT_BUFR):
        ...
```

Note that we didn't have to release any resources explicitly.
The `BUFRMessage` object, with its underlying C handle, will be released
automatically when collected by the Python's garbage collector.


The `BUFRMessage` object can also be used as a context manager:

```python
>>> for bufr in FileReader('file.bufr', eccodes.CODE_PRODUCT_BUFR):
        with bufr:
            ...
```
This will ensure that `BUFRMessage` resources (including the underlying C handle)
are properly released _right after use_, even in the occurrence of exception.

### Inspecting messages

The most straightforward way to inspect the contents of a BUFR message is by
printing it with the built-in `print()` function:

```python
>>> print(bufr)
...
```
This pretty prints the message in a dict-like representation which is obtain
via the `as_dict()` method.

We can call the `as_dict()` method ourselves, which will return the actual
dictionary, not a string:

```
```python
>>> bufr.as_dict()
...
```
`as_dict()` provides many useful options such as listing keys with their rank
prefixes or changing the depth of expansion of hierarchical data section blocks.

### Getting and setting values

The `BUFRMessage` class provides a dict-like interface for accessing keys and values:

```python
>>> bufr['stationNumber']
60
>>> bufr['someUndefinedKey']
Traceback (most recent call last):
...
eccodes.KeyValueNotFoundError: 'someUndefinedKey'
>> bufr.get('someUndefinedKey', 12345)
12345
```

Note that array values are always returned as masked arrays:

```python
>>> bufr['airTemperature']
masked_array(data=[--, 272.3, --, --, 270.5, --, 266.90000000000003, --,
                   --, --, --, 257.90000000000003, --, --, --, --, --, --,
                   --, --, --, 238.70000000000002, --, --, --, --, --, --,
                   --, 225.3, --],
             mask=[ True, False,  True,  True, False,  True, False,  True,
                    True,  True,  True, False,  True,  True,  True,  True,
                    True,  True,  True,  True,  True, False,  True,  True,
                    True,  True,  True,  True,  True, False,  True],
       fill_value=-1e+100)
```

Individual elements can be accessed using a special key syntax with a rank prefix:

```python
>>> bufr['#2#airTemperature']
272.3
```

Setting values is straightforward:

```python
>>> bufr['airTemperature'] = 273.15
masked_array(data=[273.15, 273.15, 273.15, 273.15, 273.15, 273.15, 273.15,
                   273.15, 273.15, 273.15, 273.15, 273.15, 273.15, 273.15,
                   273.15, 273.15, 273.15, 273.15, 273.15, 273.15, 273.15,
                   273.15, 273.15, 273.15, 273.15, 273.15, 273.15, 273.15,
                   273.15, 273.15, 273.15],
             mask=[False, False, False, False, False, False, False, False,
                   False, False, False, False, False, False, False, False,
                   False, False, False, False, False, False, False, False,
                   False, False, False, False, False, False, False],
       fill_value=-1e+100)
```

We can use the `update()` method to update multiple items at once, for instance:

```python
>>> bufr.update(year=2022, month=11, day=22)
```
Mappings and iterables are also supported:

```python
>>> mapping = {'blockNumber': 12, 'stationNumber': 345}
>>> bufr.update(mapping)
>>> iterable = [('blockNumber', 12), ('stationNumber', 345)]
>>> bufr.update(iterable)
```
Another common use of the `update()` method is to copy items within a given data block
from one message the another:

```python
>>> other = BUFRMessage(open('other.bufr', 'rb'))
>>> bufr.data[1].update(other.data[1])
```

### Iterating over keys & values

We can iterate over the combined header and data keys:

```python
>>> for key in bufr.keys():
...     print(key)
edition
# more header keys...
unexpandedDescriptors
blockNumber
# more data keys...
windSpeed
```

or just over the header (or data) keys separately:

```python
>>> for key in bufr.header.keys():
...     print(key)
edition
# more header keys...
unexpandedDescriptors
>>>
>>> for key in bufr.data.keys():
...     print(key)
blockNumber
# more data keys...
windSpeed
```

We can also iterate over the key-value pairs:

```python
>>> for item in bufr.data.items():
...     print(item)
('blockNumber', 6)
# more data items...
('windSpeed', masked_array(data=[--, 6.0, 12.0, 16.0, 15.0, 14.0, 14.0, 14.0, 12.0,
                   12.0, 12.0, 13.0, 13.0, 13.0, 9.0, 9.0, 9.0, 7.0, 5.0,
                   4.0, 7.0, 7.0, 7.0, 6.0, 7.0, 8.0, 6.0, 6.0, 5.0, 4.0,
                   3.0],
             mask=[ True, False, False, False, False, False, False, False,
                   False, False, False, False, False, False, False, False,
                   False, False, False, False, False, False, False, False,
                   False, False, False, False, False, False, False],
       fill_value=-1e+100))
```

### Selecting items in hierarchically structured messages

If the message contains one or more delayed replications, the data section is divided
into blocks delineated by the replication block bounds.
We can think of blocks as groups of adjacent data section items.
A similar principle applies to uncompressed multi-subset messages where items of
individual subsets are grouped into blocks - one block per subset.
Blocks can also be nested which happens when a message contains nested replications.

This division into blocks is especially useful when working with complex hierarchical
structures where the same item can appear in multiple places in the message.

As an example, let's take the following wind profiler message which has 4 outer
replication blocks.
Each of these blocks represents a different station:

```python
>>> bufr = BUFRMessage(open('sample-data/rwp_jma.bufr', 'rb'))
>>> len(bufr.data)
4
>>> [each['stationNumber'] for each in bufr.data]
[755, 891, 893, 898]
```

Now, each of the outer blocks (stations) has another two inner blocks:

```python
>>> [len(each) for each in bufr.data]
[2, 2, 2, 2]
```

The first sub-block contains station metadata:


```python
# 1st station's 1st sub-block (metadata)
>>> list(bufr.data[0][0].keys())
['blockNumber', 'stationNumber', 'latitude', 'longitude', 'heightOfStation', 'measuringEquipmentType']
```
and the second sub-block represents the profile data:

```python
>>> list(bufr.data[0][1].keys())
['year', 'month', 'day', 'hour', 'minute', 'timeSignificance', 'timePeriod', 'heightAboveStation', 'u', 'v', 'w', 'signalToNoiseRatio']
```

If we now try to get values of, say, key 'u', from the top-level view, we
will be presented with an array which is a concatenation of all values
across all replication blocks (i.e., all profiles of all stations combined together):

```python
>>> bufr.data['u']
masked_array(data=[--, --, --, -6.4, -0.5, --, --, --, -8.5, --, --, --,
                   --, -3.4000000000000004, --, --, --,
                   -5.1000000000000005, --, --, --, --, --, --,
                   0.7000000000000001, --, -5.4, -9.0, -7.7, --, --, --,
#                  ... 300 more values
```
This is not very helpful, though.
In practice, what we really want is values of a particular profile.
The easiest way to do that is to use a subscripting to get hold of the desired data blocks:

```python
>>> station = bufr.data[0]
>>> station_info = station[0]
>>> profile  = station[1]
>>> profile['u']
masked_array(data=[--, --, --, -6.4, -0.5, --, --, --, -8.5, --, --, --,
                   --, -3.4000000000000004, --, --, --,
                   -5.1000000000000005, --, --, --, --, --, --,
                   0.7000000000000001],
             mask=[ True,  True,  True, False, False,  True,  True,  True,
                   False,  True,  True,  True,  True, False,  True,  True,
                    True, False,  True,  True,  True,  True,  True,  True,
                   False],
       fill_value=-1e+100)
```
Just a side note: using rank prefix syntax (e.g., '#1#u') wouldn't help in this case
because each profile can have different number of levels, which makes the computation
of the correct ranks more complicated; we won't get away with a simple arithmetic 
based on rank offsets in this case.
To make this work we would need to calculate the ranks based on the outer and
the inner replication factors, which is tedious and error prone.

### Creating a new message

Let's create a new `BUFRMessage` object from a sample:

```python
>>> bufr = BUFRMessage('BUFR3_local_satellite')
```
Before setting keys from the data section we first need to set the relevant template-related keys:

```python
>>> bufr['masterTablesVersionNumber'] = 18
>>> bufr['numberOfSubsets'] = 5
>>> bufr['compressedData'] = 1
>>> bufr['inputShortDelayedDescriptorReplicationFactor'] = [1, 1, 1, 1, 1, 1]
>>> bufr['unexpandedDescriptors'] = [311010]
```
Note that once the 'unexpandedDescriptors' key has been set, the template is
"baked" and can't be modified afterwards!

After this we can finally proceed with setting the data section keys:

```python
>>> bufr['year'] = 2022
>>> bufr['latitude'] = [45.61, 45.62, 45.63, 45.64, 45.65]
>>> ...
```

Another way of creating new messages is by copying the template from an existing message:

```python
>>> old = BUFRMessage(open('old.bufr', 'rb'))
>>> new = BUFRMessage('BUFR3_local_satellite')
>>> old.copy_to(new, header_only=True)
>>> old['year'] = 2022
>>> ...
```

### Writing to file

To write `BUFRMessage` to a file, use the `write_to()` method.

```python
>>> bufr.write_to(open('output.bufr', 'wb'))
581
```

Use `get_buffer()` to get the contents of the encoded message:

```python
>>> bufr.get_buffer()
b'BUFR\x00...\xc07777'
```

### Copying

We can create a copy of the entire message with all its subsets by calling the
`copy()` method:

```python
>>> new = bufr.copy()
>>> bufr['md5Data']
'8769d91b03a00ee26f1fa1f56bb6284c'
>>> new['md5Data']
'8769d91b03a00ee26f1fa1f56bb6284c'
```

Specific subsets can be extracted by either passing a sequence of (0-based)
subset indices or a slice/range to the `copy()` method:

```python
>>> new1 = bufr.copy(subsets=np.array([0, 2, 4]))
>>> new2 = bufr.copy(subsets=[8, 16, 32])
>>> new3 = bufr.copy(subsets=range(0, 32, 4))
>>> new4 = bufr.copy(subsets=slice(0, 64, 8))
```

For convenience, a subsets slice can also be comprised of built-in `datetime` or numpy
`datetime64` objects, in which case it's interpreted as a date-time range.
Note that that the bounds of such slices are inclusive on both sides.

```python
>>> new = bufr.copy(subsets=slice(datetime(2000, 2, 4, 8), datetime(2000, 2, 4, 16)))
```

### Miscellaneous

Use `get_datetime()` method to get `numpy.datetime64` array whose values are
derived from datetime-related keys (e.g. 'year', 'month', etc.).

```python
>>> bufr = BUFRMessage(open('sample-data/hdob.bufr', 'rb'))
>>> bufr.get_datetime()
masked_array(data=[['2022-05-29T16:00:30', '2022-05-29T16:01:00',
                    '2022-05-29T16:01:30', '2022-05-29T16:02:00',
                    ...
                    '2022-05-29T16:08:30', '2022-05-29T16:09:00',
                    '2022-05-29T16:09:30', '2022-05-29T16:10:00']],
             mask=False,
       fill_value=numpy.datetime64('NaT'),
            dtype='datetime64[s]')
```
