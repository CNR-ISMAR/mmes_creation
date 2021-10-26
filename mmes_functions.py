#!/usr/bin/env python3

import json
import os
import re
from datetime import datetime, timedelta
from subprocess import run

from cdo import Cdo
# imports from local project
from mmes_validate import check_time
from manage import loadconfig

# MMES rotate script


# general variables

# load generl config from json
configfile = os.getcwd() + '/config.json'
Config = loadconfig(configfile)
ensemble_name = Config["ensemble_name"]
data_dir = Config['data_dir']
cdo = Cdo(tempdir=data_dir+'/tmp')

def prepare_forecast_sea_level(source, model, filename, filedate):
    """
    Just after downlading the forecast from provider's server prepare the forecast on the grid
    :param source:
    :param model:
    :param filename:
    :param filedate:
    :return: 0 or error
    """
    proc_filename = os.path.splitext(os.path.basename(filename))[0] + '.nc'
    # change extension for tide model
    if model.system == 'tide':
        proc_filename = os.path.splitext(os.path.basename(filename))[0] + '.tide'
    outputdir = os.path.join(data_dir, 'mmes_components', filedate)
    processedfile = os.path.join(outputdir, proc_filename)
    # create otuput dir if not exists
    if not os.path.isdir(outputdir):
        os.mkdir(outputdir, 0o775)
    if os.path.isfile(processedfile):
        print('prepared file exists, skipping')
        return 0
    else:
        # define dates
        date = datetime.strptime(filedate, "%Y%m%d").strftime("%Y-%m-%d")
        date2 = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        # create Cdo and nco objects and set tmp dir
        cdo.debug = True
        # load processing options
        processing_opt = json.load(open(os.getcwd() + '/processing.json'))
        steps = processing_opt['sea_level_prepare']
        ms = model.system
        tempfile = filename

        # step 1 preapare variables convert to NetCDF if file is .grib
        if ms in steps['variable_selection']:
            varlist = model.var_names
            tempfile = cdo.selvar(varlist, input=tempfile, options="-f nc")
            # set miss value
            miss = model.miss_value
            if miss != '':
                tempfile = cdo.setmissval(miss, input=tempfile)
            # create dictionaries with variable to rename
            new_vars  = Config['ensemble_variables'][model.variable]
            old_vars = model.var_names.split(',')
            if len(new_vars) == len(old_vars):
                rdict = dict(zip(old_vars,new_vars))
                cmd_arguments = ['ncrename']
                for key, value in rdict.items():
                    cmd_arguments.append('-v')
                    cmd_arguments.append(key + ',' + value)
                # in place rename variables
                # example: cmd_arguments = ['ncrename', '-v', 'dslm,sea_level', tempfile]
                cmd_arguments.append(tempfile)
                try:
                    p = run(cmd_arguments)
                except Exception as e:
                    print('error in rename variables: \n' + str(e))
            else:
                msg='Configuration error about var names of model ' + model.system
        # step 2 temporal interpolation
        if ms in steps['temporal_interpolation']:
            # set time axis (already setted for most models
            tempfile = cdo.settaxis(date,"00:00:00","1hour", input=tempfile)
            tempfile = cdo.inttime(date,"00:00:00","1hour", input=tempfile)
        if ms  in steps['get_48hours']:
            # Get fields in the 00-23 time range
            tempfile = cdo.seldate(date+"T00:00:00,"+date2+"T00:00:00", input=tempfile)
        if ms  in steps['add_factor']:
            # subtract factor to otranto bias
            var = model.variable
            fact = model.sea_level_fact
            expr = var +'=' +var +'-'+fact
            tempfile = cdo.expr(expr, input=tempfile)
        # mask before interpolation
        for s in steps['mask_before_interpolation']:
             if ms in s.keys():
                 var = model.variable
                 miss = model.miss_value
                 modmask = s[ms]
                 cmd_arguments = ['ncap2', '-s', var + modmask + '=' + miss +'f;', tempfile]
                 try:
                     p = run(cmd_arguments)
                 except Exception as e:
                     print('error in mask with ncap2: \n' + str(e))
        # spatial interpolatio
        if ms in steps['spatial_interpolation']:
            maskfile = Config['mask_file']
            gridfile = os.path.dirname(maskfile) + Config['ensemble_name'] + '_grid.txt'
            if not os.path.isfile(gridfile):
                write_grid(maskfile,gridfile)
            weightfile = data_dir + '/config/weights/' + '_'.join([source.name,model.system, model.variable])
            if not os.path.isfile(weightfile):
                cdo.gendis(gridfile,input=tempfile,output=weightfile)
            # use cdo remap
            tempfile = cdo.remap(gridfile,weightfile,input=tempfile)

        # extrapolate_missing values
        if ms in steps['extrapolate_missing']:
            tempfile = cdo.fillmiss(input=tempfile)

        # mask_after_interpolation
        for s in steps['mask_after_interpolation']:
            if ms in s.keys():
                var = model.variable
                miss = model.miss_value
                modmask = s[ms]
                cmd_arguments = ['ncap2', '-s', var + modmask + '=' + miss + 'f;', tempfile]
                try:
                    p = run(cmd_arguments)
                except Exception as e:
                    print('error in mask with ncap2: \n' + str(e))
        # mask_outside_area
        if ms in steps['mask_outside_area']:
            maskfile = Config['mask_file']
            tempfile = cdo.mul(input=[maskfile,tempfile], options='-O')
        # add tide
        tide = None
        if ms in steps['add_tide']:
            files = os.listdir(outputdir)
            for f in files:
                if f.endswith('.tide'):
                    tide = outputdir + '/' + f
                    break
            if os.path.isfile(tide):
                    tempfile = cdo.enssum(input=[tide,tempfile])
            else: # tide not processed exit preparation
                msg= ms + ' not processed tide model not available'
                print(msg)
                return
        # copy to destination
        cdo.copy(input=tempfile,output=processedfile)


