
# !/usr/bin/env python3
import json
import os
import sys
import argparse
from _datetime import datetime, timedelta

from manage import readsources, selectsource, selectmodel
from mmes_download import download_ftp, download_http, download_script
from mmes_functions import create_mmes, archive_tmes, prepare_forecast_sea_level, prepare_forecast_waves
from mmes_validate import check_time


def main(today, vars, prompt=False):
    # load general config from json
    config = json.load(open(os.getcwd() + '/config.json'))

    # general configuration
    iws_datadir = config["data_dir"]
    current_dir = os.getcwd()
    tmpdir = iws_datadir + '/tmp/'
    # today = '20191223'
    # load sources as object
    sources_file = config["sources_file"]
    sources = readsources(sources_file)
    # if interactive select only one source
    if prompt:
        singlesrc = selectsource(sources)
        sources = [singlesrc]
    # date of previous mmes
    yesterday = (datetime.strptime(today, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
    # show download progress (use only in debug mode otherwise logging will be verbose)
    progress = True
    line = '\n' + '-' * 80 + '\n'
    msg = 'Starting ensemble creation with ' + str(len(sources)) + ' sources. for date ' + today
    print(line + msg + line)
    # download sources and process forecast TODO parallelize processing and start new download
    for s in sources:
        # fix sources variables setted to currentdate
        if 'ftp_dir' in s.__dict__.keys():
            if s.ftp_dir == 'currentdate':
                s.ftp_dir = today
        for m in s.models:
            # skip models not in listed vars
            # composite variables are in the form xxx_waves and sea level is in the form sea_level
            if not (m.variable in vars or m.variable.split('_')[-1] in vars):
                continue
            print(datetime.now().strftime("%Y%m%d %H:%M"))
            print(' '.join((s.name, m.system, m.variable)))
            # prepare filename based on source and model information
            if m.source != '':
                # some models have another source not their provider
                src = m.source
            else:
                src = s.name
            basename = '_'.join([src, m.system, m.variable, today]) + m.ext
            filename = os.path.join(iws_datadir, 'forecasts', s.name, basename)
            # check if file alredy exists otherwise download
            if os.path.isfile(filename):
                print('file ' + filename + ' already exists, dowload skipped')
            else:
                if s.srctype in ['ftp_login', 'ftp']:
                    download_ftp(s, m, tmpdir, filename, today)
                elif s.srctype in ['http_server', 'http_login']:
                    download_http(s, m, filename, today, progress)
                elif s.srctype == 'script':
                    download_script(current_dir + '/scripts/', s, m, filename, today)
            # downlaod can be truncated, check if the file is valid
            if os.path.isfile(filename):
                valid = check_time(filename, today, 48)
                if not valid:
                    print('invalid file downloaded - deleted')
                    os.remove(filename)
                else:
                    if m.variable.endswith('waves'):
                        print(filename)
                        # for multiple files (e.g. wave models) the function prepare_forecast take care of merging
                        prepare_forecast_waves(s, m, filename, today)
                    elif m.variable == 'sea_level':
                        print(filename)
                        prepare_forecast_sea_level(s, m, filename, today)
                    else:
                        msg = 'Model variable not recognized'
                        print(msg)
    # create tmes and rotate
    if 'sea_level' in vars:
        psl = create_mmes('sea_level', today)

        if psl == 0:
            # check if exists previous tmes if not launch this script with old date as new argument
            p = archive_tmes('sea_level', yesterday)
            if p == 1:
                # gapfilling
                gap_days = int(config['gap_days'])
                if datetime.strptime(yesterday, "%Y%m%d") + timedelta(days=gap_days) <= datetime.now():
                    main(yesterday, vars)
    if 'waves' in vars:
        pwv = create_mmes('waves', today)
        if pwv == 0:
            # check if exists previous tmes if not launch this script with old date as new argument
            p = archive_tmes('waves', yesterday)
            if p == 1:
                # gapfilling
                gap_days = int(config['gap_days'])
                if datetime.strptime(yesterday, "%Y%m%d") + timedelta(days=gap_days) >= datetime.now():
                    main(yesterday, vars)


if __name__ == '__main__':
    datestring = datetime.now().strftime("%Y%m%d")  # type: str
    parser = argparse.ArgumentParser(description='Script to create MMES ensemble')
    addhelp='launch with cron or interactively'
    parser.add_argument('-d', '--date', default=datestring, help='date of the ensamble to create in the format AAAAMMDD if null use current date')
    parser.add_argument('-v', '--variable', action='append', choices=['sea_level','waves'], help='Variable to consider (sea_level or waves)')
    parser.add_argument('-i', '--interactive', action='store_true', help='interactive execution from CLI, allow user to choose only one source')
    args = parser.parse_args()
    vars = ['sea_level', 'waves'] if not args.variable else args.variable
    main(args.date, vars, args.interactive )
