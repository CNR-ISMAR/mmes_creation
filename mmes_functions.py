#!/usr/bin/env python3

import json
import os
import signal
import sys
import re
from shutil import copy2
from datetime import datetime, timedelta
from subprocess import run, call, Popen, PIPE, TimeoutExpired

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

def prepare_forecast_sea_level(source, model, filename, filedate, verbose=False):
    """
    Just after downlading the forecast from provider's server prepare the forecast on the grid
    :param source:
    :param model:
    :param filename:
    :param filedate:
    :return: 0 or error
    """
    variable = 'sea_level'
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
        cdo.debug = Config['debug']
        # load processing options
        processing_opt = json.load(open(os.getcwd() + '/processing.json'))
        steps = processing_opt['sea_level_prepare']
        ms = model.system
        tempfile = filename

        # step 1 preapare variables convert to NetCDF if file is .grib
        key = 'variable_selection'
        if ms in steps[key]:
            msg = "processing step:  " +  key
            varlist = model.var_names
            tempfile = cdo.selvar(varlist, input=tempfile, options="-f nc")

            # set miss value
            miss = model.miss_value
            if miss != '':
                tempfile = cdo.setmissval(miss, input=tempfile)
            # create dictionaries with variable to rename
            new_vars  = Config['ensemble_variables'][variable]
            old_vars = model.var_names.split(',')
            if len(new_vars) == len(old_vars):
                rdict = dict(zip(old_vars,new_vars))
                cmd_arguments = ['ncrename']
                for key, value in rdict.items():
                    if key != value: # exclude variables already named
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
            # TODO in case of dry-run print the above command in this form
            # cdo -inttime,2011-01-01,00:00:00,1 hour inputfile outptufile
        if ms  in steps['get_48hours']:
            # Get fields in the 00-23 time range
            tempfile = cdo.seldate(date+"T00:00:00,"+date2+"T23:00:00", input=tempfile)
        if ms  in steps['add_factor']:
            # subtract factor to otranto bias
            var = model.variable
            fact = model.sea_level_fact
            expr = var +'=' +var +'-'+fact
            tempfile = cdo.expr(expr, input=tempfile)
        # mask before interpolation
        for s in steps['dict_mask_before_interpolation']:
             if ms in s.keys():
                 modmask = s[ms]
                 cmd_arguments = ['ncap2', '-s', modmask, tempfile]
                 try:
                     p = run(cmd_arguments)
                 except Exception as e:
                     print('error in mask with ncap2: \n' + str(e))
        # spatial interpolation
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
        for s in steps['dict_mask_after_interpolation']:
            if ms in s.keys():
                modmask = s[ms]
                cmd_arguments = ['ncap2', '-s', modmask , tempfile]
                try:
                    p = run(cmd_arguments)
                except Exception as e:
                    print('error in mask with ncap2: \n' + str(e))
        # mask_outside_area
        if ms in steps['mask_outside_area']:
            maskfile = Config['mask_file']
            tempfile = cdo.mul(input=[maskfile,tempfile], options='-O')
        # add tide
        tide = ''
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


