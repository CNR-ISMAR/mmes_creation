
#!/usr/bin/env python3
import os, sys
import  json
from _datetime import datetime, timedelta
from tmes_rotate import create_tmes, archive_tmes, prepare_forecast, prepare_grid
from tmes_download import download_ftp, download_http, download_script
from tmes_validate import check_time

#load generl config from json
Config = json.load(open(os.getcwd() + '/config.json'))
sources_file = Config["sources_file"]
#load sources from json TODO create objects not dictionaries
Sources = json.load(open(os.getcwd() + '/' + sources_file))

iws_datadir = Config["data_dir"]
current_dir = os.getcwd()
tmpdir =  iws_datadir + '/tmp/'
today = datetime.now().strftime("%Y%m%d")  # type: str
#today = '20191223'
if len(sys.argv) > 1:
    if isinstance(datetime.strptime(sys.argv[1], "%Y%m%d"), datetime):
        today = sys.argv[1]

yesterday = (datetime.strptime(today, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
#show download progress (use only in debug mode otherwise logging will be verbose)
progress=True

#download ftp and http sources and process forecast
for s in Sources["sources"]:
    #fix sources variables setted to currentdate
    if 'ftp_dir' in s.keys():
        if s['ftp_dir']=='currentdate':
            s['ftp_dir'] = today
    for m in s['models']:
        print(datetime.now().strftime("%Y%m%d %H:%M"))
        print(' '.join((s['name'], m['system'], m['var'])))
        #prepare filename based on source and model information
        if 'source' in m.keys():
            src = m['source']
        else:
            src = s['name']
        filename = os.path.join(iws_datadir, 'forecasts', s['name'],'_'.join([src, m['system'], m['var'], today]) + m['ext'])
        processed_dir = os.path.join(iws_datadir, 'mmes_components') # TODO parametrize model name
        if s['type'] == 'login_ftp':
            download_ftp(s,m, tmpdir, filename, today)
        elif s['type'] in ['http_server', 'http_login']:
            download_http(s, m, filename, today, progress)
        elif s['type'] == 'script':
            download_script(current_dir + '/scripts/', s, m, filename, today)
        if os.path.isfile(filename):
	    #TODO enable validation for downloaded forecast
            #valid = check_time(filename, today, 48)
            valid = True
            if valid:
                if m['var']=='waves':
                    print(filename)
                prepare_forecast(s,m,filename, today, processed_dir, tmpdir)
            else:
                print('invalid file downloaded - deleted')
                os.remove(filename)
            pass

#prepare mmes_components

#rotate
for q in ['sea_level', 'waves']:
    p = create_tmes(iws_datadir, q, today)
    if p == 0:
        archive_tmes(iws_datadir, q, yesterday)


