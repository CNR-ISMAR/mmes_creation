#!/bin/bash
#
# Process model output for the MMES. All fields are interpolated
# over the same grid and the same timesteps.
#
# See ../bin/README on how to create a mask

#--------------------------------------------------
Define_dir() {
#--------------------------------------------------
  scriptdir=`dirname "$0"`
  var="sea_level"
  tmesdir="/usr3/iwsdata"
  orgdir="${tmesdir}/forecasts"
  tmpdir="${tmesdir}/tmp"
  outdir="${tmesdir}/mmes_components"
  weidir="${tmesdir}/config/weights"
  mask="${tmesdir}/config/mask/TMES_mask_002.nc"
  declare -Ag models=( ["KASSANDRA"]="shy"
		       ["TIRESIAS"]="shy" 
		       ["SHYMED"]="shy" 
		       ["ISSOS"]="shy" 
		       ["SIMM-E"]="shy" 
		       ["SIMM-B"]="shy" 
		       ["SMMO"]="nc" 
		       ["MFS"]="nc" 
		       ["COAWST1km"]="nc" 
		       ["ADRIAROMS"]="nc" )
}

#--------------------------------------------------
Define_date() {
#--------------------------------------------------
  fdate=`date +%Y%m%d`
  [ -n "$1" ] && fdate=$1
  date=`date -d $fdate +"%Y-%m-%d"`
  date2=`date -d "$date + 1 days" +"%Y-%m-%d"`
  
}

#--------------------------------------------------
Define_grid() {
#--------------------------------------------------
  dx="0.02"
  dy="0.02"
  x0="12.21"
  y0="36.67"
  x1="22.37"
  y1="45.85"
  nx=$(echo "(($x1-$x0)/$dx)+1" | bc)
  ny=$(echo "(($y1-$y0)/$dy)+1" | bc)
  y1=$(echo "($y1-$dy)" | bc)

  ofile="${scriptdir}/remap_grid_ADRION"
  echo "gridtype = lonlat" > $ofile
  echo "xsize    = $nx"   >> $ofile
  echo "ysize    = $ny"   >> $ofile
  echo "xfirst   = $x0"   >> $ofile
  echo "xinc     = $dx"   >> $ofile
  echo "yfirst   = $y0"   >> $ofile
  echo "yinc     = $dy"   >> $ofile
}

#---------------------------------------------------
Process_tide() {			#TIDE simulation
#---------------------------------------------------
  input=$1
  outfil=$2

  #Spatial interpolation 
  #shyelab -out -outformat nc -reg $dx,$dy,$x0,$y0,$x1,$y1 -regexpand 8 $input
  #Remove vel,depth, level variables
  #ncks -C -x -v u_velocity,v_velocity,total_depth,level $input tmp.nc
  #Rename variable 
  #ncrename -v water_level,${var} tmp.nc
  #Get fields in the 00-23 time range
  #cdo seldate,${date}T00:00:00,${date}T23:00:00 tmp.nc tmp1.nc
  #Mask values outside ADRION area
  cdo -O mul $mask ${input} ${outfil}
  #rm -f out.nc tmp.nc tmp1.nc
}

#---------------------------------------------------
Process_kassandra() {			#KASSANDRA forecasts
#---------------------------------------------------
  input=$1
  outfil=$2
  fact="0.385"		#BIAS for IBI at Gibraltar, to refer to the geoid

  #Spatial interpolation 
  #shyelab -out -outformat nc -reg $dx,$dy,$x0,$y0,$x1,$y1 -regexpand 8 $input
  #Remove vel,depth, level variables
  ncks -C -x -v u_velocity,v_velocity,total_depth,level $input tmp.nc
  #Rename variable 
  #ncrename -v water_level,${var} tmp.nc
  #Temporal interpolation 
  cdo settaxis,${date},00:00:00,3hour tmp.nc tmp1.nc
  mv tmp1.nc tmp.nc
  cdo inttime,${date},00:00:00,1hour tmp.nc tmp1.nc
  #Get fields in the 00-23 time range
  cdo seldate,${date}T00:00:00,${date2}T23:00:00 tmp1.nc tmp2.nc
  #Add fact to water level
  cdo expr,"${var}=${var}-$fact" tmp2.nc tmp3.nc
  #Mask values outside ADRION area
  cdo -O mul $mask tmp3.nc ${outfil}
  rm -f out.nc tmp.nc tmp1.nc tmp2.nc tmp3.nc
  #todo: extract file from 00 to 00 of the day after
}