def prepare_forecast_waves(source, model, filename, filedate, verbose=False):
    """
    Just after downlading the forecast from provider's server prepare the forecast on the grid
    :param source:
    :param model:
    :param filename:
    :param filedate:
    :return: 0 or error
    """
    variable = 'waves'
    filedir = os.path.dirname(filename)
    proc_filename = os.path.splitext(os.path.basename(filename))[0] + '.nc'
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
        cdo.debug = Config['debug']
        # load processing options
        processing_opt = json.load(open(os.getcwd() + '/processing.json'))
        steps = processing_opt['waves_prepare']
        ms = model.system
        # step 0 merge downloaded components if needed steps['merge'components'] has a list of dictionaries with model_system: numfiles
        for st in steps['dict_merge_components']:
            if ms in st.keys():
                # get list of files to group with the same source, model system and variable  in the filename
                # prepare filename based on source and model information
                if model.source != '':
                    # some models have another source not their provider
                    src = model.source
                else:
                    src = source.name
                filedir = os.path.dirname(filename)
                pattern = r'.*' + src + '_' + ms + '.*'+ variable + '.*' + filedate
                files = [os.path.join(filedir, f) for f in os.listdir(filedir)  if re.match(pattern, f)]
                # to do the merge  must be equal to value setted in st[ms] from processing.json config
                if len(files) >= int(st[ms]):
                    # replace vars in filename
                    v = model.variable
                    filename = filename.replace('_' + v + '_', '_waves_')
                    processedfile = processedfile.replace('_' + v + '_', '_waves_')
                        # check if merged file was already processed
                    if os.path.isfile(processedfile):
                        print('prepared file exists, skipping')
                        return 0
                    cdo.merge(input=files,output=filename)
                    if verbose:
                        #print step
                        print('**** dict_merge_components ****')
                        #print command
                        print('cdo merge ' + str(files) + '-o' + filename)
                else:
                    msg = str(len(files)) + ' of ' + st[ms] + ' files present for model ' + ms
                    print(msg)
                    return
        # copy input file to tempfile and convert to NetCDF format
        # for grib file use ncl_convert2nc
        # TODO genarilze for all grib or solve
        if model.ext=='.grb' and model.system=='smmo':
            # script style scripts/ncl_convert2nc.sh /usr3/iwsdata/forecasts/arso/arso_smmo_waves_20230411.grb /usr3/iwsdata/forecasts/arso SWH_GDS0_MSL,MWP_GDS0_MSL,MWD_GDS0_MSL
            # command style /usr/bin/ncl_convert2nc /usr3/iwsdata/forecasts/arso/arso_smmo_waves_20230411.grb -o /usr3/iwsdata/forecasts/arso -v forecast_time0,g0_lat_1,g0_lon_2,SWH_GDS0_MSL,MWP_GDS0_MSL,MWD_GDS0_MSL
            script = 'scripts/ncl_convert2nc.sh'
            #set timeout in second
            tmout = 60
            dimensions = 'forecast_time0,g0_lat_1,g0_lon_2,'
            cmd_arguments = ['ncl_convert2nc',  filename, '-o',  filedir,'-v',  dimensions + model.var_names]
            cmdstring = ' '.join(cmd_arguments)
            print(cmdstring)
            try:
                p = Popen(cmd_arguments, start_new_session=True) #TODO check if file already exists
                # wait for suprocess timeut
                p.wait(timeout=tmout)
                # os.remove(filename)
            except TimeoutExpired:
                print(str(tmout) + 'seconds timeout reached')
                print('Terminating the whole process group...', file=sys.stderr)
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                newfile = filename.replace(".grb", ".nc")
                pass
            except Exception as e:
                print('error in convert grib file: \n' + str(e))
                newfile = None
            # when subprocess is finished changhe filename for next step
            if newfile and os.path.isfile(newfile):
                cmd_arguments = ['ncrename', '-d'  'g0_lat_1,lat', '-d', 'g0_lon_2,lon', '-d', 'forecast_time0,time',  newfile]
                cmdstring = ' '.join(cmd_arguments)
                print(cmdstring)
                run(cmd_arguments)
                cmd_arguments = ['ncrename', '-v'  'g0_lat_1,lat', '-v', 'g0_lon_2,lon', '-v', 'forecast_time0,time',  newfile]
                cmdstring = ' '.join(cmd_arguments)
                print(cmdstring)
                run(cmd_arguments)
                tempfile = cdo.settaxis(filedate, "00:00:00", "1hour", input=newfile)
                valid = check_time(tempfile,filedate,48)
                if valid:
                    filename = newfile
                else:
                    print('error in converted file')
            # ARSO smmo file has now this variables
        else:
            # other models not arso
            tempfile = cdo.copy(input=filename, options='-f nc')
        # step 1 extract wave variables in correct order
        if ms in steps['variable_selection']:
            varlist = model.var_names
            tempfile = cdo.selvar(varlist, input=tempfile, options="-f nc")
            # set miss value
            miss = model.miss_value
            if miss != '':
                tempfile = cdo.setmissval(miss, input=tempfile)
            # create dictionaries with variable to rename
            new_vars  = Config['ensemble_variables'][variable]
            old_vars = model.var_names.split(',')
            if len(new_vars) == len(old_vars) and new_vars != old_vars:
                rdict = dict(zip(old_vars,new_vars))
                cmd_arguments = ['ncrename']
                for key, value in rdict.items():
                    cmd_arguments.append('-v')
                    cmd_arguments.append(key + ',' + value)
                # in place rename variables
                # example: cmd_arguments = ['ncrename', '-v', 'dslm,sea_level', tempfile]
                cmd_arguments.append(tempfile)
                cmdstring = ' '.join(cmd_arguments)
                print(cmdstring)
                try:
                    p = run(cmd_arguments)
                except Exception as e:
                    print('error in rename variables: \n' + str(e))
            else:
                msg='Configuration error about var names of model ' + model.system
        # step 2 temporal interpolation
        if ms in steps['temporal_interpolation']:
            # set time axis (already setted for most models
            tempfile = cdo.settaxis(date, "00:00:00", "1hour", input=tempfile)
            tempfile = cdo.inttime(date, "00:00:00", "1hour", input=tempfile)
        # step 3 invert lat
        if ms in steps['invert_latitude']:
            tempfile = cdo.invertlat(input=tempfile)
        # step 4 get only first 48 hours
        if ms in steps['get_48hours']:
            # Get fields in the 00-23 time range
            tempfile = cdo.seldate(date + "T00:00:00," + date2 + "T23:00:00", input=tempfile)
        # step 5 set grid to unstructured this requires a corrispondent file for grid
        if ms in steps['set_grid_unstructured']:
            us_gridfile = data_dir + '/config/weights/' +  ms + '.grid'
            if os.path.isfile(us_gridfile):
                us_gridfile = data_dir + '/config/weights/' + ms + '_' + variable +'.grid'
            if os.path.isfile(us_gridfile):
                tempfile = cdo.setgrid(us_gridfile, input=tempfile)
            else:
                'grid file ' + us_gridfile + 'not found'
        # step 6 spatial interpolation this  requires a corrispondent file for weights
        if ms in steps['spatial_interpolation']:
            maskfile = Config['mask_file']
            int_gridfile = os.path.dirname(maskfile) + '/' + Config['ensemble_name'] + '_grid.txt'
            if not os.path.isfile(int_gridfile):
                write_grid(maskfile,int_gridfile)
            weightfile = data_dir + '/config/weights/' + '_'.join([source.name,model.system, variable])
            if not os.path.isfile(weightfile):
                cdo.gendis(int_gridfile,input=tempfile,output=weightfile)
            # use cdo remap
            tempfile = cdo.remap(int_gridfile,weightfile,input=tempfile)
        # extrapolate_missing values
        if ms in steps['extrapolate_missing']:
            tempfile = cdo.fillmiss(input=tempfile)
        # step 5 mask_after_interpolation
        for s in steps['dict_mask_after_interpolation']:
            if ms in s.keys():
                modmask = s[ms]
                cmd_arguments = ['ncap2', '-s', modmask , tempfile]
                try:
                    p = run(cmd_arguments)
                except Exception as e:
                    print('error in mask with ncap2: \n' + str(e))
        # step 6 mask_outside_area
        if ms in steps['mask_outside_area']:
            maskfile = Config['mask_file']
            tempfile = cdo.mul(input=[maskfile,tempfile])
        # step 7 removes value  equal 0
        if ms in steps['remove_zero_values']:
            tempfile = cdo.setctomiss(0, input=tempfile)
        # copy to destination
        cdo.copy(input=tempfile,output=processedfile)


