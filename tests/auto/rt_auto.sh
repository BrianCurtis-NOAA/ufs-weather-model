#!/bin/bash --login
set -eux

export RT_COMPILER='intel'
source ../detect_machine.sh
echo "Machine ID: "+$MACHINE_ID
if [[ $MACHINE_ID = hera.* ]]; then
  WORKDIR=/scratch1/NCEPDEV/nems/Brian.Curtis/test
  export PATH=/scratch1/NCEPDEV/nems/emc.nemspara/soft/miniconda3/bin:$PATH
  export PYTHONPATH=/scratch1/NCEPDEV/nems/emc.nemspara/soft/miniconda3/lib/python3.8/site-packages
elif [[ $MACHINE_ID = orion.* ]]; then
  WORKDIR=/work/noaa/nems/bcurtis/test
  export PATH=/work/noaa/nems/emc.nemspara/soft/miniconda3/bin:$PATH
  export PYTHONPATH=/work/noaa/nems/emc.nemspara/soft/miniconda3/lib/python3.8/site-packages
elif [[ $MACHINE_ID = jet.* ]]; then
  WORKDIR=/lfs4/HFIP/h-nems/Brian.Curtis/test
  export ACCNR="h-nems"
  export PATH=/lfs4/HFIP/hfv3gfs/software/ecFlow-5.3.1/bin:$PATH
  export PYTHONPATH=/lfs4/HFIP/hfv3gfs/software/ecFlow-5.3.1/lib/python2.7/site-packages
elif [[ $MACHINE_ID = gaea.* ]]; then
  WORKDIR=/lustre/f2/pdata/ncep/Brian.Curtis/test
  export LOADEDMODULES=$LOADEDMODULES
  export ACCNR="nggps_emc" # This applies to Brian.Curtis, may need change later
  export PATH=/lustre/f2/pdata/esrl/gsd/contrib/miniconda3/4.8.3/envs/ufs-weather-model/bin:$PATH
  export PYTHONPATH=/lustre/f2/pdata/esrl/gsd/contrib/miniconda3/4.8.3/lib/python3.8/site-packages
elif [[ $MACHINE_ID = cheyenne.* ]]; then
  #export PATH=/glade/p/ral/jntp/tools/ecFlow-5.3.1/bin:$PATH
  #export PYTHONPATH=/glade/p/ral/jntp/tools/ecFlow-5.3.1/lib/python2.7/site-packages
  echo "cheyenne not currently supported. automated RT not starting"
  exit 1
else
  echo "No Python Path for this machine. automated RT not starting"
  exit 1
fi

python rt_auto.py -m $MACHINE_ID -w $WORKDIR

exit 0
