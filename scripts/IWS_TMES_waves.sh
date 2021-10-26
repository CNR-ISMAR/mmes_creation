#!/bin/bash
#
# Process model output for the TMES. All fields are interpolated
# over the same grid and the same timesteps.
# set -x
#--------------------------------------------------
Define_dir() {
#--------------------------------------------------
  scriptdir=`dirname "$0"`
  var="waves"
  datedir=`dirname "$1"`
  outdir=`dirname "$datedir"`
  echo $outdir
  tmesdir=`dirname "$outdir"`
  orgdir="${tmesdir}/forecasts"
  tmpdir="${tmesdir}/tmp"
  weidir="${tmesdir}/config/weights"
  mask="${tmesdir}/config/mask/TMES_mask_002_ext.nc"
  declare -Ag models=( ["KASSANDRA"]="shy"
                       ["MED-Waves"]="nc"
                       ["NETTUNO"]="nc"
                       ["SIMM"]="nc"
                       ["HENETUS"]="txt"
                       ["SMMO"]="nc"
                       ["COAWST1km"]="nc"
                       ["WWMHR"]="nc"
                       ["SWANIT"]="grb" )
  #models=(KASSANDRA MFS NETTUNO SIMM HENETUS COAWST1km SMMO SWANIT WWMHR)
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
Process_kassandra() {			#KASSANDRA forecasts
#---------------------------------------------------
  input=$1
  outfil=$2
  model='kassandra'
  tmp=${tmpdir}/${model}_${var}_tmp

  #Spatial interpolation 
  #./shyelab -out -outformat nc -reg $dx,$dy,$x0,$y0,$x1,$y1 
  #Remove vel,depth, level variables
  ncks -O -C -x -v total_depth,level ${input} ${tmp}1.nc
  #ncwa -a level tmp.nc tmp1.nc #TODO nosuitable variable error
  #cp ${input} ${tmp}1.nc
  #Temporal interpolation 
  cdo settaxis,${date},00:00:00,3hour ${tmp}1.nc ${tmp}2.nc
  mv ${tmp}2.nc ${tmp}1.nc
  #read -p "continue?"
  cdo inttime,${date},00:00:00,1hour ${tmp}1.nc ${tmp}2.nc
  #Get fields in the 00-23 time range
  cdo -O seldate,${date}T00:00:00,${date2}T23:00:00 ${tmp}2.nc ${tmp}3.nc
  #Mask values outside ADRION area
  cdo -O mul $mask ${tmp}3.nc ${outfil}
  rm -f out.nc ${tmp}.nc ${tmp}1.nc ${tmp}2.nc ${tmp}3.nc
}

#---------------------------------------------------
Process_wam() {			#MFS forecasts
#---------------------------------------------------
  input=$1
  model="hcmr_wam"
  outfil=$2
  motuT1=`date -d $date +"%Y-%m-%d %H:%M:%S"`
  user="*****"
  psw="******"
  pid="med-hcmr-wav-an-fc-h"
  url="http://nrt.cmems-du.eu/motu-web/Motu"
  sid="MEDSEA_ANALYSISFORECAST_WAV_006_017-TDS"

  #Download file from CMEMS
  #python motu-client.py -q --user $user --pwd $psw  --motu $url --service-id $sid --product-id $pid --longitude-min $x0 --longitude-max $x1 --latitude-min $y0 --latitude-max $y1 --date-min "${motuT1}" --date-max "${date} 23:00:00" --variable VHM0 --variable VTM10 --variable VMDR  --out-dir $orgdir --out-name ${outfil}_orig.nc

  #Spatial interpolation (weights already computed)
  cdo remap,${scriptdir}/remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc $input tmp.nc
  #Rename variables
  ncrename -v VHM0,wsh -v VTM10,wmp tmp.nc
  ncrename -v VMDR,wmd tmp.nc
  #Get fields in the 00-23 time range
  cdo -O seldate,${date}T00:00:00,${date2}T23:00:00 tmp.nc tmp1.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss tmp1.nc tmp2.nc
  #Change integet to float
  cdo -b f32 copy tmp2.nc tmp3.nc
  #Mask values outside ADRION area
  cdo -O mul $mask tmp3.nc tmp4.nc
  cdo setmissval,-999 tmp4.nc ${outfil}
  rm -f tmp.nc tmp1.nc tmp2.nc tmp3.nc tmp4.nc #orig/${outfil}_orig.nc
}

#---------------------------------------------------
Process_MED-Waves() {			#MFS forecasts
#---------------------------------------------------
  input=$1,
  psw="******"
  pid="med-hcmr-wav-an-fc-h"
  url="http://nrt.cmems-du.eu/motu-web/Motu"
  sid="MEDSEA_ANALYSISFORECAST_WAV_006_017-TDS"
  remap_file="${scriptdir}/remap_grid_ADRION"

  #Download file from CMEMS
  #python motu-client.py -q --user $user --pwd $psw  --motu $url --service-id $sid --product-id $pid --longitude-min $x0 --longitude-max $x1 --latitude-min $y0 --latitude-max $y1 --date-min "${motuT1}" --date-max "${date} 23:00:00" --variable VHM0 --variable VTM10 --variable VMDR  --out-dir $orgdir --out-name ${outfil}_orig.nc

  #Spatial interpolation (weights already computed)
  cdo remap,${scriptdir}/remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc $input tmp.nc
  #Rename variables
  ncrename -v VHM0,wsh -v VTM10,wmp tmp.nc
  ncrename -v VMDR,wmd tmp.nc
  #Get fields in the 00-23 time range
  cdo -O seldate,${date}T00:00:00,${date2}T23:00:00 tmp.nc tmp1.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss tmp1.nc tmp2.nc
  #Change integet to float
  cdo -b f32 copy tmp2.nc tmp3.nc
  #Mask values outside ADRION area
  cdo -O mul $mask tmp3.nc tmp4.nc
  cdo setmissval,-999 tmp4.nc ${outfil}.nc
  rm -f tmp.nc tmp1.nc tmp2.nc tmp3.nc tmp4.nc #orig/${outfil}_orig.nc 
}

#---------------------------------------------------
Process_NETTUNO() {			#NETTUNO forecasts
#---------------------------------------------------
  input=$1
  model="NETTUNO"
  outfil="${model}_${var}_${fdate}"
  ndate=`date -d $date +"%Y%m%d"`
  nname="orig/WAM${ndate}00_"

  tar zxvf $input
  #Concatenate files from 00 to 24 and convert to nc
  cdo mergetime ${nname}00*.grb ${nname}01*.grb ${nname}021.grb ${nname}024.grb tmp.grb
  rm -f ${nname}*.grb
  cdo -f nc copy tmp.grb tmp.nc
  #Remove vel,depth, level variables
  ncks -C -x -v dwi,pp1d,cdww,wind,mp2,height tmp.nc tmp1.nc
  #Spatial interpolation (${weidir}/already computed)
  cdo remap,${scriptdir}/remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc tmp1.nc tmp2.nc
  #Temporal interpolation 
  cdo inttime,${date},00:00:00,1hour tmp2.nc tmp3.nc
  #Rename variables
  ncrename -v swh,wsh -v mwp,wmp tmp3.nc
  ncrename -v mwd,wmd tmp3.nc
  #Get fields in the 00-23 time range
  cdo -O seldate,${date}T00:00:00,${date}T23:00:00 tmp3.nc tmp4.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss tmp4.nc tmp5.nc
  #Mask values outside ADRION area
  cdo -O mul $mask tmp5.nc tmp6.nc
  cdo setmissval,-999 tmp6.nc ${outfil}.nc
  rm -f tmp.grb tmp.nc tmp1.nc tmp2.nc tmp3.nc tmp4.nc tmp5.nc #orig/WAM*.grb
}

#---------------------------------------------------
Process_swanita_mwd() {			#SWAN forecasts 1
#---------------------------------------------------
  model="swanita_single"
  input=$1
  varname="mwd"
  ndate=`date -d $date +"%Y%m%d"`
  tmp=${tmpdir}/${model}_${varname}${ndate}_tmp

  #Convert to nc
  cdo -f nc copy $input  ${tmp}.nc
  
  #process files
  Process_swanita

}

#---------------------------------------------------
Process_swanita_swh() {			#SWAN forecasts 2
#---------------------------------------------------
  model="swanita_single"
  input=$1
  varname=swh
  ndate=`date -d $date +"%Y%m%d"`
  tmp=${tmpdir}/${model}_${varname}${ndate}_tmp
  
  #Convert to nc
  #Convert to nc
  cdo -f nc copy $input  ${tmp}.nc
  
  #process files
  Process_swanita

}

#---------------------------------------------------
Process_swanita_pp1d() {			#SWAN forecasts 2
#---------------------------------------------------
  model="swanita_single"
  input=$1
  varname=pp1d
  ndate=`date -d $date +"%Y%m%d"`
  tmp=${tmpdir}/${model}_${varname}${ndate}_tmp
  
  
  #Convert to nc
  cdo -f nc copy $input  ${tmp}.nc
  
  #process files
  Process_swanita
}


#---------------------------------------------------
Process_swanita() {			#SWAN forecasts
#---------------------------------------------------
  model="swanita"
  #set -x
  
  ndate=`date -d $date +"%Y%m%d"`
  outfil="${outdir}/${ndate}/arpae_${model}_${var}_${ndate}.nc"
  var="waves"
  miss="-9.e+33f"
  tmp=${tmpdir}/${model}_${var}${ndate}_tmp


  #merge single components
  swanitafiles=(${tmpdir}/${model}_single*${ndate}*.nc) 
  echo ${#swanitafiles[@]}
  #check if single files are already copied (must be three)
  if [ ${#swanitafiles[@]} -lt 3 ]; then
    echo "swanita not complete"
    exit
  fi
  cdo -O merge  ${swanitafiles[@]} ${tmp}.nc
  #Extact wave variable
  #cdo selvar,swh,mwp,mwd tmp.nc tmp1.nc
  cdo selvar,swh,pp1d,mwd ${tmp}.nc ${tmp}1.nc
  #Rename variable 
  ncrename -v swh,wsh ${tmp}1.nc
  ncrename -v pp1d,wmp ${tmp}1.nc
  #ncrename -v mwp,wmp tmp1.nc
  ncrename -v mwd,wmd ${tmp}1.nc
  #Spatial interpolation (weights already computed)
  #cdo gendis,${scriptdir}/remap_grid_ADRION tmp1.nc ${weidir}/SWAN_waves_weights.nc
  cdo remap,${scriptdir}/remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc ${tmp}1.nc ${tmp}2.nc
  #Get fields in the 00-23 time range
  cdo -O seldate,${date}T00:00:00,${date2}T23:00:00 ${tmp}2.nc ${tmp}3.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss ${tmp}3.nc ${tmp}4.nc
  #Mask values below 40.51  to missing value
  ncap2 -O -v -s "wsh(:,0:459,371:508)=$miss;wmp(:,0:459,371:508)=$miss;wmd(:,0:459,371:508)=$miss;" ${tmp}4.nc ${tmp}5.nc
  #Mask values outside ADRION area
  cdo -O mul $mask ${tmp}5.nc ${tmp}6.nc
  cdo setmissval,-999 ${tmp}6.nc ${outfil}
  # read -p "continue?"  
  rm -f ${tmpdir}/*${model}*.nc 
}

#---------------------------------------------------
Process_SIMM() {              #SIMM wave forecasts
#---------------------------------------------------
  model="SIMM"
  input=$1
  outfil="${model}_${var}_${fdate}"
  dlon="-5.9368"
  dlat="30.0"

  #Set time axis
  cdo settaxis,${date},00:00:00,1hour $input tmp.nc
  cdo -O seldate,${date}T00:00:00,${date2}T23:00:00 tmp.nc tmp1.nc
  mv tmp1.nc tmp.nc
  #rm -f tmp.grb tmp.nc tmp1.nc tmp2.nc tmp3.nc #orig/WAM*.grb
  #Remove variables
  ncks -C -x -v ff,dd,tp,hs_sea,tp_sea,tmp_sea,thq_sea,hs_swell,tp_swell,tmp_swell,thw_swell tmp.nc tmp1.nc
  #Rename variables
  ncrename -v hs,wsh -v tmp,wmp tmp1.nc
  ncrename -v thq,wmd tmp1.nc
  #Change lon lat
  ncap2 -O -s "lon=lon+$dlon" tmp1.nc tmp2.nc
  ncap2 -O -s "lat=lat+$dlat" tmp2.nc tmp3.nc
  #Change gridtype from generic to latlon
  #do -setgrid,${weidir}/simm_grid tmp3.nc tmp4.nc
  cdo -setgrid,${weidir}/simm_grid_old tmp3.nc tmp4.nc
  #Spatial interpolation (weights already computed)
  #cdo gendis,${scriptdir}/remap_grid_ADRION tmp4.nc ${weidir}/SIMM_waves_weights.nc
  #cdo -O remap,${scriptdir}/remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc tmp4.nc tmp5.nc
  cdo -O remapdis,${scriptdir}/remap_grid_ADRION tmp4.nc tmp5.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss tmp5.nc tmp6.nc
  #Mask values outside ADRION area
  cdo -O mul $mask tmp6.nc tmp7.nc
  #Remove values equal 0 
  cdo setctomiss,0 tmp7.nc tmp8.nc
  #Convert direction
  ncap2 -s "wmd = wmd + 180" tmp8.nc tmp9.nc
  ncap2 -s "where(wmd >= 360) wmd = wmd - 360" tmp9.nc ${outfil}.nc
  rm -f out.nc tmp*.nc
}

#---------------------------------------------------
Process_HENETUS() {              #HENETUS wave forecasts
#---------------------------------------------------
  model="HENETUS"
  input=$1
  outfil="${model}_${var}_${fdate}"
  hdate=`date -d "$date - 1 day" +"%Y-%m-%d"`
  miss="-999."

  #Convert ascii to nc
  ln -s $input henetus.dat
  ${orgdir}/henetus_extract
  cdo -f nc input,${weidir}/${model}_grid wsh.nc < wsh.dat
  ncrename -v var1,wsh wsh.nc
  cdo -f nc input,${weidir}/${model}_grid wmp.nc < wmp.dat
  ncrename -v var1,wmp wmp.nc
  cdo -f nc input,${weidir}/${model}_grid wmd.nc < wmd.dat
  ncrename -v var1,wmd wmd.nc
  cdo -O merge  wsh.nc wmp.nc wmd.nc tmp.nc
  #Set time axis and time interpolation
  cdo settaxis,${hdate},15:00:00,3hour tmp.nc tmp1.nc
  cdo inttime,${date},00:00:00,1hour tmp1.nc tmp2.nc
  cdo -O seldate,${date}T00:00:00,${date2}T23:00:00 tmp2.nc tmp3.nc
  #Set missing value
  cdo setmissval,0. tmp3.nc tmp4.nc
  #Spatial interpolation (weights already computed)
  #cdo gendis,${scriptdir}/remap_grid_ADRION tmp4.nc ${weidir}/HENETUS_waves_weights.nc
  cdo -O remap,${scriptdir}/remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc tmp4.nc tmp5.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss tmp5.nc tmp6.nc
  #Mask values below 40.51  to missing value
  ncap2 -O -v -s "wsh(:,0:192,0:508)=$miss;wmp(:,0:192,0:508)=$miss;wmd(:,0:192,0:508)=$miss;" tmp6.nc tmp7.nc
  #Mask values outside ADRION area
  cdo -O mul $mask tmp7.nc tmp8.nc
  cdo -O setmissval,-999 tmp8.nc ${outfil}.nc
  rm -f *.dat wsh.nc wmp.nc wmd.nc tmp*.nc
}

#---------------------------------------------------
Process_COAWST1km() {		#COAWST forecasts
#---------------------------------------------------
  model="COAWST1km"
  input=$1
  outfil="${model}_${var}_${fdate}"
  miss="1.e+37f"

  #Extact zeta variable
  cdo selvar,Hwave,Pwave_top,Dwave $input tmp.nc
  #Rename variable 
  ncrename -v Hwave,wsh tmp.nc
  ncrename -v Pwave_top,wmp tmp.nc
  ncrename -v Dwave,wmd tmp.nc
  #Time interpolation
  cdo inttime,${date},00:00:00,1hour tmp.nc tmp1.nc
  cdo -O seldate,${date}T00:00:00,${date}T23:00:00 tmp1.nc tmp2.nc
  #Spatial interpolation 
  #cdo gendis,${scriptdir}/remap_grid_ADRION tmp.nc ${weidir}/COAWST1km_weights.nc
  cdo remap,${scriptdir}/remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc tmp2.nc tmp3.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss tmp3.nc tmp4.nc
  #Mask lower values before interpolation
  ncap2 -O -v -s "wsh(:,0:220,0:508)=$miss;wmp(:,0:220,0:508)=$miss;wmd(:,0:220,0:508)=$miss;" tmp4.nc tmp5.nc
  #Mask values outside ADRION area
  cdo -O mul -gtc,0 $mask tmp5.nc tmp6.nc
  cdo setmissval,-999 tmp6.nc tmp7.nc
  #Remove values equal 0 
  cdo -O setctomiss,0 tmp7.nc ${outfil}.nc
  rm -f tmp*.nc
}

#---------------------------------------------------
Process_smmo() {		#SMMO forecasts
#---------------------------------------------------
  model="smmo"
  input=$1
  outfil=$2
  miss="-999"
  tmp=${tmpdir}/${model}_${var}_tmp
  echo "tmpdir: ${tmp}"

  #convert to netcdf
  cdo -f nc copy $input ${tmp}_input.nc
  #Extact wave variable
  #cdo selvar,S_WHT,MEAN_FR,MEANWDIR ${input} tmp.nc
  cdo selvar,swh,mwp,mwd ${tmp}_input.nc ${tmp}.nc
  #Invert latitude
  cdo invertlat ${tmp}.nc ${tmp}0.nc
  #Convert frequency to period
  #ncap2 -s "where(MEAN_FR != -999) MEAN_FR = 1./MEAN_FR" tmp.nc tmp1.nc
  cp ${tmp}.nc ${tmp}1.nc
  #Set missing value
  cdo setmissval,$miss ${tmp}1.nc ${tmp}2.nc
  #Rename variable 
  ncrename -v .swh,wsh ${tmp}2.nc
  ncrename -v .mwp,wmp ${tmp}2.nc
  ncrename -v .mwd,wmd ${tmp}2.nc
  #ncrename -v S_WHT,wsh tmp2.nc
  #ncrename -v MEAN_FR,wmp tmp2.nc
  #ncrename -v MEANWDIR,wmd tmp2.nc
  #Change integet to float
  cdo -b f32 copy ${tmp}2.nc ${tmp}3.nc
  #Time interpolation
  cdo -O seldate,${date}T00:00:00,${date2}T23:00:00 ${tmp}3.nc ${tmp}4.nc
  #Spatial interpolation #bilinear perche' dis e nn non funzia
  #cdo genbil,${scriptdir}/remap_grid_ADRION tmp3.nc ${weidir}/SMMO_waves_weights.nc
  cdo remap,${scriptdir}/remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc ${tmp}4.nc ${tmp}5.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss ${tmp}5.nc ${tmp}6.nc
  #Mask values outside ADRION area
  cdo -O mul -gtc,0 $mask ${tmp}6.nc ${outfil}
  #rm -f ${tmp}*.nc
}

#---------------------------------------------------
Process_wwm3() {		#WWM forecasts
#---------------------------------------------------
  model="wwm3"
  input=$1
  outfil=$2
  miss="-999"
  tmp=${tmpdir}/${model}_${var}_tmp

  #Remove not needed variables
  ncks -C -x -v MESNL,MESIN,MESDS,MESBF,ICOMP,AMETHOD,FMETHOD,DMETHOD,SMETHOD,LSPHE,IOBP,ocean_time_day,frhigh,frlow,SPDIR,SPSIG,AdjacencyEdgeBound,NEIGHBORedge,CorrespVertex,CycleBelong,LenCycle,ListBoundEdge,ListVertBound,MULTIPLEOUT,ele,depth $input ${tmp}.nc
  #Rename variables 
  ncrename -v HS,wsh ${tmp}.nc
  #ncrename -v WLM,wmp ${tmp}.nc
  ncrename -v TM01,wmp ${tmp}.nc
  ncrename -v DM,wmd ${tmp}.nc
  ncrename -v ocean_time,time ${tmp}.nc
  ncrename -d ocean_time,time ${tmp}.nc
  #Select data on correct time range
  cdo -O seldate,${date}T00:00:00,${date2}T23:00:00 ${tmp}.nc ${tmp}1.nc
  #Set grid to unstructured
  cdo -O setgrid,${weidir}/${model}.grid ${tmp}1.nc ${tmp}2.nc
  #Spatial interpolation
  #cdo -P 6 gendis,${scriptdir}/remap_grid_ADRION popo.nc ${weidir}/wwm3_waves_weights.nc
  cdo -O remap,${scriptdir}/remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc ${tmp}2.nc ${tmp}3.nc
  #Mask lower values after interpolation
  ncap2 -O -v -s "wsh(:,0:193,0:508)=$miss;wmp(:,0:193,0:508)=$miss;wmd(:,0:193,0:508)=$miss;" ${tmp}3.nc ${tmp}4.nc
  #Mask values outside ADRION area
  cdo -O mul -gtc,0 $mask ${tmp}4.nc ${tmp}5.nc
  cdo setmissval,$miss ${tmp}5.nc ${tmp}6.nc
  #Remove values equal 0 
  cdo -O setctomiss,0 ${tmp}6.nc ${tmp}7.nc
  #Convert wave direction 
  ncap2 -s "wmd = 270 - wmd" ${tmp}7.nc ${tmp}8.nc 
  ncap2 -s "where(wmd < 0) wmd = wmd + 360" ${tmp}8.nc ${outfil}
  rm -f ${tmp}*.nc
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
Define_dir $4

#-------------------------------------------------------------
# Define grid
#-------------------------------------------------------------
Define_grid

#-------------------------------------------------------------
# Process model results - Loop over models
#-------------------------------------------------------------


model=$2
filename=$3
outfil=$4
echo "file ${filename}"


  if [ -s "$filename" ]; then
    echo " ----- Processing model $model ----- "
    Process_${model} $filename $outfil
  fi

##-------------------------------------------------------------
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
#Extract_TMES wsh
#Extract_TMES wmp
#Extract_TMES wmd

#-------------------------------------------------------------
# Compute timeseries
#-------------------------------------------------------------
#for model in "${!models[@]}"; do
  #Compute_timeserie $model  
#done

#-------------------------------------------------------------
# Make plot of timeseries
#-------------------------------------------------------------
#Create_timeseries_plot
