
#!/usr/bin/env python3
import os
from _datetime import datetime, timedelta
from tmes_rotate import create_tmes, archive_tmes
from tmes_download import download_ftp, download_http

from sources import Sources


iws_datadir = '/usr3/iwsdata'
tmpdir =  iws_datadir + '/tmp/'
today = datetime.now().strftime("%Y%m%d")  # type: str
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

#download ftp and http sources
for s in Sources:
    for m in s['models']:
        print(datetime.now().strftime("%Y%m%d %H:%M"))
        print(' '.join((s['name'], m['name'], m['quantity'])))
        filename = os.path.join(iws_datadir, 'forecasts', s['name'],'_'.join(([s['prefix'], m['name'], m['quantity'], today])) + s['ext'])
        if s['type'] == 'login_ftp':
            download_ftp(s,m, tmpdir, filename)
        elif s['type'] in ['thredds_server',]:
            download_http(s, m, filename)

#rotate
for q in ['sea_level', 'waves']:
    p = create_tmes(iws_datadir, q, today)
    if p == 0:
        archive_tmes(iws_datadir, q, yesterday)


