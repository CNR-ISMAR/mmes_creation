#!/usr/bin/env python3
# Script to manage configuration files for MMES creation
# --------------------------------------------



import json
import os
import re
import sys
import attr
from subprocess import run
# get sourcesfile from arguments
sourcesfile = 'sources.json'
if sys.argv[2:]:
    if os.path.isfile(sys.argv[2]):
        sourcesfile = sys.argv[2]
# source template file
templatefile = 'sources_template.json'
procfile = 'processing.json'
if not os.path.isfile(procfile):
    procfile = 'processing_template.json'
configfile = 'config.json'



@attr.s
class Source(object):
    # attributes
    fullname = attr.ib(default='')
    name = attr.ib(default='')
    fullname = attr.ib(default='')
    name = attr.ib(default='')
    srctype = attr.ib(default='')
    url = attr.ib(default='')
    ftp_dir = attr.ib(default='')
    username = attr.ib(default='')
    password = attr.ib(default='')
    models = attr.ib(default=[])


@attr.s
class Model(object):
    # attributes
    source = attr.ib(default='')
    system = attr.ib(default='')
    engine = attr.ib(default='')
    meteo_forcing = attr.ib(default='')
    variable = attr.ib(default='')
    var_names = attr.ib(default='')
    miss_value = attr.ib(default='')
    sea_level_add_tide = attr.ib(default='')
    sea_level_fact = attr.ib(default='')
    path = attr.ib(default='')
    ext = attr.ib(default='')
    filename = attr.ib(default='')
    script = attr.ib(default='')
    info = attr.ib(default='')


def loadconfig(file=configfile):
    """
    Load config from file and recursively format parameters {}
    You can declare data_dir and use {data_dir} in subsequent declarations
    :param file: full path of config file
    """
    Config = json.load(open(file))
    # format config itmes with template
    for k,v in Config.items():
        s = str(Config[k])
        p = '{(\w+)}'
        if re.match(p, s):
            Config[k] = Config[k].format(**Config)

    return  Config

def checkdirs():
    Config = loadconfig('config.json')
    # check if default structure exists in data_dir
    data_dir = Config['data_dir']
    cur_dirs = os.listdir(data_dir)
    def_dirs = ['config','config/mask', 'config/weights', 'forecasts', 'mmes_components', 'tmp', Config['ensemble_name'], Config['ensemble_name'] +'/history']
    for d in def_dirs:
        if not os.path.exists(data_dir + '/' + d):
            prompt = 'would you like to create directory ' + data_dir + '/' + d +'?'
            create = input(prompt)
            if create[0:1] in ('Y', 'y', 'S', 's'):
                os.makedirs(data_dir + '/' + d)
                print('dir created')

def checkbin():
    """
    Check if erquired binary are available
    """
    # check cdo
    try:
        from cdo import Cdo
        cdo = Cdo()
    except FileNotFoundError:
        msg = 'cdo binary not found'
        print(msg)
    # check nco
    try:
        cmd_arguments = ['ncap2', '-h']
        p = run(cmd_arguments)
    except FileNotFoundError:
        msg = 'nco binary not found'
        print(msg)


def readsources(filename):
    """
    Load sources from json file and return a list of Source and Model objects
    """
    input_sources = json.load(open(os.getcwd() + '/' + filename))['sources']
    obj_sources = []
    for i in input_sources:
        s = Source(**i)
        obj_models = []
        for m in s.models:
            obj_models.append(Model(**m))
        s.models = obj_models
        obj_sources.append(s)

    return obj_sources


