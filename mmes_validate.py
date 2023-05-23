#!/usr/bin/env python3
import os
import re
from _datetime import datetime, timedelta
from cdo import Cdo


# set general objects
cdo = Cdo()


# check time function
def check_time(file, date_start, shape):
    """
    Check a netCdf or Grib forecast file against a required time interval
    :param file: filename (netcdf or grib) to evaluate
    :param date_start: desired start date of file YYYMMDD format
    :param shape: number of hourly time steps to have a valid file
    :return: true if the file is valid
    """
    # check if file exists
    if not os.path.isfile(file):
        return False
    #check if file is empty
    if os.stat(file).st_size == 0:
        return False
    # calculate date_start and date end
    startdate = datetime.strptime(date_start, "%Y%m%d")
    enddate = startdate + timedelta(hours=int(shape)-1)
    # get info from cdo sinfon
    info = cdo.sinfon(input=file)
    # set empty variables
    first_date = last_date = ''
    timesteps = []
    for i in info:
        # match reftime date (always lower then first date
        m1 = re.match(r'RefTime.*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', i)
        if m1:
            try:
                reftime = datetime.strptime(m1.group(1), "%Y-%m-%d %H:%M:%S")

            except ValueError:
                print('Error while finding reftime')
            continue # next loop
            # match all dates in array
        m2 = re.findall(r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})', i)
        if m2:
            try:
                # add all dates to array
                timesteps += [datetime.strptime(d, "%Y-%m-%d %H:%M:%S") for d in m2]
            except ValueError:
                print('Error while finding last date')
            except:
                print('Error in time dimension')
    # get first date and last date
    first_date = min(timesteps)
    last_date = max(timesteps)
    # check if date interval include our interval of interest
    if first_date <= startdate and last_date >= enddate:
        return True
    else:
        return False
