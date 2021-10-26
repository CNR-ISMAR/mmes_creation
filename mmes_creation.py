
#!/usr/bin/env python3
import os, sys
import  json
from _datetime import datetime, timedelta
from mmes_functions import create_tmes, archive_tmes, prepare_forecast_sea_level, prepare_forecast_waves, write_grid
from mmes_download import download_ftp, download_http, download_script
from mmes_validate import check_time
from manage import readsources

#load generl config from json
Config = json.load(open(os.getcwd() + '/config.json'))
sources_file = Config["sources_file"]
# general configuration
iws_datadir = Config["data_dir"]
current_dir = os.getcwd()
tmpdir =  iws_datadir + '/tmp/'
today = datetime.now().strftime("%Y%m%d")  # type: str
#today = '20191223'
#load sources from json and convert in a dictionary TODO change to object
sources = [s.__dict__ for s in readsources(sources_file)]
#load sources as object
sources = readsources(sources_file)
if len(sys.argv) > 1:
    if isinstance(datetime.strptime(sys.argv[1], "%Y%m%d"), datetime):
        today = sys.argv[1]
yesterday = (datetime.strptime(today, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
#TODO check if previous mmes exists and make recursive
#show download progress (use only in debug mode otherwise logging will be verbose)
progress=True

#download sources and process forecast TODO parallelize processing and start new download
for s in sources:
    #fix sources variables setted to currentdate
    if 'ftp_dir' in s.__dict__.keys():
        if s.ftp_dir=='currentdate':
            s.ftp_dir = today
    for m in s.models:
        print(datetime.now().strftime("%Y%m%d %H:%M"))
        print(' '.join((s.name, m.system, m.variable)))
        #prepare filename based on source and model information
        if m.source != '':
            src = m.source
        else:
            src = s.name
        filename = os.path.join(iws_datadir, 'forecasts', s.name,'_'.join([src, m.system, m.variable, today]) + m.ext)
        processed_dir = os.path.join(iws_datadir, 'mmes_components') # TODO parametrize model name
        if s.srctype == 'login_ftp':
            download_ftp(s,m, tmpdir, filename, today)
        elif s.srctype in ['http_server', 'http_login']:
            download_http(s, m, filename, today, progress)
        elif s.srctype == 'script':
            download_script(current_dir + '/scripts/', s, m, filename, today)
        if os.path.isfile(filename):
            valid = check_time(filename, today, 48)
            if valid:
                if m.variable.endswith('waves'):
                    print(filename)
                    prepare_forecast_waves(s,m,filename, today)
                elif m.variable =='sea_level':
                    prepare_forecast_sea_level(s,m,filename, today)
                else:
                    msg = 'Model variable not recognized'
            else:
                print('invalid file downloaded - deleted')
                os.remove(filename)


#prepare mmes_components

#rotate
for q in ['sea_level', 'waves']:
    p = create_tmes(iws_datadir, q, today)
    if p == 0:
        archive_tmes(iws_datadir, q, yesterday)


