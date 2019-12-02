#!/usr/bin/env python3

import os
import shutil
import requests
from requests.auth import HTTPBasicAuth

from datetime import datetime, timedelta
from ftplib import FTP



# general variables

now = datetime.now()
one_day_ago = now -timedelta(days=1)
today = now.strftime("%Y%m%d")
yesterday = one_day_ago.strftime("%Y%m%d")



#today = '20200909'

#Please make a connection to ftp.arso.gov.si
#Username: Istorms
#Password:  ModelZaOcean18

#download a source  via ftp login


def download_ftp(source, model, tmpdir, filename):
    with FTP(source['url']) as ftp:
        try:
            FTP(source['url'])
            ftp.login(source['username'], source['password'])
        except:
            print('could not connect to ' + source['url'])
            return
        if os.path.isfile(filename):
            print('file ' + filename + 'exists skipping')
        else:
            try:
                 ftp.cwd(source['ftp_dir'])
                 _list = ftp.nlst()
            except:
                print('Dir not found')
                return

            for i in _list:
                if today in str(i) and model['name'] in str(i):
                    print('Downlading ' + i )
                    ftp.retrbinary('RETR ' + i, open(tmpdir+ i, 'wb').write)
                    print('done')
                    shutil.copy2(tmpdir + i, filename)
                    print('File copied as ' + filename)
                    os.remove(tmpdir+ i)
                    print(tmpdir + i + 'removed')



def download_http(source, model, filename):
    """

    :rtype: object
    """
    if source['type'] == 'thredds_server':
        downloadfile = source['url']  + '_'.join(([source['prefix'], model['name'], model['quantity'], today])) + source['ext']
        print(downloadfile)
        #TODO add basic autehntication in TDS
        sourceauth = (source['username'], source['password'])
        with requests.get(downloadfile, stream=True) as r:
            if r._content:
                with open(filename, 'wb') as fd:
                    for chunk in r.iter_content(chunk_size=128):
                        fd.write(chunk)






