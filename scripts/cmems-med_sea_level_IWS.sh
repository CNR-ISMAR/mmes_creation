#!/bin/bash
#
# Script to get CMCC CMEMS files
# Require motuclient python to download files from CMEMS database
#   change permission: umask 022
#   intall: python -m pip install motuclient 
#set -x
#--------------------------------------------------
Define_dir() {
#--------------------------------------------------
  date=`date +%Y%m%d`
  [ -n "$1" ] && date=$1
  ddate=`date -d $date +"%Y-%m-%d"`
  ddate2=`date -d "$date + 1 days" +"%Y-%m-%d"`
  motuT1=`date -d "$date -1 hours" +"%Y-%m-%d %H:%M:%S"`
  motuT2=`date -d "$date 3 days" +"%Y-%m-%d"`   


  var="sea_level"
  thrdir="/usr3/thredds"

  iwsdir="/usr3/iwsdata"
  tiddir="${iwsdir}/forecasts/TIDE" 
  locdir="${iwsdir}/forecasts/CMCC"   
  outdir="${iwsdir}/tmes_components/${date}"
  bindir="${iwsdir}/bin"
  tmpdir="${iwsdir}/tmp"
  weidir="${bindir}/weights"
  mask="${bindir}/TMES_mask_002.nc"
  motu="python2.7 -m motuclient"



  lfile="med-cmcc-ssh-an-fc-hts"
  slfile="cmcc_mfs_sea_level_${date}.nc"

  # Region for the whole grid
  x1="12"
  x2="23"
  y1="36."
  y2="46"
}

#--------------------------------------------------
Get_myocean() {
#--------------------------------------------------
   echo '-----------------------------------------------'
   echo ' Downloading netcdf file from CMEMS'
   echo '-----------------------------------------------'


# Set your CMEMS user and password
   user="***********"
   pass="***********"
   murl="http://nrt.cmems-du.eu/motu-web/Motu"
   surl="MEDSEA_ANALYSIS_FORECAST_PHY_006_013-TDS"
   tsleep=10
   varname="zos"
   EXITSTATUS=-1
   ITER=0
   echo "${locdir}"
   
   FILE=${locdir}/$slfile
    if [ -f $FILE ]; then
       echo "The file '$FILE' exists."
    else
       until [ ${EXITSTATUS} -eq 0 ]; do
          ${motu} -q -u $user -p $pass -m $murl -s $surl -d ${lfile} -x $x1 -X $x2 -y $y1 -Y $y2 -t "$motuT1" -T "$motuT2" -v $varname -o $locdir -f $slfile
          EXITSTATUS=$?
          if [ ${EXITSTATUS} -ne 0 ]; then
            let "ITER=$ITER + 1"
            error="ERROR:_cmemsv02-med_reg_custom.sh_FAIL SSH: $ITER"
            echo $error 
            if [ $ITER -ge 10 ]; then
              echo "   $error" >> $logfile
              exit 1
            fi
            sleep $tsleep
          fi
       done
    fi
}

#--------------------------------------------------
Remap(){
#--------------------------------------------------
  #Spatial interpolation
  cdo remap,remap_grid_ADRION,${weidir}/MFS_${var}_weights.nc ${locdir}/${slfile} ${tmpdir}/mfs_tmp.nc
  #Temporal interpolation
  cdo inttime,${ddate},00:00:00,1hour ${tmpdir}/mfs_tmp.nc ${tmpdir}/mfs_tmp1.nc
  #Get fields in the 00-23 time range
  cdo seldate,${ddate}T00:00:00,${ddate2}T23:00:00 ${tmpdir}/mfs_tmp1.nc ${tmpdir}/mfs_tmp2.nc
  #Rename variable
  ncrename -v zos,${var} ${tmpdir}/mfs_tmp2.nc
  #Extrapolate on missing values (bilinear interpolation)
  cdo fillmiss ${tmpdir}/mfs_tmp2.nc ${tmpdir}/mfs_tmp3.nc
  #Mask values outside ADRION area
  cdo mul $mask ${tmpdir}/mfs_tmp3.nc ${tmpdir}/mfs_tmp4.nc
  #Add tide
  cdo -O enssum ${tiddir}/ismar_tide_sea_level_${date}.nc ${tmpdir}/mfs_tmp4.nc ${outdir}/${slfile}
  #cdo seldate,2018-10-29T00:00:00,2018-10-30T23:00:00 MFS_sea_level.nc 1111.nc
  rm -f ${tmpdir}/mfs_tmp*.nc #orig/${outfil}_orig.nc
}

##########################################################
#               MAIN
##########################################################

#-------------------------------------------------------------
# Define directory name
#-------------------------------------------------------------
Define_dir $1 $2 $3 $4 $5 $6

#-------------------------------------------------------------
# Download files
#-------------------------------------------------------------
Get_myocean

#-------------------------------------------------------------
# Prcess model
#-------------------------------------------------------------
Remap


#-------------------------------------------------------------
# Copy to IWS directory
#-------------------------------------------------------------
#mv $locdir$lfile /usr3/thredds/data/cmcc_forecasts/$slfile
#rm -f ${slfile}