#---------------------------------------------------
Process_shymed() {			#SHYMED forecasts
#---------------------------------------------------
  input=$1
  outfil=$2
  tmp=${tmpdir}/${model}_${var}_tmp

  #Spatial interpolation 
  #shyelab -out -outformat nc -reg $dx,$dy,$x0,$y0,$x1,$y1 -regexpand 8 $input
  #Remove vel,depth, level variables
  #ncks -C -x -v u_velocity,v_velocity,total_depth,level out.nc tmp.nc
  #Rename variable 
  #ncrename -v water_level,${var} tmp.nc
  #Temporal interpolation 
  cdo inttime,${date},00:00:00,1hour $input ${tmp}1.nc
  #Get fields in the 00-23 time range
  cdo seldate,${date}T00:00:00,${date2}T23:00:00 ${tmp}1.nc ${tmp}2.nc
  #Mask values outside ADRION area
  cdo mul $mask ${tmp}2.nc ${tmp}3.nc
  #Add tide
  cdo -O enssum ${orgdir}/ismar/ismar_tide_${var}_${fdate}.nc ${tmp}3.nc ${outfil}
  rm -f ${tmp}*.nc
}

#---------------------------------------------------
Process_tiresias() {			#TIRESIAS forecast
#---------------------------------------------------
  input=$1
  outfil=$2
  tmp=${tmpdir}/${model}_${var}_tmp
  fact="0.2000"		#BIAS for MSF at Otranto, to refer to the geoid

  #Spatial interpolation 
  # shyelab -out -outformat nc -reg $dx,$dy,$x0,$y0,$x1,$y1 -regexpand 5 $input
  #Remove vel,depth, level variables
  ncks -C -x -v u_velocity,v_velocity,total_depth,level $input tmp.nc
  #Rename variable 
  # ncrename -v water_level,${var} tmp.nc
  #Temporal interpolation 
  cdo inttime,${date},00:00:00,1hour tmp.nc tmp1.nc
  #Get fields in the 00-23 time range
  cdo seldate,${date}T00:00:00,${date2}T23:00:00 tmp1.nc tmp2.nc
  #Subtract fact to water level
  cdo expr,"${var}=${var}-$fact" tmp2.nc tmp3.nc
  #Mask values outside ADRION area
  cdo -O mul $mask tmp3.nc ${outfil}
  rm -f out.nc tmp.nc tmp1.nc tmp2.nc tmp3.nc
}

#---------------------------------------------------
Process_issos() {			#ISSOS forecasts
#---------------------------------------------------
  input=$1
  outfil=$2
  tmp=${tmpdir}/${model}_${var}_tmp

  #Spatial interpolation 
  #shyelab -out -outformat nc -reg $dx,$dy,$x0,$y0,$x1,$y1 -regexpand 8 $input
  #Remove vel,depth, level variables
  #ncks -C -x -v u_velocity,v_velocity,total_depth,level $input ${tmp}.nc
  #Rename variable 
  #ncrename -v water_level,${var} ${tmp}.nc
  cp $input ${tmp}.nc
  #Get fields in the 00-23 time range
  cdo seldate,${date}T00:00:00,${date2}T23:00:00 ${tmp}.nc ${tmp}1.nc
  #Mask values outside ADRION area
  cdo mul $mask ${tmp}1.nc ${tmp}2.nc
  #Add tide
  cdo -O enssum ${orgdir}/ismar/ismar_tide_${var}_${fdate}.nc ${tmp}2.nc ${outfil}
  rm -f ${tmp}*
}

