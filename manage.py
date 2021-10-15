#!/usr/bin/env python3
import json
import os
import sys
# get sourcesfile from arguments
if os.path.isfile(sys.argv[2]):
    sourcesfile = sys.argv[2]\
else:
    #set it to default
    sourcesfile = 'sources.json'
#template file
templatefile = 'sources_template.json'
configfile = 'config.json'


class Source:
    def __init__(self, fullname, name, srctype, url, ftp_dir, username, password, models):
        self.fullname = fullname
        self.name = name
        self.srctype = srctype
        self.url = url
        self.ftp_dir = ftp_dir
        self.username = username
        self.password = password
        self.models = models


class Model:
    def __init__(self, source, system, name, meteo, var, filename, var_name='', ext=".nc", fact=0, add_tide=False):
        self.source = source.name
        self.system = system
        self.name = name
        self.meteo = meteo
        self.var = var
        self.var_name = var_name
        self.ext = ext
        self.fact = fact
        self.add_tide = add_tide
        self.filename = filename


def readsources(filename):
    sources = json.load(open(os.getcwd() + '/' + filename))['sources']
    return sources


def modsource(srclist, new=False):
    line = '-' * 20 + '\n'
    if new:
        msg = 'Adding a new source to file ' + sourcesfile + '\n'
        print(line + msg + line)
        new = Source("-", "-", "-", "-", "-", "-", "-", [])
        srclist.append(new.__dict__)
        # set current element to last added
        current = sourcelist[-1]
    else:
        # Default: list all sources and let user choose wich modify
        msg = 'Modify existing sources from file '+ sourcesfile + '\n'
        print(line + msg + line)
        while True:
            for i in range(len(srclist)):
                print(str(i) + ' ' + srclist[i]['name'] + ' (' + str(len(srclist[i]['models'])) + ' models)')
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
    # change every key of the source from use input
    for k in current.keys():
        # different condition for key models
        if k == 'models':
            currentmodels = current[k]
            for m in currentmodels:
                modmodel(m)
            # at the end check user input for new model
            prompt = 'Would you like to add a new model for source ' + current["fullname"] + '? [Y/N}'
            add = input(prompt)
            # first adda a new empty model then modify values
            if add[0:1] in ('Y', 'y', 'S', 's'):
                print('Adding new model')
                new = {"system": "--",
                       "name": "--",
                       "meteo": "--",
                       "var": "--",
                       "var_name": "--",
                       "ext": "--",
                       "filename": ""}
                currentmodels.append(new)
                modmodel(current, current['models'][-1])
            elif add[0:1] in ('N','n','S','s'):
                prompt = 'would you like to modify another source? [Y/N]'
                rerun = input(prompt) or 'N'
                if rerun[0:1] in ('Y', 'y', 'S', 's'):
                    modsource(srclist)
                else:
                    saveandexit(srclist)
        else:
            while True:
                # ask for new values for each key
                prompt = 'enter new value for source ' + k + ' (type ? for hint) :' + '[' + current[k] + ']  '
                r = input(prompt)
                if r == '?':
                    print(hints[k])
                    continue
                else:
                    current[k] = r or current[k]
                    break



def modmodel(source, model):
    for k in model.keys():
        while True:
            # ask for new values for each key
            prompt = 'enter new value for model '+ k + '  (type ? for hint) :' + '[' + model[k] + ']'
            r = input(prompt)
            if r == '?':
                print(hints['models'][0][k])
                continue
            else:
                model[k] = input(prompt) or model[k]
                break

def saveandexit(srclist):
    # create dictionary
    srcdict = {"sources": srclist}
    # create file
    with open(sourcesfile, 'w') as fp:
        json.dump(srcdict, fp, indent=4)
        fp.close()
    print('file ' + sourcesfile +  ' saved')

if __name__ == "__main__":
    # read sources from sources file
    sourcelist = []
    for s in readsources(sourcesfile):
        sourcelist.append(s)
    # read sources template for hints
    hints = readsources(templatefile)[0]
    # create dictionary
    sourcesdict = {"sources": sourcelist}
    # create backup
    with open(sourcesfile + '.bak', 'w') as fp:
        json.dump(sourcesdict, fp, indent=4)
        fp.close()

    action = sys.argv[1]
    if action == 'add':
        modsource(sourcelist, True)
    if action == 'mod':
        modsource(sourcelist)
    if action == 'new':
        prompt = "type new filename for sources:"
        sourcesfile = os.path.splitext(input(prompt))[0] + '.json'
        modsource(sourcelist, True)