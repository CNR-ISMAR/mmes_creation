
#!/usr/bin/env python3
import os, sys
from _datetime import datetime, timedelta
from tmes_rotate import create_tmes, archive_tmes, prepare_forecast, prepare_grid, download_script
from tmes_download import download_ftp, download_http
from tmes_validate import check_time
from sources import Sources


iws_datadir = '/usr3/iwsdata'
tmpdir =  iws_datadir + '/tmp/'
today = datetime.now().strftime("%Y%m%d")  # type: str
#today = '20191223'
if len(sys.argv) > 1:
    if isinstance(datetime.strptime(sys.argv[1], "%Y%m%d"), datetime):
        today = sys.argv[1]

yesterday = (datetime.strptime(today, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")

progress=False
#download ftp and http sources and process forecast
for s in Sources:
    #fix sources variables setted to currentdate
    if 'ftp_dir' in s.keys():
        if s['ftp_dir']=='currentdate':
            s['ftp_dir'] = today
    for m in s['models']:
        print(datetime.now().strftime("%Y%m%d %H:%M"))
        print(' '.join((s['name'], m['name'], m['var'])))
        filename = os.path.join(iws_datadir, 'forecasts', s['name'],'_'.join(([s['prefix'], m['name'], m['var'], today])) + m['ext'])
        processed_dir = os.path.join(iws_datadir, 'tmes_components')
        if s['type'] == 'login_ftp':
            download_ftp(s,m, tmpdir, filename, today)
        elif s['type'] in ['http_server', 'http_login']:
            download_http(s, m, filename, today, progress)
        elif s['type'] == 'script':
            download_script(iws_datadir, s, m, filename, today)
        if os.path.isfile(filename):
	    #TODO enable validation for downloaded forecast
            #valid = check_time(filename, today, 48)
            valid = True
            if valid:
                prepare_forecast(s,m,filename, today, processed_dir, tmpdir)
            else:
                print('invalid file downloaded - deleted')
                os.remove(filename)
            pass

#prepare tmes_components

#rotate
for q in ['sea_level', 'waves']:
    p = create_tmes(iws_datadir, q, today)
    if p == 0:
        archive_tmes(iws_datadir, q, yesterday)


