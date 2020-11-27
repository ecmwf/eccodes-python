"""

Note: The high-level Python interface is currently experimental and may change in a future release.

``GribMessage`` class that implements a GRIB message that allows access to
the message's key-value pairs in a dictionary-like manner and closes the
message when it is no longer needed, coordinating this with its host file.

Author: Daniel Lee, DWD, 2014
"""

from .codesmessage import CodesMessage
from .. import eccodes
import cftime

def julian_to_datetime(jd):
    """
    julian_to_datetime(julday)

    convert Julian day number to python datetime instance.
    """
    return cftime.DateFromJulianDay(jd, calendar='prolpetic_gregorian',
            only_use_cftime_datetimes=False)

# dict for forecast time units (Code Table 4.4).
_ftimedict = {}
_ftimedict[0]='mins'
_ftimedict[1]='hrs'
_ftimedict[2]='days'
_ftimedict[3]='months'
_ftimedict[4]='yrs'
_ftimedict[5]='decades'
_ftimedict[6]='30 yr periods'
_ftimedict[7]='centuries'
_ftimedict[10]='3 hr periods'
_ftimedict[11]='6 hr periods'
_ftimedict[12]='12 hr periods'
_ftimedict[13]='secs'

class IndexNotSelectedError(Exception):
    """GRIB index was requested before selecting key/value pairs."""


