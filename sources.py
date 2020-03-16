#!/usr/bin/env python3



#Sea level models
#NEMO, SHYFEM, ROMS, SHYMED, Kassandra, ISSOS, Tiresias, MFS, AdriaROMS4

#waves models
#Kassandra, Nettuno,Henetus, SWAN,Adriac

#mandatory fields
# source name, type
# model name, engine, ext, filename, fact (BIAS for IBI at Gibraltar, to refer to the geoid)
Sources = [

{
    'name': 'TIDE',
    'type': 'http_login',
    'models': [
        {'name': 'tide', 'engine': 'tide', 'meteo': '---', 'var': 'sea_level', 'ext':'.nc',
         'fact': '0.385',
         'filename': '2/{prefix}_{name}_{var}_{currentdate}{ext}'
         }
    ],
    'url': 'https://iws.ismar.cnr.it/thredds/fileServer/ismar/',
    'username': 'iws' ,
    'password': '6hCala6Hcresce',
    'prefix': 'ismar',
    }
,

{
    'name': 'ISMAR',
    'type': 'http_login',
    'models': [
        {'name': 'tiresias', 'engine': 'shyfem', 'meteo': 'moloch', 'var': 'sea_level', 'ext':'.nc',
         'fact': '0.385',
         'filename': '1/{prefix}_{name}_{var}_{currentdate}{ext}'
         },
        {'name': 'kassandra', 'engine': 'shyfem', 'meteo': 'bolam,moloch', 'var': 'sea_level', 'ext': '.nc',
         'fact': '0.385',
         'filename': '1/{prefix}_{name}_{var}_{currentdate}{ext}'
         },
        {'name': 'issos', 'engine': 'shyfem', 'meteo': 'bolam', 'var': 'sea_level', 'ext': '.nc',
         'filename': '2/{prefix}_{name}_{var}_{currentdate}{ext}'},
        {'name': 'kassandra', 'engine': 'shyfem', 'meteo': 'bolam,moloch', 'var': 'waves', 'ext': '.nc',
         'fact': '0.385',
         'filename': '1/{prefix}_{name}_wave_{currentdate}{ext}'
         },
        #{'name': 'kassandra', 'engine': 'shyfem', 'var': 'waves', 'ext':'.nc', 'filename': '{prefix}_{name}_{var}_{currentdate}{ext}'},

    ],
    'url': 'https://iws.ismar.cnr.it/thredds/fileServer/ismar/',
    'username': 'iws' ,
    'password': '6hCala6Hcresce',
    'prefix': 'ismar',

    }
,
{
    'name': 'CMCC',
    'type': 'script',
    'models': [
        {'name': 'mfs', 'var': 'sea_level','ext': '.nc', 'script': 'cmems-med_sea_level_IWS.sh'},
        {'name': 'mfs', 'var': 'waves','ext': '.nc', 'script': 'cmems-med_waves_IWS.sh'}
    ],
        'url': '',
        'username': '' ,
        'password': '',
        'prefix': 'cmcc',

        }
,
    {
        'name': 'ARSO',
        'type': 'login_ftp',
        'models': [
            {'name':'smmo', 'engine':'nemo', 'meteo':'aladin', 'var':'sea_level', 'ext':'.grb', 'filename': '{engine}_{currentdate}00{ext}'},
            {'name':'smmo', 'engine':'wam', 'meteo':'aladin', 'var':'waves', 'ext':'.grb', 'filename': '{engine}_{currentdate}00{ext}'}
        ],
        'url': 'ftp.arso.gov.si',
        'ftp_dir': 'currentdate',
        'username': 'Istorms' ,
        'password': 'ModelZaOcean18',
        'prefix': 'arso'
        }
,
    {
        'name': 'DHMZ',
        'type': 'login_ftp',
        'models': [
            {'name': 'wwm3', 'engine':'', 'var': 'waves', 'ext': '.nc', 'filename': '{prefix}_{name}_{currentdate}{ext}'}
        ],
        'ftp_dir': 'wwm3',
        'url': '161.53.81.105',
        'username': 'iws' ,
        'password': 'dhmziws1234',
        'prefix': 'dhmz',

        }
,
    {
        'name': 'COVE',
        'type': 'http_login',
        'models': [
            {'name':'shymed','engine': 'shyfem', 'var': 'sea_level', 'ext': '.nc',
             'filename': 'shy/files/{prefix}_{name}00-v03_{var}_{currentdate}00{ext}'}
        ],
        #https://thredds.comune.venezia.it/thredds/fileServer/shy/files/cov_shymed00-v03_sea_level_20191205.nc
        'url': 'https://thredds.comune.venezia.it/thredds/fileServer/',
        'username': 'threddsadmin' ,
        'password': 'threddsstorms',
        'prefix': 'cov',
        'ext': '.nc'
        }
,
    {
        'name': 'ARPAE',
        'type': 'http_login',
        'models': [
            {'name': 'adroms', 'engine':'roms', 'meteo':'cosmo5', 'var': 'sea_level', 'ext': '.grib',
             'filename': '{name}/files/{name}2k_dslm_{currentisodate}T00:00:00{ext}'},
            {'name': 'swanita', 'engine': 'roms', 'meteo': 'cosmo5', 'var': 'mwd_waves', 'ext': '.grib',
             'filename': 'swan/files/{name}_mwd_{currentisodate}T00:00:00{ext}'},
            {'name': 'swanita', 'engine': 'roms', 'meteo': 'cosmo5', 'var': 'mwp_waves', 'ext': '.grib',
             'filename': 'swan/files/{name}_mwp_{currentisodate}T00:00:00{ext}'},
            {'name': 'swanita', 'engine': 'roms', 'meteo': 'cosmo5', 'var': 'pp1d_waves', 'ext': '.grib',
             'filename': 'swan/files/{name}_pp1d_{currentisodate}T00:00:00{ext}'},
            {'name': 'swanita', 'engine': 'roms', 'meteo': 'cosmo5', 'var': 'swh_waves', 'ext': '.grib',
             'filename': 'swan/files/{name}_swh_{currentisodate}T00:00:00{ext}'}
        ],
        #https://thredds.comune.venezia.it/thredds/fileServer/adroms/files/adroms2k_dslm_2019-11-30T00:00:00.grib
        'url': 'https://thredds.comune.venezia.it/thredds/fileServer/',
        'username': 'threddsadmin',
        'password': 'threddsstorms',
        'prefix': 'arpae'
    }
]