#---------------------------------------------------
Process_smmo() {		#SMMO forecasts
#---------------------------------------------------
  input=$1
  outfil=$2
  miss="1.0000e+20"
  fact="0.100"		#BIAS for MSF at Otranto, to refer to the geoid
  tmp=${tmpdir}/${model}_${var}_tmp

  #convert to netcdf
  cdo -f nc copy $input ${tmp}_input.nc
  #remove variables
  cdo selvar,dslm ${tmp}_input.nc ${tmp}_out.nc
  #ncks -C -x -v t,s,ucurr,vcurr input.nc out.nc
  #Set missing value
  cdo setmissval,$miss ${tmp}_out.nc ${tmp}.nc
  #Rename variable 
  ncrename -v dslm,${var} ${tmp}.nc
  #Temporal interpolation 
  cdo settaxis,${date},00:00:00,1hour ${tmp}.nc ${tmp}1.nc
  mv ${tmp}1.nc ${tmp}.nc
  cdo inttime,${date},00:00:00,1hour ${tmp}.nc ${tmp}1.nc
  #Get fields in the 00-23 time range
  cdo seldate,${date}T00:00:00,${date2}T23:00:00 ${tmp}1.nc ${tmp}2.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss ${tmp}2.nc ${tmp}3.nc
  #Spatial interpolation 
  #cdo gendis,remap_grid_ADRION tmp3.nc ${weidir}/SMMO_weights.nc 
  cdo remap,${scriptdir}/remap_grid_ADRION,${weidir}/SMMO_${var}_weights.nc ${tmp}3.nc ${tmp}4.nc
  #Subtract fact to water level
  cdo expr,"${var}=${var}-$fact" ${tmp}4.nc ${tmp}5.nc
  #Mask values belowe 39 to missing value
  ncap2 -O -v -s "${var}(:, 0:117, 0:508)=$miss;" ${tmp}5.nc ${tmp}6.nc
  #Mask values outside ADRION area
  cdo -O mul $mask ${tmp}6.nc ${outfil%.*}.nc
  rm -f ${tmp}_input.nc ${tmp}_out.nc ${tmp}*.nc
}

#---------------------------------------------------
Process_adroms() {		#ADRIAROMS forecasts
#---------------------------------------------------
  input=$1
  outfil=$2
  #miss="1.0000e+09"
  
  fact="0.10"		#BIAS at Otranto???
  tmp=${tmpdir}/${model}_${var}_tmp

  #convert to netcdf
  cdo -f nc copy $input ${tmp}input.nc
  #Extact zeta variable
  cdo selvar,dslm ${tmp}input.nc ${tmp}.nc
  #Rename variable 
  ncrename -v dslm,${var} ${tmp}.nc
  #Get fields in the 00-23 time range
  cdo seldate,${date}T00:00:00,${date2}T23:00:00 ${tmp}.nc ${tmp}1.nc
  #Subtract fact to water level
  cdo expr,"${var}=${var}-$fact" ${tmp}1.nc ${tmp}2.nc
  #Mask lower values before interpolation
  #ncap2 -s "${var}(:, 0:1,0:135)=1.e+37f;" ${tmp}2.nc ${tmp}3.nc
  ncap2 -s "${var}(:, 0:1,0:135)=-9.e+33f;" ${tmp}2.nc ${tmp}3.nc
  #Spatial interpolation 
  #cdo gendis,remap_grid_ADRION tmp1.nc ${weidir}/ADRIAROMS_weights.nc
  cdo remap,${scriptdir}/remap_grid_ADRION,${weidir}/ADRIAROMS_${var}_weights.nc ${tmp}3.nc ${tmp}4.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss ${tmp}4.nc ${tmp}5.nc
  #Mask lower values before interpolation
  #ncap2 -s "${var}(:, 0:200,0:508)=1.e+37f;" ${tmp}5.nc ${tmp}6.nc
  #ncap2 -s "${var}(:, 0:200,0:508)=9.e+33f;" ${tmp}5.nc ${tmp}6.nc
  ncap2 -s "${var}(:, 0:200,0:508)=-999.f;" ${tmp}5.nc ${tmp}6.nc
  #Mask values outside ADRION area
  cdo -O mul $mask ${tmp}6.nc ${outfil}
  rm -f ${tmp}_input.nc ${tmp}*.nc
}

