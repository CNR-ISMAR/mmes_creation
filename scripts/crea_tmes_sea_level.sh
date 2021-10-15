#!/bin/bash  

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
  var="sea_level"
  origdir="/usr3/iwsdata/mmes_components/${fdate}"
  outputdir="/usr3/iwsdata/MMES"
	
  #model	s=(KASSANDRA MFS NETTUNO SIMM HENETUS COAWST1km SMMO SWANIT WWMHR)
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


#-------------------------------------------------------------
# Compute tmes
#-------------------------------------------------------------
# rename tide
mv "$origdir/ismar_tide_sea_level_$date.nc" "$origdir/ismar_tide_sea_level_$date.tide"
echo $fdate
files=($origdir/*$var*.nc)
# tmesf="${outputdir}/MMES_${var}_${fdate}.nc"
tmesf=$2
printf '%s\n' "${files[@]}"
echo "tmesfile $tmesf"

cdo -O ensmean ${files[@]} mean.nc 
ncrename -v ${var},${var}-mean mean.nc 
cdo -O ensstd  ${files[@]} std.nc
ncrename -v ${var},${var}-std std.nc
cdo settabnum,141 std.nc std1.nc
cdo -O merge mean.nc std1.nc tmp.nc
MODELS=''
for i in "${files[@]}"
do
   :
   f=${i##*/}
   echo $f
   echo ${f%_sea_level*}
   MODELS="${MODELS},${f%_sea_level*}"
done
echo ${MODELS#,}
#read -n 1 -p   continue?
cdo -O setreftime,2019-01-01,00:00:00,hours tmp.nc $tmesf
ncatted -O -h -a source,global,o,c,"Ensemble generated from ${#files[@]} models: ${MODELS#,}" $tmesf
#cdo expr,"uncertaintly=(std/${var})*100" MMES_${var}_${fdate}.nc)"
# moved to python tmes_rotate.py
#cp $tmesf ${outputdir}/history/MMES_${var}_${fdate}.nc
rm -f mean.nc std*.nc tmp.nc
slcomment=$(cat ${scriptdir}/sealevel_list.txt)
ncatted -O -h -a comment,global,o,c,"$slcomment" $tmesf
