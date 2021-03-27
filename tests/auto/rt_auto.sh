#!/bin/bash --login
set -eux
if [ -f "accesstoken.sh" ]; then
  if [ $(stat -L -c "%a" "accesstoken.sh") == "600" ]; then
    echo "Sourcing accesstoken.sh"
    source ./accesstoken.sh
  else
    echo "accesstoken.sh permissions NEED to be set to 600 before starting"
    exit 1
  fi
else
  echo "Please create accesstoken.sh (600) with the following content\n"
  echo "export ghapitoken=<GitHub API Token Here>"
  exit 1
fi

if [[ $HOSTNAME == hfe* ]]; then
  NAME=hera
  export PATH=/scratch1/NCEPDEV/nems/emc.nemspara/soft/miniconda3/bin:$PATH
  export PYTHONPATH=/scratch1/NCEPDEV/nems/emc.nemspara/soft/miniconda3/lib/python3.8/site-packages
elif [[ $HOSTNAME == Orion-login-* ]]; then
  MACHINE_NAME=orion
  # WORKDIR=/work/noaa/nems/emc.nemspara/autort/pr
  # STMP=/work/noaa/stmp/${USER}/stmp
  # PTMP=/work/noaa/stmp/${USER}/stmp
  export PATH=/work/noaa/nems/emc.nemspara/soft/miniconda3/bin:$PATH
  export PYTHONPATH=/work/noaa/nems/emc.nemspara/soft/miniconda3/lib/python3.8/site-packages
elif [[ $HOSTNAME == fe* ]]; then
  NAME=jet
  # WORKDIR=/lfs4/HFIP/h-nems/emc.nemspara/autort/pr
  # STMP=/lfs4/HFIP/h-nems/${USER}/RT_BASELINE
  # PTMP=/lfs4/HFIP/h-nems/${USER}/RT_RUNDIRS
  export ACCNR="h-nems"
  export PATH=/lfs4/HFIP/hfv3gfs/software/miniconda3/4.8.3/envs/ufs-weather-model/bin:/lfs4/HFIP/hfv3gfs/software/miniconda3/4.8.3/bin:$PATH
  export PYTHONPATH=/lfs4/HFIP/hfv3gfs/software/miniconda3/4.8.3/envs/ufs-weather-model/lib/python3.8/site-packages:/lfs4/HFIP/hfv3gfs/software/miniconda3/4.8.3/lib/python3.8/site-packages
elif [[ $HOSTNAME == gaea* ]]; then
  NAME=gaea
  # WORKDIR=/lustre/f2/pdata/ncep/Brian.Curtis/test
  # STMP=/lustre/f2/scratch
  # PTMP=/lustre/f2/scratch
  export LOADEDMODULES=$LOADEDMODULES
  export ACCNR="nggps_emc" # This applies to Brian.Curtis, may need change later
  export PATH=/lustre/f2/pdata/esrl/gsd/contrib/miniconda3/4.8.3/envs/ufs-weather-model/bin:$PATH
  export PYTHONPATH=/lustre/f2/pdata/esrl/gsd/contrib/miniconda3/4.8.3/lib/python3.8/site-packages
elif [[ $HOSTNAME == *.cheyenne.ucar.edu ]]; then
  NAME=cheyenne
  # WORKDIR=/glade/work/heinzell/fv3/ufs-weather-model/auto-rt
  # STMP=/glade/work
  # PTMP=/glade/scratch
  export ACCNR="P48503002"
  export PATH=/glade/p/ral/jntp/tools/miniconda3/4.8.3/envs/ufs-weather-model/bin:/glade/p/ral/jntp/tools/miniconda3/4.8.3/bin:$PATH
  export PYTHONPATH=/glade/p/ral/jntp/tools/miniconda3/4.8.3/envs/ufs-weather-model/lib/python3.8/site-packages:/glade/p/ral/jntp/tools/miniconda3/4.8.3/lib/python3.8/site-packages
else
  echo "No Python Path for this machine. automated RT not starting"
  exit 1
fi

python rt_auto.py -n $NAME

exit 0
