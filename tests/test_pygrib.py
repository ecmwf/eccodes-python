def test():
    """
    demonstrates basic pygrib functionality.

    open a grib file, create an iterator.
    >>> import sys, os
    >>> sys.stdout.write('_'); from eccodes import pygrib, codes_samples_path #doctest:+ELLIPSIS
    _...
    >>> grbs = pygrib.open(os.path.join(codes_samples_path(),'gg_sfc_grib2.tmpl'))

    acts like a file object
    >>> grbs.tell()
    0
    >>> grbs.readline()
    1:Temperature:K (instant):reduced_gg:surface:level 0:fcst time 0 hrs:from 200704241200
    >>> grbs.rewind()

    iterate
    >>> for grb in grbs: grb
    1:Temperature:K (instant):reduced_gg:surface:level 0:fcst time 0 hrs:from 200704241200
    >>> print(grb.packingType)
    grid_simple
    >>> print(grb.typeOfGrid)
    reduced_gg

    get the data on the regular gaussian grid (reduced grid expanded
    using linear interpolation by default)
    >>> data = grb.values # values attribute returns the data
    >>> 'shape/min/max data %s %6.2f %6.2f'%(str(data.shape),data.min(),data.max())
    'shape/min/max data (96, 192) 210.71 316.90'
    >>> lats, lons = grb.latlons() # returns lat/lon values on grid.
    >>> str('shape/min/max lats %s %4.2f %4.2f' % (lats.shape,lats.min(),lats.max()))
    'shape/min/max lats (96, 192) -88.57 88.57'
    >>> str('shape/min/max lons %s %4.2f %4.2f' % (lons.shape,lons.min(),lons.max()))
    'shape/min/max lons (96, 192) 0.00 358.12'

    don't expand to regular grid
    >>> grb.expand_grid(False)
    >>> data = grb.values
    >>> 'shape/min/max data %s %6.2f %6.2f'%(str(data.shape),data.min(),data.max())
    'shape/min/max data (13280,) 209.54 316.90'
    >>> lats, lons = grb.latlons() # returns lat/lon values on grid.
    >>> str('shape/min/max lats %s %4.2f %4.2f' % (lats.shape,lats.min(),lats.max()))
    'shape/min/max lats (13280,) -88.57 88.57'
    >>> str('shape/min/max lons %s %4.2f %4.2f' % (lons.shape,lons.min(),lons.max()))
    'shape/min/max lons (13280,) 0.00 358.12'
    >>> grbs.close()
    """

if __name__ == "__main__":
    import doctest
    failure_count, test_count = doctest.testmod(verbose=True)
    from eccodes import pygrib
    import sys
    sys.stdout.write('using ECCODES library version %s\n' % pygrib.grib_api_version)
    if failure_count==0:
        sys.exit(0)
    else:
        sys.exit(1)
