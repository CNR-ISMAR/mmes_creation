#!/usr/bin/bash
# Amedeo Fadini 
# this script expect 3 arguments, filename, outputdir, variable list
# ncl_convert2nc.sh arso_smmo_waves_20230411.grb /usr3/iwsdata/forecasts/arso/ SWH_GDS0_MSL,MWP_GDS0_MSL,MWD_GDS0_MSL
# set -x 
ifile=$1
fname=$(basename $ifile .grb)
date=$(echo $fname | tr -dc '0-9')
outputdir=$2
varlist=$3
# convert grib to netcdf
ncl_convert2nc ${ifile}  -o $outputdir -v forecast_time0,g0_lat_1,g0_lon_2,${varlist}
# rename dimension
ncrename -d g0_lat_1,lat -d g0_lon_2,lon -d forecast_time0,time ${fname}.nc
ncrename -v g0_lat_1,lat -v g0_lon_2,lon -v forecast_time0,time ${fname}.nc
cdo settaxis,${date},00:00:00,1hour ${fname}.nc tmp.nc
mv tmp.nc ${fname}.nc