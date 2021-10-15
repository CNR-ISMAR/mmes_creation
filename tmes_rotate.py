#!/usr/bin/env python3

import os, json

from subprocess import call, run, CompletedProcess
from datetime import datetime, timedelta
import shutil
import glob

from tmes_validate import check_time

# MMES rotate script


# general variables
#load generl config from json
Config = json.load(open(os.getcwd() + '/config.json'))
ensemble_name = Config["ensemble_name"]
# now = datetime.now()
# one_day_ago = now -timedelta(days=1)
# today = now.strftime("%Y%m%d")
#yesterday = one_day_ago.strftime("%Y%m%d")
#iws_datadir = '/usr3/iwsdata'
#tmes_datadir =  os.path.join(iws_datadir, 'MMES')



def prepare_forecast(source,model, filename, filedate, outdir, tmpdir, mask='MMES_mask_002.nc'):
    '''
    Just after downlading the forecast from provider's server prepare the forecast on the grid
    :param source:
    :param filename:
    :return: 0 or error
    '''
    proc_filename = os.path.splitext(os.path.basename(filename))[0] + '.nc'
    if model['system']=='tide':
        proc_filename = os.path.splitext(os.path.basename(filename))[0] + '.tide'
    outputdir = os.path.join(outdir, filedate)
    processedfile =  os.path.join(outputdir, proc_filename)
    if not os.path.isdir(outputdir):
        os.mkdir(outputdir, 0o775)
    if os.path.isfile(processedfile):
        print('prepared file exists, skipping')
        return 0
    elif model['var']=='sea_level' and 'python' in model.keys():
        #define dates
        date = datetime.strptime(filedate, "%Y%m%d").strftime("%Y-%m-%d")
        date2 = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        fdate = filedate
        #Remove vel,depth, level variables
        cmd1_arguments = ['ncks', '-C', '-x', '-v', 'u_velocity,v_velocity,total_depth,level', filename, tmpdir + 'tmp.nc']
        try:
            p1 = run(cmd1_arguments, check=True)
        except:
            print('command failure:\n' +  ' '.join(cmd1_arguments))
            return
        #Rename variable
        cmd2_arguments = ['ncrename', '-v', 'water_level,'+ model['var'], tmpdir + 'tmp.nc']
        p2 = run(cmd1_arguments, check=True)
        #Temporal interpolation
        cmd3_arguments = ['cdo', 'settaxis,' + date +',00:00:00,3hour', tmpdir + 'tmp.nc', tmpdir + 'tmp1.nc']

        p3 = run(cmd3_arguments, check=True)
        shutil.move(tmpdir + 'tmp1.nc', tmpdir + 'tmp.nc')
        cmd4_arguments = ['cdo', 'inttime,' + date + ',00:00:00,1hour', tmpdir + 'tmp.nc', tmpdir + 'tmp1.nc']
        p4 = run(cmd4_arguments, check=True)
        #Get fields in the 00-23 time range
        cmd5_arguments = ['cdo',  'seldate,' + date + 'T00:00:00,' + date2 + 'T23:00:00', tmpdir + 'tmp1.nc', tmpdir + 'tmp2.nc']
        p5 = run(cmd5_arguments, check=True)
        #Add fact to water level
        cmd6_arguments = ['cdo', 'expr,"' + model['var'] + '=' + model['var'] + '-' + model['fact'] +'"',  tmpdir + 'tmp2.nc', tmpdir + 'tmp3.nc']
        p6 = run(cmd6_arguments)
        #Mask values outside ADRION area
        cmd7_arguments = ['cdo', '-O', 'mul',  mask,  tmpdir + 'tmp3.nc', processedfile]
        p7 = run(cmd7_arguments)
        for i in glob.glob(tmpdir + u'tmp*'):
            os.unlink(i)
        #rm -f out.nc tmp.nc tmp1.nc tmp2.nc tmp3.nc
    else:
        #TODO port preparation in python
        current_dir = os.getcwd()
        script = current_dir + '/scripts/' + 'IWS_TMES_' + model['var'] + '.sh'
        if not os.path.isfile(script):
            print('preparation script not found')
            return
        cmd_arguments = [script, filedate, model['system'], filename, processedfile,]
        print(' '.join(cmd_arguments))
        try:
            p = run(cmd_arguments, check=True)
        except:
            print('preaparation failed')
        pass

