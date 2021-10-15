.. _introduction:

Multi model ensemble system
==============================

This software is intended to collect daily oceanographic forecasts from different sources and create a Multi-model Ensemble. The software is specifically designed to publish NetCDF files about sea-level and waves, but can be configured to manage other variables.


Inputs
+++++++++++

To run the MMES software you need to provide

* a list of sources sources.json: each source can provide one or more models for one or more variable
* a mask file with the final grid you want to get
* [optional] a wheights file for each model that needs to be spatially interpolated to fit the multi-model ansemble
* a small amount of configuration information (directory in which all data will be available, variable to be considered ...)



Directory structure
+++++++++++++++++++
The application directory has python scripts and a subdirectori '''scripts''' with bash scripts used to download special sources or called by subprocess during program execution

The data directory should have the following structure:

| data
| ├── MMES
| │   ├── history
| ├── forecasts
| │   ├── SOURCE1
| │   ├── SOURCE2
| │   ├── SOURCE3
| │   ├── ...
| │   ├── TIDE
| ├── mmes_components
| │   ├── 20211001
| │   ├── 20211002
| │   ├── 20211003
| │   ├── ...
| ├── config
| │   ├── mask
| │   ├── wheights
| ├── tmp

Inside MMES directory will be placed the daily ensemble produced and inside the MMES/history directory will be stored the old ensamble cuted to 24 hour