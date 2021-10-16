# MMES
## Multi Model Ensemble System
MMES ensamble ingestion and creation

This repository contains python script that daily generate the Multi-Model Ensable Sytem (MMES)
from different sources.
The software was originally developed for I-STORMS Web System and further improved within STREAM project.
Also bash scripts are required to process each forecast and compute Ensamble. Bash scripts are in *scripts* folder 

Sources must be defined in sources.json file (refer to sources_template.json to define your list).

## Installation
Clone this repository in a convenient location.
Prepare the data directory structure according to [documentation](https://cnr-ismar.github.io/mmes_creation/_build/html/index.html)
Manually edit config.json according to your needs
From the main directory launch

```
python manage.py new
```

to create a new source config file

```
python manage.py mod
```

to edit existing source config file