class GribMessage(CodesMessage):

    __doc__ = "\n".join(CodesMessage.__doc__.splitlines()[4:]).format(
        prod_type="GRIB", classname="GribMessage", parent="GribFile", alias="grib"
    )

    product_kind = eccodes.CODES_PRODUCT_GRIB

    # Arguments included explicitly to support introspection
    def __init__(
        self,
        codes_file=None,
        clone=None,
        sample=None,
        headers_only=False,
        gribindex=None,
    ):
        """
        Open a message and inform the GRIB file that it's been incremented.

        The message is taken from ``codes_file``, cloned from ``clone`` or
        ``sample``, or taken from ``index``, in that order of precedence.
        """
        grib_args_present = True
        if gribindex is None:
            grib_args_present = False
        super(self.__class__, self).__init__(
            codes_file, clone, sample, headers_only, grib_args_present
        )
        #: GribIndex referencing message
        self.grib_index = None
        if gribindex is not None:
            self.codes_id = eccodes.codes_new_from_index(gribindex.iid)
            if not self.codes_id:
                raise IndexNotSelectedError(
                    "All keys must have selected "
                    "values before receiving message "
                    "from index."
                )
            self.grib_index = gribindex
            gribindex.open_messages.append(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release GRIB message handle and inform file of release."""
        super(self.__class__, self).__exit__(exc_type, exc_val, exc_tb)
        if self.grib_index:
            self.grib_index.open_messages.remove(self)

    def missing(self, key):
        """Report if the value of a key is MISSING."""
        return bool(eccodes.codes_is_missing(self.codes_id, key))

    def set_missing(self, key):
        """Set the value of key to MISSING."""
        eccodes.codes_set_missing(self.codes_id, key)

    @property
    def gid(self):
        """Provided for backwards compatibility."""
        return self.codes_id

    @property
    def grib_file(self):
        """Provided for backwards compatibility."""
        return self.codes_file

    @gid.setter
    def gid(self, val):
        self.codes_id = val

    @grib_file.setter
    def grib_file(self, val):
        self.codes_file = val

    def valid_key(self,key):
        """
        valid_key(key)

        tests whether a grib message object has a specified key,
        it is not missing and it has a value that can be read.
        """
        ret =  key in self.keys()
        # if key exists, but value is missing, return False.
        if ret and self.missing(key): ret = False
        if ret:
            try:
                self[key]
            except:
                ret = False
        return ret

    def __getattr__(self, item):
        # allow gribmessage keys to accessed like attributes.
        # this is tried after looking for item in self.__dict__.keys().
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    def has_key(self,key):
        """
        has_key(key)

        tests whether a grib message object has a specified key.
        """
        if key in self.keys():
            return True
        try:
            self[key]
        except:
            return False
        else:
            return True

    def _set_time_units(self):
        self.fcstimeunits = ""
        if self.has_key('indicatorOfUnitOfTimeRange') and\
           self.indicatorOfUnitOfTimeRange in _ftimedict:
            self.fcstimeunits = _ftimedict[self.indicatorOfUnitOfTimeRange]
        if self.has_key('forecastTime'):
            if self.has_key('forecastTime'):
                ftime = self.forecastTime
            elif self.has_key('stepRange'):
                # if forecastTime doesn't exist, use end of stepRange.
                ftime = self['stepRange'] # computed key, uses stepUnits
                # if it's a range, use the end of the range to define validDate
                try: 
                    ftime = float(ftime.split('-')[1])
                except:
                    ftime = None
        else:
            ftime = 0
        if ftime is None: ftime = 0. # make sure ftime is not None
        if self.has_key('julianDay'):
            # don't do anything if datetime fails (because of a miscoded julianDay)
            try:
                self.analDate =\
                julian_to_datetime(self.julianDay)
            except ValueError:
                pass
            if self.fcstimeunits == 'hrs':
                try:
                    self.validDate =\
                    julian_to_datetime(self.julianDay+ftime/24.)
                except ValueError:
                    pass
            elif self.fcstimeunits == 'mins':
                try:
                    self.validDate =\
                    julian_to_datetime(self.julianDay+ftime/1440.)
                except ValueError:
                    pass
            elif self.fcstimeunits == 'days':
                try:
                    self.validDate =\
                    julian_to_datetime(self.julianDay+ftime)
                except ValueError:
                    pass
            elif self.fcstimeunits == 'secs':
                try:
                    self.validDate =\
                    julian_to_datetime(self.julianDay+ftime/86400.)
                except ValueError:
                    pass
            elif self.fcstimeunits == '3 hr periods':
                try:
                    self.validDate =\
                    julian_to_datetime(self.julianDay+ftime/8.)
                except ValueError:
                    pass
            elif self.fcstimeunits == '6 hr periods':
                try:
                    self.validDate =\
                    julian_to_datetime(self.julianDay+ftime/4.)
                except ValueError:
                    pass
            elif self.fcstimeunits == '12 hr periods':
                try:
                    self.validDate =\
                    julian_to_datetime(self.julianDay+ftime/2.)
                except ValueError:
                    pass

    def __repr__(self):
        """prints a short inventory of the grib message"""
        inventory = []
        messagenumber = self.codes_file.message
        self._set_time_units()
        if self.valid_key('name'):
            if self['name'] != 'unknown':
                inventory.append(repr(messagenumber)+':'+self['name'])
            elif self.valid_key('parameterName'):
                inventory.append(repr(messagenumber)+':'+self['parameterName'])
        if self.valid_key('units'):
            if self['units'] != 'unknown':
                inventory.append(':'+self['units'])
            elif self.valid_key('parameterUnits'):
                inventory.append(':'+self['parameterUnits'])
        if self.valid_key('stepType'):
            inventory.append(' ('+self['stepType']+')')
        if self.valid_key('typeOfGrid') or self.valid_key('gridType'):
            if self.valid_key('typeOfGrid'):
               inventory.append(':'+self['typeOfGrid'])
            else:
               inventory.append(':'+self['gridType'])
        if self.valid_key('typeOfLevel'):
            inventory.append(':'+self['typeOfLevel'])
        if self.valid_key('topLevel') and self.valid_key('bottomLevel'):
            toplev = None; botlev = None
            levunits = 'unknown'
            if self.valid_key('unitsOfFirstFixedSurface'):
                levunits = self['unitsOfFirstFixedSurface']
            if self.valid_key('typeOfFirstFixedSurface') and self['typeOfFirstFixedSurface'] != 255:
                toplev = self['topLevel']
                if self.valid_key('scaledValueOfFirstFixedSurface') and\
                   self.valid_key('scaleFactorOfFirstFixedSurface'):
                   if self['scaleFactorOfFirstFixedSurface']:
                       toplev = self['scaledValueOfFirstFixedSurface']/\
                                np.power(10.0,self['scaleFactorOfFirstFixedSurface'])
                   else:
                       toplev = self['scaledValueOfFirstFixedSurface']
            if self.valid_key('typeOfSecondFixedSurface') and self['typeOfSecondFixedSurface'] != 255:
                botlev = self['bottomLevel']
                if self.valid_key('scaledValueOfSecondFixedSurface') and\
                   self.valid_key('scaleFactorOfSecondFixedSurface'):
                   if self['scaleFactorOfSecondFixedSurface']:
                       botlev = self['scaledValueOfSecondFixedSurface']/\
                                np.power(10.0,self['scaleFactorOfSecondFixedSurface'])
                   else:
                       botlev = self['scaledValueOfSecondFixedSurface']
            levstring = None
            if botlev is None or toplev == botlev:
                levstring = ':level %s' % toplev
            else:
                levstring = ':levels %s-%s' % (toplev,botlev)
            if levunits != 'unknown':
                levstring = levstring+' %s' % levunits
            if levstring is not None:
                inventory.append(levstring)
        elif self.valid_key('level'):
            inventory.append(':level %s' % self['level'])
        if self.valid_key('stepRange'):
            ftime = self['stepRange'] # computed key, uses stepUnits
            if self.valid_key('stepType') and self['stepType'] != 'instant':
                inventory.append(':fcst time %s %s (%s)'%\
                    (ftime,self.fcstimeunits,self.stepType))
            else:
                inventory.append(':fcst time %s %s'% (ftime,self.fcstimeunits))
        elif self.valid_key('forecastTime'):
            ftime = repr(self['forecastTime'])
            inventory.append(':fcst time %s %s'% (ftime,self.fcstimeunits))
        if self.valid_key('dataDate') and self.valid_key('dataTime'):
            inventory.append(
            ':from '+repr(self['dataDate'])+'%04i' % self['dataTime'])
        #if self.valid_key('validityDate') and self.valid_key('validityTime'):
        #    inventory.append(
        #    ':valid '+repr(self['validityDate'])+repr(self['validityTime']))
        if self.valid_key('perturbationNumber') and\
           self.valid_key('typeOfEnsembleForecast'):
            ens_type = self['typeOfEnsembleForecast']
            pert_num = self['perturbationNumber']
            if ens_type == 0:
               inventory.append(":lo res cntl fcst")
            elif ens_type == 1:
               inventory.append(":hi res cntl fcst")
            elif ens_type == 2:
               inventory.append(":neg ens pert %d" % pert_num)
            elif ens_type == 3:
               inventory.append(":pos ens pert %d" % pert_num)
        if self.valid_key('derivedForecast'):
            if self['derivedForecast'] == 0:
                inventory.append(":ens mean")
            elif self['derivedForecast'] == 1:
                inventory.append(":weighted ens mean")
            elif self['derivedForecast'] == 2:
                inventory.append(":ens std dev")
            elif self['derivedForecast'] == 3:
                inventory.append(":normalized ens std dev")
            elif self['derivedForecast'] == 4:
                inventory.append(":ens spread")
            elif self['derivedForecast'] == 5:
                inventory.append(":ens large anomaly index")
            elif self['derivedForecast'] == 6:
                inventory.append(":ens mean of cluster")
        if self.valid_key('probabilityTypeName'):
            inventory.append(":"+self['probabilityTypeName'])
            lowerlim = None
            if self.valid_key('scaledValueOfLowerLimit') and\
               self.valid_key('scaleFactorOfLowerLimit'):
               if self['scaledValueOfLowerLimit'] and\
                  self['scaleFactorOfLowerLimit']: 
                   lowerlim = self['scaledValueOfLowerLimit']/\
                              np.power(10.0,self['scaleFactorOfLowerLimit'])
            upperlim = None
            if self.valid_key('scaledValueOfUpperLimit') and\
               self.valid_key('scaleFactorOfUpperLimit'):
               if self['scaledValueOfUpperLimit'] and\
                  self['scaleFactorOfUpperLimit']: 
                   upperlim = self['scaledValueOfUpperLimit']/\
                              np.power(10.0,self['scaleFactorOfUpperLimit'])
            if upperlim is not None and lowerlim is not None:
                inventory.append(" (%s-%s)" % (upperlim,lowerlim))
            elif upperlim is not None:
                inventory.append(" (> %s)" % upperlim)
            elif lowerlim is not None:
                inventory.append(" (< %s)" % lowerlim)
        return ''.join(inventory)