#---------------------------------------------------
Process_mfs() {			#MFS forecasts
#---------------------------------------------------
  input=$1
  outfil=$2
  ##outfil="MFS_${var}_${fdate}"
  motuT1=`date -d "$date 30 min" +"%Y-%m-%d %H:%M:%S"`
  user="******"
  psw="*******"
  pid="sv04-med-ingv-ssh-an-fc-h"
  url="http://nrt.cmems-du.eu/motu-web/Motu"
  sid="MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS"


  #Download file from CMEMS
  #python motu-client.py -q --user $user --pwd $psw  --motu $url --service-id $sid --product-id $pid --longitude-min $x0 --longitude-max $x1 --latitude-min $y0 --latitude-max $y1 --date-min "${motuT1}" --date-max "${date} 23:30:00" --variable zos --out-dir $orgdir --out-name ${outfil}_orig.nc
 
  #Spatial interpolation 
  cdo remap,${scriptdir}/remap_grid_ADRION,${weidir}/MFS_${var}_weights.nc $input tmp.nc
  #Temporal interpolation 
  cdo inttime,${date},00:00:00,1hour tmp.nc tmp1.nc
  #Rename variable 
  ncrename -v zos,${var} tmp1.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss tmp1.nc tmp2.nc
  #Mask values outside ADRION area
  cdo mul $mask tmp2.nc tmp3.nc
  #Add tide
  mv tmp3.nc ${outfil}
####  cdo -O enssum ${orgdir}/ismar/ismar_tide_${var}_${fdate}.nc tmp3.nc ${outfil}
  #cdo seldate,2018-10-29T00:00:00,2018-10-30T23:00:00 MFS_sea_level.nc 1111.nc
  rm -f tmp.nc tmp1.nc tmp2.nc tmp3.nc #orig/${outfil}_orig.nc 
}

#---------------------------------------------------
Process_COAWST1km() {              #COAWST forecasts
#---------------------------------------------------
  model="COAWST1km"
  input=$1
  outfil="${model}_${var}_${fdate}"
  miss="1.e+37f"

  #Extact zeta variable
  cdo selvar,zeta $input tmp.nc
  #Rename variable 
  ncrename -v zeta,${var} tmp.nc
  #Time interpolation
  cdo inttime,${date},00:00:00,1hour tmp.nc tmp1.nc
  cdo -O seldate,${date}T00:00:00,${date}T23:00:00 tmp1.nc tmp2.nc
  #Spatial interpolation 
  #cdo gendis,remap_grid_ADRION tmp.nc ${weidir}/COAWST1km_weights.nc
  cdo remap,${scriptdir}/remap_grid_ADRION,${weidir}/${model}_weights.nc tmp2.nc tmp3.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss tmp3.nc tmp4.nc
  #Mask lower values before interpolation
  ncap2 -O -v -s "sea_level(:,0:220,0:508)=$miss;" tmp4.nc tmp5.nc
  #Mask values outside ADRION area
  cdo -O mul -gtc,0 $mask tmp5.nc tmp6.nc
  cdo setmissval,-999 tmp6.nc tmp7.nc
  #Remove values equal 0 
  cdo -O setctomiss,0 tmp7.nc ${outfil}.nc
  rm -f tmp*.nc
}

