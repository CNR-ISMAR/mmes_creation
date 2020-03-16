#!/usr/bin/env python3

# this is an example file with a Sources array that is used by cron.py
# the cron.py import a sources.py file with this structure

#mandatory fields
# source name, type (ftp_login | http_login | script)
# models:
#   name, engine, ext, fact (BIAS for IBI at Gibraltar, to refer to the geoid),
#   filename: template of downloaded file (to be formatted in download function)
#   script: where source type is script the bash script to download the specified model
# url:  url to retrieve file for ftp and http
# username:
# password:
# prefix: used to identify the source
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
    'username': '**********' ,
    'password': '**********',
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
     ],
    'url': 'https://iws.ismar.cnr.it/thredds/fileServer/ismar/',
    'username': '*********' ,
    'password': '**********',
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
# ,
#     'name': '',
#     'type': '',
#     'models': [
#         {'name': '', 'var': '','ext': '', '': ''},
#         {'name': '', 'var': '', 'ext': '', '': ''},
#     ],
#         'url': '',
#         'username': '' ,
#         'password': '',
#         'prefix': '',
#
#         }
]