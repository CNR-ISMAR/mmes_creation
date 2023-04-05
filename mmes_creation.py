
# !/usr/bin/env python3
import json
import os
import sys
from _datetime import datetime, timedelta

from manage import readsources
from mmes_download import download_ftp, download_http, download_script
from mmes_functions import create_mmes, archive_tmes, prepare_forecast_sea_level, prepare_forecast_waves
from mmes_validate import check_time


def main(today):
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
            print(datetime.now().strftime("%Y%m%d %H:%M"))
            print(' '.join((s.name, m.system, m.variable)))
            # prepare filename based on source and model information
            if m.source != '':
                src = m.source
            else:
                src = s.name
            basename = '_'.join([src, m.system, m.variable, today]) + m.ext
            filename = os.path.join(iws_datadir, 'forecasts', s.name, basename)
            if s.srctype in ['ftp_login', 'ftp']:
                download_ftp(s, m, tmpdir, filename, today)
            elif s.srctype in ['http_server', 'http_login']:
                download_http(s, m, filename, today, progress)
            elif s.srctype == 'script':
                download_script(current_dir + '/scripts/', s, m, filename, today)
            if os.path.isfile(filename):
                valid = check_time(filename, today, 48)
                if valid:
                    if m.variable.endswith('waves'):
                        print(filename)
#                        prepare_forecast_waves(s, m, filename, today)
                    elif m.variable == 'sea_level':
                        prepare_forecast_sea_level(s, m, filename, today)
                    else:
                        msg = 'Model variable not recognized'
                        print(msg)
                else:
                    print('invalid file downloaded - deleted')
                    os.remove(filename)
    # create tmes and rotate
    psl = create_mmes('sea_level', today)
    pwv = create_mmes('waves', today)
    if psl == 0:
        # check if exists previous tmes if not launch this script with old date as new argument
        p = archive_tmes('sea_level', yesterday)
        if p == 1:
            # gapfilling
            gap_days = int(config['gap_days'])
            if datetime.strptime(yesterday, "%Y%m%d") + timedelta(days=gap_days) <= datetime.now():
                main(yesterday)
    if pwv == 0:
        # check if exists previous tmes if not launch this script with old date as new argument
        p = archive_tmes('waves', yesterday)
        if p == 1:
            # gapfilling
            gap_days = int(config['gap_days'])
            if datetime.strptime(yesterday, "%Y%m%d") + timedelta(days=gap_days) >= datetime.now():
                main(yesterday)


if __name__ == '__main__':

    datestring = datetime.now().strftime("%Y%m%d")  # type: str
    # get datestring from first argument
    if len(sys.argv) > 1:
        if isinstance(datetime.strptime(sys.argv[1], "%Y%m%d"), datetime):
            datestring = sys.argv[1]
    main(datestring)
