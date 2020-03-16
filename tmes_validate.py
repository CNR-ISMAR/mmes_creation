#!/usr/bin/env python3
import xarray as xr

# check
def check_time(file, date_start, shape):
    '''
    Check a netCdf or Grib forecast file against a required time interval
    :param date_start: desired start date of file YYYMMDD format
    :param shape: number of hourly time steps to have a valid file
    :return: true if the file is valid
    '''
    pass
#dataset.variables['valid_time'][0].values