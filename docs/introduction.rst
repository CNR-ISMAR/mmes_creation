.. _introduction:

Introduction
==============================

Multi model ensemble system (MMES)

This software is intended to collect daily oceanographic forecasts from different sources and create a Multi-model Ensemble. The software is specifically designed to publish NetCDF files about sea-level and waves, but can be configured to manage other variables.

Ocean forecast results are collected by the system every day in the morning: the program contacts each provider of the list, checks if an updated model exists, downloads it and stores it on a local filesystem using one folder for each node with current and historical data. If the updated forecast is not present in the node, the system will pass to the next node and retry later. Once all forecasts available are downloaded, the multi-model builder prepares the data harmonizing all different forecasts. The ensemble creation procedure can be three main task:
1. retrieve and download each single forecast file provided from different sources;
2. process each forecast with appropriate operations;
3. create the ensemble with mean value and estimate error as standard deviation value and archive old ensemble.
At the present stage, the download and processing tasks are executed in sequence for each source and the cycle is repeated at specified intervals, including new available resources. The choice of Python scripts instead of bash shells procedure allows to execute more than one task in parallel shortening the time of the whole cycle. The software is capable of downloading data from ftp or http/https servers using credentials stored in the configuration files or using a custom command to be executed on the system shell. The software can retrieve virtually any kind of source.