def modsource(srclist, new=False):
    line = '-' * 20 + '\n'
    if new:
        msg = 'Adding a new source to file ' + sourcesfile + '\n'
        print(line + msg + line)
        new = Source()
        srclist.append(new)
        # set current element to last added
        current = sourcelist[-1]
    else:
        # Default: list all sources and let user choose wich modify
        msg = 'Modify existing sources from file '+ sourcesfile + '\n'
        print(line + msg + line)
        while True:
            for i in range(len(srclist)):
                print(str(i) + ' ' + srclist[i].name + ' (' + str(len(srclist[i].models)) + ' models)')
            prompt = 'Which source would you modify? [enter number]'
            try:
                n = int(input(prompt))
            except ValueError:
                print('Enter an integer betwwen 0 and ' + str(len(srclist)-1))
                continue
            if n not in range(len(srclist)):
                print('Invalid value')
            else:
                break
        # current source element from user input
        current = srclist[n]
        msg = 'Editing ' + current.name
        print(line + msg + '\n')
    # change every key of the source from use input
    for k in current.__dict__.keys():
        # different condition for key models
        if k == 'models':
            currentmodels = current.models
            for m in currentmodels:
                msg = "Editing " + m.system + ' from ' + current.fullname + ' - model' + str(currentmodels.index(m)+1) + ' of ' + str(len(currentmodels))
                print(line + msg + '\n')
                modmodel(current, m)
            while True:
                # at the end check user input for new model
                prompt = '\n Would you like to add a new model for source ' + current.fullname + '? [Y/N]'
                add = input(prompt)
                # first add a new empty model then modify values
                if add[0:1] in ('Y', 'y', 'S', 's'):
                    print('Adding new model')
                    new = Model()
                    currentmodels.append(new)
                    modmodel(current, current.models[-1])
                    break
                elif add[0:1] in ('N','n'):
                    prompt = 'would you like to modify another source? [Y/N]'
                    rerun = input(prompt) or 'N'
                    if rerun[0:1] in ('Y', 'y', 'S', 's'):
                        modsource(srclist)
                    else:
                        saveandexit(srclist)
                    break
                else:
                    msg = 'Please type Y or N'
                    print(msg)
                    continue
        else:
            while True:
                # ask for new values for each key
                prompt = 'enter new value for source ' + k + ' (press ? for hint) :' + '[' + current.__dict__[k] + ']  '
                r = input(prompt) or current.__dict__[k]
                if r == '?':
                    print(hints.__dict__[k])
                    continue
                else:
                    current.__dict__[k] = r
                    break


def modmodel(source, model):
    for k in model.__dict__.keys():
        while True:
            # ask for new values for each key
            prompt = 'enter new value for model '+ k + '  (press ? for hint) :' + '[' + model.__dict__[k] + ']'
            r = input(prompt) or model.__dict__[k]
            if r == '?':
                print(hints.models[0].__dict__[k])
                continue
            else:
                model.__dict__[k] = r
                break
    # ask for processing step
    prompt = 'would you like to set processing step for this model? [Y/N]'
    setproc = input(prompt) or 'N'
    if setproc[0:1] in ('Y', 'y', 'S', 's'):
        prep_steps(source, model)



def prep_steps(source, model):
    key = model.variable + '_prepare'
    processing = json.load(open(procfile))
    steps = processing[key]
    processing.pop(key)
    for k, v  in steps.items():
        msg = 'current step for ' + model.variable + ' is ' + k
        print(msg)
        if model.system in steps[k]:
            prompt = model.system + ' is present in ' + k + \
                     '. Do you want to remove it? '
            rmv = input(prompt)
            if rmv[0:1] in ('Y', 'y', 'S', 's'):
                steps[k].remove(model.system)
        else:
            prompt = model.system + ' is NOT present in ' + k + \
                     '. Do you want to add it? '
            apn = input(prompt)
            if apn[0:1] in ('Y', 'y', 'S', 's'):
                steps[k].append(model.system)
    # add modified steps to dictionary
    processing[key] = steps
    # save json file
    with open(procfile, 'w') as fp:
        json.dump(processing, fp, indent=4, default=obj_dict)
    fp.close()

# default function to convert in dictionary all objects
def obj_dict(obj):
    return obj.__dict__


def saveandexit(srclist):
    # create dictionary
    srcdict = {"sources": srclist}
    # create file
    with open(sourcesfile, 'w') as fp:
        json.dump(srcdict, fp, indent=4, default=obj_dict)
    fp.close()
    print('file ' + sourcesfile +  ' saved')

if __name__ == "__main__":
    # read sources from sources file
    sourcelist = readsources(sourcesfile)
    # read sources template for hints
    hints = readsources(templatefile)[0]
    # create dictionary for outer json level
    sourcesdict = {"sources": sourcelist}
    # create backup file
    with open(sourcesfile + '.bak', 'w') as fp:
        json.dump(sourcesdict, fp, indent=4, default=obj_dict)
    fp.close()
    # check action required
    action = sys.argv[1]
    if action == 'add':
        modsource(sourcelist, True)
    if action == 'mod':
        modsource(sourcelist)
    if action == 'new':
        prompt = "type new filename for sources:"
        sourcesfile = os.path.splitext(input(prompt))[0] + '.json'
        sourcelist = readsources(sourcesfile)
        modsource(sourcelist, True)
    if action == 'dir':
        checkdirs()
    if action == 'bin':
        checkbin()