#---------------------------------------------------
Process_SIMM-E() {		#SIMM-Ecmwf forecasts
#---------------------------------------------------
  input=$1
  outfil="SIMM-E_${var}_${fdate}"
  fact="0.385"		#BIAS for IBI at Gibraltar, to refer to the geoid

  #Convert ous to shy
  #./ous2shy $input ${orgdir}/MedAdr_ispra_27610_nkn.bas
  #input=${orgdir}/out.hydro.shy
  #Spatial interpolation 
  shyelab -out -outformat nc -reg $dx,$dy,$x0,$y0,$x1,$y1 -regexpand 8 $input
  #Remove vel,depth, level variables
  ncks -C -x -v u_velocity,v_velocity,total_depth,level out.nc tmp.nc
  #Rename variable 
  ncrename -v water_level,${var} tmp.nc
  #Get fields in the 00-23 time range
  cdo settaxis,${date},00:00:00,1hour tmp.nc tmp1.nc
  cdo seldate,${date}T00:00:00,${date}T23:00:00 tmp1.nc tmp2.nc
  #Subtract fact to water level
  cdo expr,"${var}=${var}-$fact" tmp2.nc tmp3.nc
  #Mask values outside ADRION area
  cdo mul $mask tmp3.nc tmp4.nc
  #Add tide
  cdo -O enssum ${orgdir}/ismar/ismar_tide_${var}_${fdate}.nc tmp3.nc ${outfil}
  rm -f out.nc tmp.nc tmp1.nc tmp2.nc tmp3.nc tmp4.nc
}

#---------------------------------------------------
Process_SIMM-B() {		#SIMM-Bolam forecasts
#---------------------------------------------------
  input=$1
  outfil="SIMM-B_${var}_${fdate}"
  fact="0.385"		#BIAS for IBI at Gibraltar, to refer to the geoid #TO BE FIXED

  #Convert ous to shy
  #./ous2shy $input ${orgdir}/MedAdr_ispra_27610_nkn.bas
  #input=${orgdir}/out.hydro.shy
  #Spatial interpolation 
  shyelab -out -outformat nc -reg $dx,$dy,$x0,$y0,$x1,$y1 -regexpand 8 $input
  #Remove vel,depth, level variables
  ncks -C -x -v u_velocity,v_velocity,total_depth,level out.nc tmp.nc
  #Rename variable 
  ncrename -v water_level,${var} tmp.nc
  #Get fields in the 00-23 time range
  cdo settaxis,${date},00:00:00,1hour tmp.nc tmp1.nc
  cdo seldate,${date}T00:00:00,${date}T23:00:00 tmp1.nc tmp2.nc
  #Subtract fact to water level
  cdo expr,"${var}=${var}-$fact" tmp2.nc tmp3.nc
  #Mask values outside ADRION area
  cdo mul $mask tmp3.nc tmp4.nc
  #Add tide
  cdo -O enssum ${orgdir}/ismar/ismar_tide_${var}_${fdate}.nc tmp3.nc ${outfil}
  rm -f out.nc tmp.nc tmp1.nc tmp2.nc tmp3.nc tmp4.nc
}

#--------------------------------------------------
Compute_MMES() {			#Compute ensemble statistics
#--------------------------------------------------
  #cdo ensemble option: ensmin, ensmax, ensrange, ensmean, ensvar, ensstd
  files=("${outdir}/ismar")
  #for model in "${!models[@]}" ; do
    #fname="${model}_${var}_${fdate}.nc"
    #if [ -s "$fname" ]; then
      #files+=("$fname")
    #fi
  #done
  echo ${encf[@]}
 
  tmesf="TMES_${var}_${fdate}.nc"
  cdo -O ensmean ${files[@]} mean.nc 
  ncrename -v ${var},${var}-mean mean.nc 
  cdo -O ensstd  ${files[@]} std.nc
  ncrename -v ${var},${var}-std std.nc
  cdo settabnum,141 std.nc std1.nc
  cdo -O merge mean.nc std1.nc $tmesf
  #cdo expr,"uncertaintly=(std/${var})*100" TMES_${var}_${fdate}.nc  
  rm -f mean.nc std*.nc
}