def write_grid(maskfile, gridfile):
    cdo = Cdo()
    with open(gridfile, 'w') as fg:
        content = cdo.griddes(input=maskfile)
        fg.write("\n".join(map(str, content)))


def create_mmes(var, datestring):
    """ merge tmes components based on current variable
     directories are hard coded
    """
    ensemble_name = Config['ensemble_name']
    iws_datadir = Config['data_dir']
    tmpdir = iws_datadir + '/tmp/'
    filedir = os.path.join(iws_datadir, 'mmes_components', datestring)
    newtmes = os.path.join(iws_datadir, ensemble_name, ensemble_name + '_' + var + '_' + datestring + '.nc')
    if os.path.isfile(newtmes):
        # TODO check if newtmes has new models before overwrite
        print("File " + newtmes + " already exists, overwriting")

    # list all file for var and date - note that tide file has .tide extension not .nc
    pattern = r'.+' + var + '.+' + datestring + '.+nc$'
    files = [os.path.join(filedir, f) for f in os.listdir(filedir) if re.match(pattern, f)]
    # check minimun number of components to use
    min_components = Config['min_components']
    if len(files)<int(min_components):
        msg = 'Too few components. Found  ' + str(len(files)) + ' files for ' + var
        print(msg)
        return 1
    # ---------------- Sea Level creation section ---------------
    if var == 'sea_level':
        # create mean
        tempfile_mean = cdo.ensmean(input=files)
        tempfile_mean = cdo.chname(var,var+'-mean', input=tempfile_mean)
        # create stddev
        tempfile_std = cdo.ensstd(input=files)
        tempfile_std = cdo.chname(var,var+'-std', input=tempfile_std)
        tempfile_std = cdo.settabnum(141,input=tempfile_std) # TODO check why mean doesn't have tabnum
        # last merge
        merged = cdo.merge(input=[tempfile_mean, tempfile_std])
        cdo.setreftime('2019-01-01,00:00:00,hours', input=merged, output=newtmes)
        # add global attribute ensamble description
        ens_desc = get_models(files)
        cmd_arguments = ['ncatted', '-O', '-h', '-a', 'source,global,o,c,"' + ens_desc + '"', newtmes]
        try:
            p = run(cmd_arguments)
        except Exception as e:
            print(e)

    # ---------------- Waves creation section ---------------
    elif var == 'waves':
        #prepare temp files sh line 56-65
        wshp_files=[]
        wmd_files=[]
        for f in files:
            # calculate U end V components for each model
            wmd = cdo.expr('"swmd=sin(rad(wmd));cwmd=cos(rad(wmd))"', input=f)
            wmd_files.append(wmd)
            wshp = cdo.expr('"wsh=wsh;wmp=wmp"', input=f)
            wshp_files.append(wshp)
        # create mean for wave direction sh line 69
        tempfile_mean_wmd = cdo.ensmean(input=wmd_files, options='--sortname')
        # create mean for wave period and height sh line 68
        tempfile_mean_wshp = cdo.ensmean(input=wshp_files, options='--sortname')
        # split waves mean direction into one files per var sh line 70-71
        cwmd = cdo.expr('"cwmd=cwmd"', input=tempfile_mean_wmd)
        swmd = cdo.expr('"swmd=swmd"', input=tempfile_mean_wmd)
        tempfile_mean_wmd_dg = cdo.atan2(input=[swmd,cwmd])
        tempfile_mean_wmd_dg = cdo.expr('"wmd_mean=deg(swmd)"', input=tempfile_mean_wmd_dg)
        # change negative values sh line 75 (use cdo expr instead of ncap2)
        tempfile_mean_wmd_dg = cdo.expr('"wmd_mean=(wmd_mean<0)?(wmd_mean + 360):(wmd_mean)"', input= tempfile_mean_wmd_dg)
        cmd_arguments = ['ncrename', '-v', 'wmd_mean,wmd-mean', tempfile_mean_wmd_dg]
        try:
            p = run(cmd_arguments)
        except Exception as e:
            print(str(e))
        cmd_arguments = ['ncrename', '-v', 'wsh,wsh-mean', '-v', 'wmp,wmp-mean', tempfile_mean_wshp]
        try:
            p = run(cmd_arguments)
        except Exception as e:
            print(str(e))
        # merge mean sh line 79
        merged_mean = cdo.merge(input=[tempfile_mean_wshp, tempfile_mean_wmd_dg])
        # ensemble standard deviation
        tempfile_std_wshp = cdo.ensstd(input=wshp_files, options='--sortname')
        cmd_arguments = ['ncrename', '-v', 'wsh,wsh-std', '-v', 'wmp,wmp-std',  tempfile_std_wshp]
        p = run(cmd_arguments)
        # calculate std deviation from ensamble mean sh line 84
        tempfile_std_wmd = cdo.expr('"wdstd=sqrt(1.-(swmd*swmd+cwmd*cwmd))"', input=tempfile_mean_wmd, options='-O')
        tempfile_std_wmd = cdo.expr('"wmd_std=deg(asin(wdstd)*(1.+0.15470054*wdstd^3))"', input=tempfile_std_wmd, options='-O')
        cmd_arguments = ['ncrename', '-v', 'wmd_std,wmd-std',  tempfile_std_wmd]
        p = run(cmd_arguments)
        merged_std = cdo.merge(input=[tempfile_std_wshp,tempfile_std_wmd])
        merged = cdo.merge(input=[merged_mean,merged_std])
        cdo.setreftime('2019-01-01,00:00:00,hours', input=merged, output=newtmes)
        # add global attributes
        # add global attribute ensamble description
        ens_desc = get_models(files)
        cmd_arguments = ['ncatted', '-O', '-h', '-a', 'source,global,o,c,"' + ens_desc + '"', newtmes]
        try:
            p = run(cmd_arguments)
        except Exception as e:
            print(e)

        # add standard names
        standard_names = {
            "wsh-mean": "sea_surface_wave_significant_height",
            "wsh-std": "sea_surface_wave_significant_height_stdev",
            "wmp-mean": "sea_surface_wave_mean_period",
            "wmp-std": "sea_surface_wave_mean_period_stdev",
            "wmd-mean": "sea_surface_wave_from_direction",
            "wmd-std": "sea_surface_wave_from_direction_stdev"
        }
        for key, value in standard_names.items():
            cmd_arguments = ['ncatted','-O', '-a', 'standard_name,' + key + ',o,c,"' + value + '"', newtmes]
            p = run(cmd_arguments)
        pass
    else:
        msg = 'Unknown variable ' + var + '. Unable to create enesemble'
        print(msg)
    #clean temporary files
    cdo.cleanTempDir()
    # copy MMES in history collection
    tmesname = os.path.basename(newtmes)
    linktmes = os.path.join(iws_datadir, ensemble_name, 'history', tmesname)
    copy2(newtmes,linktmes)
    return 0