def prepare_grid():
    dx = 0.02
    dy = 0.02
    x0 = 12.21
    y0 = 36.67
    x1 = 22.37
    y1 = 45.85
    nx = ((x1-x0)/dx)+1
    ny = ((y1- y0)/dy)+1
    y1 = (y1-dy)

    with open('scripts/remap_grid_ADRION', 'a') as f:
        f.write("gridtype = lonlat\n")
        f.write("xsize = " + str(nx) + "\n")
        f.write("ysize = " + str(ny) + "\n")
        f.write("xfirst = " + str(x0) + "\n")
        f.write("xinc = " + str(dx) + "\n")
        f.write("yfirst = " + str(y0) + "\n")
        f.write("yinc = " + str(dy) + "\n")



def create_tmes(iws_datadir, var, datestring):
    ''' launch the script for merging tmes components based on current variable
     directories are hard coded in crea_tmes_sea_level.sh and crea_tmes_waves.sh
     '''
    newtmes = os.path.join(iws_datadir, ensemble_name, ensemble_name + '_' + var + '_'  + datestring +'.nc')

    if os.path.isfile(newtmes):
        # raise FileExistsError
        print("File " + newtmes + " already exists, overwriting")
    #launch crea_tmes script
    #TODO port this part in python
    current_dir = os.getcwd()
    script= current_dir + '/scripts/crea_tmes_' + var +'.sh'
    cmd1_arguments = [script,  datestring, newtmes]
    print(' '.join(cmd1_arguments))
    p1 = run(cmd1_arguments, check=True)
    if p1:
        #copy MMES in history collection
        linktmes = os.path.join(iws_datadir, ensemble_name,'history', ensemble_name + '_' + var + '_'  + datestring +'.nc')
        if os.path.exists(newtmes):
            cmd2_arguments = ['cp', newtmes, linktmes]
            p2 = run(cmd2_arguments, check=True)
    return  p1.returncode



def archive_tmes(iws_datadir, var, datestring):
    ''' Archive a subset of first 24 hours for old
    tmes files '''
    tmes_datadir = os.path.join(iws_datadir, ensemble_name)
    # copy subset of old tmes(only 24 hour from forecast time)
    filename =  ensemble_name + '_' + var + '_' + str(datestring) + '.nc'
    if os.path.isfile(filename):
        return "File " +  filename + " not found exiting"
        #TODO gap filling procedure
    today = (datetime.strptime(datestring, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    newfilename = ensemble_name + '_' + var + '_' + str(today) + '.nc'
    archivedir = 'history'
    #subset_cmd = 'ncks -d time,0,23 MMES_waves_20190511.nc'
    filesrc =  os.path.join(tmes_datadir, filename)
    newfile =  os.path.join(tmes_datadir, newfilename)
    filedest = os.path.join(tmes_datadir,archivedir, filename)
    # split first 24 times for history
    cmd1_arguments = ['ncks','-O', '-d', 'time,0,23', filesrc, filedest]
    print(cmd1_arguments)
    p1 = run(cmd1_arguments)
    #check if tmes in history is valid
    valid = check_time(filedest, datestring, 24)
    #valid = True
    if not valid and os.path.isfile(filedest):
        os.remove(filedest)
        return 'old tmes not valid removed'
    #check if new tmes is valid
    p2 = check_time(newfile, today, 48)
    if p2 and os.path.isfile(filesrc):
        #delete old file
        os.remove(filesrc)
    else:
        return newfile + 'is not valid MMES'





