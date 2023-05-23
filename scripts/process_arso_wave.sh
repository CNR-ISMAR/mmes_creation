#!/bin/bash

ifile=$1
fname=$(basename $ifile .grb)
date=$(echo $fname | tr -dc '0-9')

ncl_convert2nc  ${ifile} -v forecast_time0,g0_lat_1,g0_lon_2,SWH_GDS0_MSL,MWP_GDS0_MSL,MWD_GDS0_MSL
ncrename -d g0_lat_1,lat -d g0_lon_2,lon -d forecast_time0,time ${fname}.nc
ncrename -v g0_lat_1,lat -v g0_lon_2,lon -v forecast_time0,time ${fname}.nc

cdo settaxis,${date},00:00:00,1hour ${fname}.nc tmp.nc
mv tmp.nc ${fname}.nc