def get_models(files):
    # TODO generate source description with date and time of generation models to be used and effectively  used
    # add global attribute about files
    ens_desc = 'Ensemble generated from ' + str(len(files)) + ' models: \n'
    for i in [os.path.basename(f).split('_') for f in files]:
        # get source (0) and system (1) from filename TODO get this from sources object
        ens_desc = ens_desc + i[1] + ' from ' + i[0] + ' \n'
    return ens_desc

def archive_tmes(var, datestring):
    """ Archive a subset of first 24 hours for old
    tmes files """
    tmes_datadir = os.path.join(data_dir, ensemble_name)
    # copy subset of old tmes(only 24 hour from forecast time)
    filename = ensemble_name + '_' + var + '_' + str(datestring) + '.nc'
    today = (datetime.strptime(datestring, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    newfilename = ensemble_name + '_' + var + '_' + str(today) + '.nc'
    archivedir = 'history'
    # subset_cmd = 'ncks -d time,0,23 MMES_waves_20190511.nc'
    filesrc =  os.path.join(tmes_datadir, filename)
    newfile =  os.path.join(tmes_datadir, newfilename)
    filedest = os.path.join(tmes_datadir, archivedir, filename)
    if os.path.isfile(filesrc):
        # split first 24 times for history
        cmd1_arguments = ['ncks', '-O', '-d', 'time,0,23', filesrc, filedest]
        print(' '.join(cmd1_arguments))
        try:
            p1 = run(cmd1_arguments)
        except Exception as e:
            print(str(e))
    elif os.path.isfile(filedest):
        # check if tmes in history is valid
        valid = check_time(filedest, datestring, 24)
        # valid = True
        if not valid:
            os.remove(filedest)
            return 'old tmes not valid removed'
    else:
        msg = "File " + filename + " not found exiting"
        print(msg)
        return 1
        # with return 1 gap filling procedure restart main with yesterday as argument
        # and goes on until a valid old mmes is found in output dir or in history
    # check if new tmes is valid
    p2 = check_time(newfile, today, 48)
    if p2 and os.path.isfile(filesrc):
        # delete old file
        os.remove(filesrc)
    else:
        return newfile + 'is not valid MMES'
