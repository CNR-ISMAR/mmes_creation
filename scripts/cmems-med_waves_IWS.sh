#!/bin/bash
#
# Script to get CMCC CMEMS files
# Require motuclient python to download files from CMEMS database
#   change permission: umask 022
#   intall: python -m pip install motuclient 
# set -x
#--------------------------------------------------
Define_dir() {
#--------------------------------------------------
  date=`date +%Y%m%d`
  [ -n "$1" ] && date=$1
  ddate=`date -d $date +"%Y-%m-%d"`
  ddate2=`date -d "$date + 1 days" +"%Y-%m-%d"`
  motuT1=`date -d "$date -1 hours" +"%Y-%m-%d %H:%M:%S"`
  motuT2=`date -d "$date 3 days" +"%Y-%m-%d"`

  var="waves"
  thrdir="/usr3/thredds"

# set username and password from arguments
  [ -n "$3" ] && user=$3
  [ -n "$4" ] && pass=$4
  echo ${user}'/'${pass}

  iwsdir="/usr3/iwsdata"
  tiddir="${iwsdir}/forecasts/TIDE"
  locdir="${iwsdir}/forecasts/CMCC"
  outdir="${iwsdir}/mmes_components/${date}"
  bindir="${iwsdir}/bin"
  tmpdir="${iwsdir}/tmp"
  weidir="${bindir}/weights"
  mask="${bindir}/TMES_mask_002.nc"
  motu="python -m motuclient"

  wfile="med-hcmr-wav-an-fc-h"
#  swfile="hcmr_wam_waves_${date}.nc"
  swfile=$2
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
   user=${user}
   pass=${pass}
   murl="http://nrt.cmems-du.eu/motu-web/Motu"
   surl="MEDSEA_ANALYSISFORECAST_WAV_006_017-TDS"
   tsleep=10

   #ADRIATIC
   #Wave
   EXITSTATUS=-1
   ITER=0
   until [ ${EXITSTATUS} -eq 0 ]; do
      ${motu} -q -u $user -p $pass -m $murl -s $surl -d ${wfile} -x $x1 -X $x2 -y $y1 -Y $y2 -t "$motuT1" -T "$motuT2" -v VHM0 -v VTM10 -v VMDR -o $locdir -f $swfile
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
}


##########################################################
#               MAIN
##########################################################

#-------------------------------------------------------------
# Define directory name
#-------------------------------------------------------------
Define_dir $1 $2 $3 $4

#-------------------------------------------------------------
# Download files
#-------------------------------------------------------------
Get_myocean

#-------------------------------------------------------------
# Copy to IWS directory
#-------------------------------------------------------------
#mv $lfile /usr3/thredds/data/cmcc_forecasts/$slfile
#rm -f ${slfile}