def prepare_forecast_waves(source, model, filename, filedate):
    """
    Just after downlading the forecast from provider's server prepare the forecast on the grid
    :param source:
    :param model:
    :param filename:
    :param filedate:
    :return: 0 or error
    """
    proc_filename = os.path.splitext(os.path.basename(filename))[0] + '.nc'
    # change extension for tide model
    if model.system == 'tide':
        proc_filename = os.path.splitext(os.path.basename(filename))[0] + '.tide'
    outputdir = os.path.join(data_dir, 'mmes_components', filedate)
    processedfile = os.path.join(outputdir, proc_filename)
    # create otuput dir if not exists
    if not os.path.isdir(outputdir):
        os.mkdir(outputdir, 0o775)
    if os.path.isfile(processedfile):
        print('prepared file exists, skipping')
        return 0
    elif model.system == 'swanita':
        # define dates
        date = datetime.strptime(filedate, "%Y%m%d").strftime("%Y-%m-%d")
        date2 = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        # create Cdo and nco objects and set tmp dir
        cdo.debug = True
        # load processing options
        processing_opt = json.load(open(os.getcwd() + '/processing.json'))
        steps = processing_opt['waves_prepare']
        ms = model.system
        # copy input file to tempfile and convert to NetCDF format
        tempfile = cdo.copy(input=filename, options='-f nc')
        # step 0 merge downloaded components if needed steps['merge'components'] has a list of dictionaries widh model:system
        for st in steps['merge_components']:
            if ms in st.keys():
                # get list of files with model system in the filename
                # to do the merge  must be equal to value setted in st[ms] from processing.json config
                files = [os.path.join(outputdir, f) for f in os.listdir(outputdir)  if re.match(r'.+' + ms + '.+' + filedate + '.+', f)]
                if len(files) == int(st[ms]):
                    tempfile = cdo.merge(input=files)
                else:
                    msg = str(len(files)) + ' of ' + st[ms] + ' files present for model ' + ms
                    print(msg)
        # step 0 extract wave variables in correct order
        if ms in steps['variable_selection']:
            varlist = model.var_names
            tempfile = cdo.selvar(varlist, input=tempfile, options="-f nc")
            # set miss value
            miss = model.miss_value
            if miss != '':
                tempfile = cdo.setmissval(miss, input=tempfile)
            # create dict with variable to rename
            var = model.variable
            rdict = {model.var_names: var}
            # in place rename variables
            cmd_arguments = ['ncrename', '-v', 'dslm,sea_level', tempfile]
            try:
                p = run(cmd_arguments)
            except Exception as e:
                print('error in rename variables: \n' + str(e))
            # step 2 temporal interpolation
        if ms in steps['temporal_interpolation']:
            # set time axis (already setted for most models
            tempfile = cdo.settaxis(date, "00:00:00", "1hour", input=tempfile)
            tempfile = cdo.inttime(date, "00:00:00", "1hour", input=tempfile)
        if ms in steps['get_48hours']:
            # Get fields in the 00-23 time range
            tempfile = cdo.seldate(date + "T00:00:00," + date2 + "T00:00:00", input=tempfile)



    else:
        # TODO port preparation in python
        current_dir = os.getcwd()
        script = current_dir + '/scripts/' + 'IWS_TMES_' + model.variable + '.sh'
        if not os.path.isfile(script):
            print('preparation script not found')
            return
        cmd_arguments = [script, filedate, model.system, filename, processedfile]
        print(' '.join(cmd_arguments))
        try:
            p = run(cmd_arguments, check=True)
        except ChildProcessError:
            print('preaparation failed')

