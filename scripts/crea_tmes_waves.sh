#!/bin/bash  
# set -x

#--------------------------------------------------
Define_date() {
#--------------------------------------------------
  fdate=$1
  [ -n "$1" ] && date=$1
  date=`date -d $fdate +"%Y-%m-%d"`
  date2=`date -d "$date + 1 days" +"%Y-%m-%d"`
}
  
  
#--------------------------------------------------
Define_dir() {
#--------------------------------------------------
  var="waves"
  startdir="/usr3/iwsdata"
  origdir="${startdir}/tmes_components/${fdate}"
  outputdir="/usr3/iwsdata/TMES"
  tmpdir="${startdir}/tmp"

  #models=(KASSANDRA MFS NETTUNO SIMM HENETUS COAWST1km SMMO SWANIT WWMHR)
}
  



##########################################################
#               MAIN
##########################################################
#-------------------------------------------------------------
# Define date
#-------------------------------------------------------------
Define_date $1

#-------------------------------------------------------------
# Define directory name
#-------------------------------------------------------------
Define_dir




files=($origdir/*$var*.nc)
tmesf="${outputdir}/TMES_${var}_${fdate}.nc"
printf '%s\n' "${files[@]}"
echo "tmesfile $tmesf"



for fname in "${files[@]}" ; do

if [ -s "$fname" ]; then
  echo $fname
  #read -n 1 -p   continue?
  f="$(basename -- $fname)"
  cdo expr,"swmd=sin(rad(wmd));cwmd=cos(rad(wmd))" $fname ${tmpdir}/${f}.wmd
  cdo expr,"wsh=wsh;wmp=wmp" $fname ${tmpdir}/${f}.wshmp
  #files+=("${fname}")
fi
done
echo ${encf[@]}


cdo -O --sortname ensmean ${tmpdir}/*.wshmp ${tmpdir}/${var}_${fdate}_mean.nc
cdo -O --sortname ensmean ${tmpdir}/*.wmd ${tmpdir}/${var}_${fdate}_tmp.nc
cdo -O expr,"cwmd=cwmd" ${tmpdir}/${var}_${fdate}_tmp.nc ${tmpdir}/${var}_${fdate}_cwmd.nc
cdo -O expr,"swmd=swmd" ${tmpdir}/${var}_${fdate}_tmp.nc ${tmpdir}/${var}_${fdate}_swmd.nc
cdo -O atan2 ${tmpdir}/${var}_${fdate}_swmd.nc ${tmpdir}/${var}_${fdate}_cwmd.nc ${tmpdir}/${var}_${fdate}_tmp1.nc
cdo -O expr,"wmd_mean=deg(swmd)" ${tmpdir}/${var}_${fdate}_tmp1.nc ${tmpdir}/${var}_${fdate}_tmp2.nc

ncap2 -O -s "where(wmd_mean < 0) wmd_mean = wmd_mean + 360." ${tmpdir}/${var}_${fdate}_tmp2.nc ${tmpdir}/${var}_${fdate}_wmdmean.nc
ncrename -v wmd_mean,wmd-mean ${tmpdir}/${var}_${fdate}_wmdmean.nc
ncrename -v wsh,wsh-mean ${tmpdir}/${var}_${fdate}_mean.nc
ncrename -v wmp,wmp-mean ${tmpdir}/${var}_${fdate}_mean.nc
cdo -O merge ${tmpdir}/${var}_${fdate}_mean.nc ${tmpdir}/${var}_${fdate}_wmdmean.nc ${tmpdir}/${var}_${fdate}_mean1.nc

cdo -O --sortname ensstd ${tmpdir}/*.wshmp ${tmpdir}/${var}_${fdate}_std.nc
ncrename -v wsh,wsh-std ${tmpdir}/${var}_${fdate}_std.nc
ncrename -v wmp,wmp-std ${tmpdir}/${var}_${fdate}_std.nc
cdo -O expr,"wdstd=sqrt(1.-(swmd*swmd+cwmd*cwmd))" ${tmpdir}/${var}_${fdate}_tmp.nc ${tmpdir}/${var}_${fdate}_tmp1.nc
cdo -O expr,"wmd_std=deg(asin(wdstd)*(1.+0.15470054*wdstd^3))" ${tmpdir}/${var}_${fdate}_tmp1.nc ${tmpdir}/${var}_${fdate}_wmdstd.nc
ncrename -v wmd_std,wmd-std ${tmpdir}/${var}_${fdate}_wmdstd.nc 
cdo -O merge ${tmpdir}/${var}_${fdate}_std.nc ${tmpdir}/${var}_${fdate}_wmdstd.nc ${tmpdir}/${var}_${fdate}_std1.nc
cdo -O settabnum,141 ${tmpdir}/${var}_${fdate}_std1.nc ${tmpdir}/${var}_${fdate}_std2.nc
#cdo expr,"uncertaintly=(std/water_level)*100" TMES_${var}_${fdate}.nc
cdo -O merge ${tmpdir}/${var}_${fdate}_mean1.nc ${tmpdir}/${var}_${fdate}_std2.nc ${tmpdir}/${var}_${fdate}_tmp.nc
#rm -f $tmesf
cdo -O setreftime,2019-01-01,00:00:00,hours ${tmpdir}/${var}_${fdate}_tmp.nc $tmesf
MODELS=''
for i in "${files[@]}"
do
   :
   f=${i##*/}
   echo $f
   echo ${f%_waves*}
   MODELS="${MODELS},${f%_waves*}"
done
echo ${MODELS#,}
read -n 1 -p   continue?
# add models list to source attribute
ncatted -O -h -a source,global,o,c,"Ensemble generated from ${#files[@]} models: ${MODELS#,}" $tmesf  

#add standard_names
ncatted -O -a standard_name,wsh-mean,o,c,"sea_surface_wave_significant_height" \
-a standard_name,wsh-std,o,c,"significant_wave_height_std" \
-a long_name,wmp-mean,o,c,"Mean wave period"  -a standard_name,wmp-mean,o,c,"sea_surface_wave_mean_period_from_variance_spectral_density_second_frequency_moment" \
-a long_name,wmp-std,o,c,"Mean wave period" -a standard_name,wmp-std,o,c,"wave_mean_period_std" \
-a long_name,wmd-mean,o,c,"Mean wave direction" -a standard_name,wmd-mean,o,c,"sea_surface_wave_from_direction" \
-a long_name,wmd-std,o,c,"Mean wave direction std" -a standard_name,wmd-std,o,c,"sea_surface_wave_from_direction_devstd" $tmesf
#remove tempo files
rm -f ${tmpdir}/${var}_${fdate}_*.nc*
rm -f ${tmpdir}/*${var}*.nc*
  
