#!/usr/bin/env python3
from datetime import datetime
today = datetime.now().strftime("%Y%m%d")  # type: str

#Sea level models
#NEMO, SHYFEM, ROMS, SHYMED, Kassandra, ISSOS, Tiresias, MFS, AdriaROMS4

#Wave models
#Kassandra, Nettuno,Henetus, SWAN,Adriac

Sources = [
{
    'name': 'ARSO',
    'type': 'login_ftp',
    'models': [
        {'name':'nemo', 'quantity':'sea_level'},
        {'name':'wam', 'quantity':'waves'}
    ],
    'url': 'ftp.arso.gov.si',
    'ftp_dir': today,
    'username': 'Istorms' ,
    'password': 'ModelZaOcean18',
    'prefix': 'arso',
    'ext': '.grb'
    }
,
{
    'name': 'ISMAR',
    'type': 'thredds_server',
'models': [
    {'name': 'tiresias', 'quantity': 'sea_level'},
    {'name': 'kassandra', 'quantity': 'wave'},
    {'name': 'kassandra', 'quantity': 'sea_level'}
],
    'url': 'https://iws.ismar.cnr.it/thredds/fileServer/ismar/',
    'username': 'iws' ,
    'password': '6hCala6Hcresce',
    'prefix': 'ismar',
    'ext': '.nc'
    }
,
{
        'name': 'CMCC',
        'type': 'thredds_server',
    'models': [
        {'name': 'mfs', 'quantity': 'sea_level'}
    ],
        'url': 'https://iws.ismar.cnr.it/thredds/fileServer/ismar/',
        'username': 'iws' ,
        'password': '6hCala6Hcresce',
        'prefix': 'cmcc',
        'ext': '.nc'
        }
,
    {
        'name': 'DHMZ',
        'type': 'login_ftp',
        'models': [
            {'name': 'wwm3', 'quantity': 'wave'}
        ],
        'ftp_dir': 'wwm3',
        'url': '161.53.81.105',
        'username': 'iws' ,
        'password': 'dhmziws1234',
        'prefix': 'dhmz',
        'ext': '.nc'
        }
]