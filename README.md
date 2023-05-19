# MMES
## Multi Model Ensemble System
MMES ensamble ingestion and creation

This repository contains python script that daily generate the Multi-Model Ensable Sytem (MMES)
from different sources.
The software was originally developed for I-STORMS Web System and further improved within STREAM project.
The software at the moment is tested on GNU/Linux environment running in other OS is not assured
Also bash scripts are required to process each forecast and compute Ensamble. Bash scripts are in *scripts* folder 

Sources must be defined in sources.json file (refer to sources_template.json to define your list).

## Installation
    
1. Create a python [virtualenv](https://docs.python.org/3/library/venv.html) and activate it.
```
python3 -m venv /path/to/new/virtual/environment/mmes
source activate /path/to/new/virtual/environment/mmes/bin/activate
```
2. Clone this repository in a convenient location.


3. Install requirements with

```
pip install -r requirements.txt
```
4. Prepare the data directory structure according to [documentation](https://cnr-ismar.github.io/mmes/_build/html/index.html
5Manually edit **config.json** according to your needs

## Configuration

6. From the main directory launch
```
python manage.py new
```
to create a new source config file
```
python manage.py mod
```
to edit existing source config file

```
python manage.py add
```
to add a new source to current sources config file

## Usage

```
python mmes_creation.py
```
to create a new ensemble for current day and all variables
```
python mmes_creation --help
```
for available options



