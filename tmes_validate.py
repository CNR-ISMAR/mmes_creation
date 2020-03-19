#!/usr/bin/env python3
import xarray as xr
import numpy as np
from _datetime import datetime, timedelta
# check
def check_time(file, date_start, shape):
    '''
    Check a netCdf or Grib forecast file against a required time interval
    :param date_start: desired start date of file YYYMMDD format
    :param shape: number of hourly time steps to have a valid file
    :return: true if the file is valid
    '''
    # check if file extension is grib
    ext = os.path.splitext(os.path.basename(filename))[1]
    if ext=='.grib':
        ds = xr.open_dataset(file, engine='cfgrib')
    else:
        ds = xr.open_dataset(file)
    # get first timestamp value and compare with date start and midnight time
    datestring = np.datetime_as_string(ds.variables['time'][0].values)
    first_date = datetime.strptime(datestring.split('T')[0], "%Y-%m-%d")
    first_time =  datestring.split('T')[1]
    if first_date.strftime("%Y%m%d") != date_start or (first_time != "00:00:00.000000000"):
        return False
    # get timesteps and check that are at least 24 hour
    timesteps = ds.variables['time'].size
    if timesteps < shape:
        return False
    return True

#dataset.variables['valid_time'][0].values