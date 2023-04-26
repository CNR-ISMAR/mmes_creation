#!/bin/bash

ifile=$1
fname=$(basename $ifile .grb)

ncl_convert2nc  ${ifile} -v forecast_time0,g0_lat_1,g0_lon_2,SWH_GDS0_MSL,MWP_GDS0_MSL,MWD_GDS0_MSL
ncrename -d g0_lat_1,lat -d g0_lon_2,lon -d forecast_time0,time ${fname}.nc
ncrename -v g0_lat_1,lat -v g0_lon_2,lon -v forecast_time0,time ${fname}.nc

