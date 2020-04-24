#!/bin/bash
#
# Process model output for the TMES. All fields are interpolated
# over the same grid and the same timesteps.
set -x
#--------------------------------------------------
Define_dir() {
#--------------------------------------------------
  var="waves"
  tmesdir="/usr3/iwsdata"
  weidir="${tmesdir}/bin/weights"
  bindir="${tmesdir}/bin"
  obsdir="${tmesdir}/observations"
  obssta="${obsdir}/stations_${var}"
  orgdir="${tmesdir}/forecasts"
  tmpdir="${tmesdir}/tmp"
  outdir="${tmesdir}/tmes-components"  
  mask="${bindir}/TMES_mask_002.nc"
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

  ofile="remap_grid_ADRION"
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
  ncks -O -C -x -v total_depth,level ${input}
  #ncwa -a level tmp.nc tmp1.nc #TODO nosuitable variable error
  cp ${input} ${tmp}1.nc
  #Temporal interpolation 
  cdo settaxis,${date},00:00:00,3hour ${tmp}1.nc ${tmp}2.nc
  mv ${tmp}2.nc ${tmp}1.nc
  cdo inttime,${date},00:00:00,1hour ${tmp}1.nc ${tmp}2.nc
  #Get fields in the 00-23 time range
  cdo -O seldate,${date}T00:00:00,${date2}T23:00:00 ${tmp}2.nc ${tmp}3.nc
  #Mask values outside ADRION area
  cdo -O mul $mask ${tmp}3.nc ${outfil}
  rm -f out.nc ${tmp}.nc ${tmp}1.nc ${tmp}2.nc ${tmp}3.nc
}


#---------------------------------------------------
Process_swanita() {			#SWAN forecasts
#---------------------------------------------------
  model="swanita"
  input=$1
  outfil=$2
  ndate=`date -d $date +"%Y%m%d"`
  miss="-9.e+33f"

  #Convert to nc
  cdo -f nc copy $input tmp.nc
  #Extact wave variable
  #cdo selvar,swh,mwp,mwd tmp.nc tmp1.nc
  cdo selvar,swh,pp1d,mwd tmp.nc tmp1.nc
  #Rename variable 
  ncrename -v swh,wsh tmp1.nc
  ncrename -v pp1d,wmp tmp1.nc
  #ncrename -v mwp,wmp tmp1.nc
  ncrename -v mwd,wmd tmp1.nc
  #Spatial interpolation (weights already computed)
  #cdo gendis,remap_grid_ADRION tmp1.nc ${weidir}/SWAN_waves_weights.nc
  cdo remap,remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc tmp1.nc tmp2.nc
  #Get fields in the 00-23 time range
  cdo -O seldate,${date}T00:00:00,${date2}T23:00:00 tmp2.nc tmp3.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss tmp3.nc tmp4.nc
  #Mask values below 40.51  to missing value
  ncap2 -O -v -s "wsh(:,0:459,371:508)=$miss;wmp(:,0:459,371:508)=$miss;wmd(:,0:459,371:508)=$miss;" tmp4.nc tmp5.nc
  #Mask values outside ADRION area
  cdo -O mul $mask tmp5.nc tmp6.nc
  cdo setmissval,-999 tmp6.nc ${outfil}.nc
  rm -f tmp.nc tmp1.nc tmp2.nc tmp3.nc tmp4.nc tmp5.nc 
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
  #cdo genbil,remap_grid_ADRION tmp3.nc ${weidir}/SMMO_waves_weights.nc
  cdo remap,remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc ${tmp}4.nc ${tmp}5.nc
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
  #Rename variable 
  ncrename -v HS,wsh ${tmp}.nc
  #ncrename -v WLM,wmp ${tmp}.nc
  ncrename -v TM01,wmp ${tmp}.nc
  ncrename -v DM,wmd ${tmp}.nc
  #Set grid to unstructured
  cdo setgrid,${weidir}/${model}.grid ${tmp}.nc ${tmp}1.nc
  #Spatial interpolation
  #cdo -P 6 gendis,remap_grid_ADRION popo.nc ${weidir}/wwm3_waves_weights.nc
  cdo -O remap,remap_grid_ADRION,${weidir}/${model}_${var}_weights.nc ${tmp}1.nc ${tmp}2.nc
  #Mask lower values after interpolation
  ncap2 -O -v -s "wsh(:,0:193,0:508)=$miss;wmp(:,0:193,0:508)=$miss;wmd(:,0:193,0:508)=$miss;" ${tmp}2.nc ${tmp}3.nc
  #Mask values outside ADRION area
  cdo -O mul -gtc,0 $mask ${tmp}3.nc ${tmp}4.nc
  cdo setmissval,$miss ${tmp}4.nc ${tmp}5.nc
  #Remove values equal 0 
  cdo -O setctomiss,0 ${tmp}5.nc ${outfil}
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
Define_dir

#-------------------------------------------------------------
# Define grid
#-------------------------------------------------------------
Define_grid

