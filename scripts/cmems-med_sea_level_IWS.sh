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



  lfile="med-cmcc-ssh-an-fc-hts"
  #slfile="cmcc_mfs_sea_level_${date}.nc"
  slfile=$2
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
   surl="MEDSEA_ANALYSISFORECAST_PHY_006_013-TDS"
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


##########################################################
#               MAIN
##########################################################

#-------------------------------------------------------------
# Define directory name
#-------------------------------------------------------------
Define_dir $1 $2 $3 $4 $5 $6 $7

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