def write_grid(maskfile, gridfile):
    cdo = Cdo()
    with open(gridfile, 'w') as fg:
        content = cdo.griddes(input=maskfile)
        fg.write("\n".join(map(str, content)))


def create_tmes(iws_datadir, var, datestring):
    """ launch the script for merging tmes components based on current variable
     directories are hard coded in crea_tmes_sea_level.sh and crea_tmes_waves.sh
    """
    newtmes = os.path.join(iws_datadir, ensemble_name, ensemble_name + '_' + var + '_' + datestring + '.nc')

    if os.path.isfile(newtmes):
        # raise FileExistsError
        print("File " + newtmes + " already exists, overwriting")
    # launch crea_tmes script
    # TODO port this part in python
    current_dir = os.getcwd()
    script = current_dir + '/scripts/crea_tmes_' + var + '.sh'
    cmd1_arguments = [script,  datestring, newtmes]
    print(' '.join(cmd1_arguments))
    p1 = run(cmd1_arguments, check=True)
    if p1:
        # copy MMES in history collection
        tmesname = ensemble_name + '_' + var + '_' + datestring + '.nc'
        linktmes = os.path.join(iws_datadir, ensemble_name, 'history', tmesname)
        if os.path.exists(newtmes):
            cmd2_arguments = ['cp', newtmes, linktmes]
            p2 = run(cmd2_arguments, check=True)
    return p1.returncode


def archive_tmes(iws_datadir, var, datestring):
    """ Archive a subset of first 24 hours for old
    tmes files """
    tmes_datadir = os.path.join(iws_datadir, ensemble_name)
    # copy subset of old tmes(only 24 hour from forecast time)
    filename = ensemble_name + '_' + var + '_' + str(datestring) + '.nc'
    if os.path.isfile(filename):
        return "File " + filename + " not found exiting"
        # TODO gap filling procedure
    today = (datetime.strptime(datestring, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    newfilename = ensemble_name + '_' + var + '_' + str(today) + '.nc'
    archivedir = 'history'
    # subset_cmd = 'ncks -d time,0,23 MMES_waves_20190511.nc'
    filesrc =  os.path.join(tmes_datadir, filename)
    newfile =  os.path.join(tmes_datadir, newfilename)
    filedest = os.path.join(tmes_datadir, archivedir, filename)
    # split first 24 times for history
    cmd1_arguments = ['ncks', '-O', '-d', 'time,0,23', filesrc, filedest]
    print(cmd1_arguments)
    p1 = run(cmd1_arguments)
    # check if tmes in history is valid
    valid = check_time(filedest, datestring, 24)
    # valid = True
    if not valid and os.path.isfile(filedest):
        os.remove(filedest)
        return 'old tmes not valid removed'
    # check if new tmes is valid
    p2 = check_time(newfile, today, 48)
    if p2 and os.path.isfile(filesrc):
        # delete old file
        os.remove(filesrc)
    else:
        return newfile + 'is not valid MMES'