#--------------------------------------------------
Extract_TMES() {                        #Extract TMES at stations
#--------------------------------------------------
  tmesf="TMES_${var}_${fdate}.nc"
  for i in "${!stats[@]}"; do
    stat=${stats[$i]}
    outf="${var}_TMES_${stat}_${date}.txt"
    lon=${lons[$i]}
    lat=${lats[$i]}
    vvv="${var}mean"
    cdo selvar,$vvv $tmesf tmp.nc
    cdo -s -outputtab,date,time,value -remapnn,lon=${lon}_lat=${lat} tmp.nc > mean.txt
    sed -i "s/ /::/2" $outf mean.txt
    rm -f tmp.nc
    vvv="${var}std"
    cdo selvar,$vvv $tmesf tmp.nc
    cdo -s -outputtab,date,time,value -remapnn,lon=${lon}_lat=${lat} tmp.nc > std.txt
    sed -i "s/ /::/2" $outf std.txt
    rm -f tmp.nc
    joincol mean.txt std.txt > $outf
    rm -f mean.txt std.txt
  done
}

#--------------------------------------------------
Read_stations() { 
#--------------------------------------------------
  coord=$1
  tmp=`awk '{print $1}' $coord`
  lons=($tmp)
  tmp=`awk '{print $2}' $coord`
  lats=($tmp)
  tmp=`awk '{print $3}' $coord`
  stats=($tmp)
}

#--------------------------------------------------
Compute_timeserie() { 
#--------------------------------------------------
  model=$1
  file="${model/%/_${var}_${fdate}.nc}"
  if [ -s "$file" ]; then
    for i in "${!stats[@]}"; do
      stat=${stats[$i]}
      outf="${var}_${model}_${stat}_${date}.txt"
      lon=${lons[$i]}
      lat=${lats[$i]}
      cdo -s -outputtab,date,time,value -remapnn,lon=${lon}_lat=${lat} $file > $outf
      sed -i "s/ /::/2" $outf
    done
  fi
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
# Define grid
#-------------------------------------------------------------
Define_grid

#-------------------------------------------------------------
# Process TIDES
#-------------------------------------------------------------
#Process_tid kassandra_v03_20181029_sims_tide.hydro.shy

#-------------------------------------------------------------
# Process model results - Loop over models
#-------------------------------------------------------------
#for model in "${!models[@]}" ; do
#  ext="${models[$model]}"
#  fname="${orgdir}/${model}_${var}_${fdate}_orig.${ext}"
#  #if [ "$model" != "ADRIAROMS" ]; then
#  #  continue
#  #fi
#  if [ -s "$fname" ]; then
#    echo " ----- Processing model $model ----- "
#    Process_${model} $fname
#  fi
#done

model=$2
filename=$3
outfil=$4
echo "file ${filename}"

  if [ -s "$filename" ]; then
    echo " ----- Processing model $model ----- "
    Process_${model} $filename $outfil
  fi


#-------------------------------------------------------------
# Compute TMES statistics
#-------------------------------------------------------------
#Compute_TMES

#-------------------------------------------------------------
# Read monitoring stations
#-------------------------------------------------------------
#Read_stations $obssta

#-------------------------------------------------------------
# Extract TMES timeseries
#-------------------------------------------------------------
#Extract_TMES

#-------------------------------------------------------------
# Compute timeseries
#-------------------------------------------------------------
#for model in "${!models[@]}"; do
#  Compute_timeserie $model
#done

#-------------------------------------------------------------
# Make plot of timeseries
#-------------------------------------------------------------
#Create_timeseries_plot

