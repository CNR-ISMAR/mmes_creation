#!/usr/bin/env python3

import os

from subprocess import call, run, CompletedProcess
from datetime import datetime, timedelta


# TMES rotate script


# general variables

# now = datetime.now()
# one_day_ago = now -timedelta(days=1)
# today = now.strftime("%Y%m%d")
#yesterday = one_day_ago.strftime("%Y%m%d")
#iws_datadir = '/usr3/iwsdata'
#tmes_datadir =  os.path.join(iws_datadir, 'TMES')

# TODO create new tmes
#by now just copy old file


def create_tmes(iws_datadir, quantity, datestring):
    ''' By now only check if file with yesterday date
    exists and copy it with new date.
    quantity argument is waves or sea_level '''

    one_day_ago = datetime.strptime(datestring, "%Y%m%d") -timedelta(days=1)
    yesterday = one_day_ago.strftime("%Y%m%d")
    oldtmes = os.path.join(iws_datadir, 'TMES', 'TMES'+ '_' + quantity + '_'  + yesterday+'.nc')
    newtmes = os.path.join(iws_datadir, 'TMES', 'TMES'+ '_' + quantity + '_'  + datestring +'.nc')
    if not os.path.isfile(oldtmes):
        #raise FileNotFoundError
        print ("File " +  oldtmes + " not found.")
        return 1

    else:
        if os.path.isfile(newtmes):
            # raise FileExistsError
            print("File " + newtmes + " already exists, overwriting")
        #copy file and dd last 24 hours

        cmd2_arguments = ['ncap2', '-s', 'time=int(time+24* 3600.)', '-O', oldtmes, newtmes]
        print(cmd2_arguments)
        p = run(cmd2_arguments, check=True)
        return  p.returncode



def archive_tmes(iws_datadir, quantity, datestring):
    ''' Archive a subset of first 24 hours for old
    tmes files '''
    tmes_datadir = os.path.join(iws_datadir, 'TMES')
    # copy subset of old tmes(only 24 hour from forecast time)
    filename =  'TMES_' + quantity + '_' + str(datestring) + '.nc'
    archivedir = 'history'
    #subset_cmd = 'ncks -d time,0,23 TMES_waves_20190511.nc'
    filesrc =  os.path.join(tmes_datadir, filename)
    filedest = os.path.join(tmes_datadir,archivedir, filename)
    cmd_arguments = ['ncks', '-d', 'time,0,23', filesrc, filedest]
    print(cmd_arguments)
    #TODO check if file already exists and in case overwrite
    p = run(cmd_arguments)
    if p.returncode==0:
        #delete old file
        d = run(['rm', filesrc], check=1)
        return d.returncode
    else:
        return 'something went wrong in ncks'





