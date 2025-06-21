import socket
import re
import os
import sys
import logging

#https://stackoverflow.com/questions/70680363/structural-pattern-matching-using-regex
class RegexEqual(str):
    def __eq__(self, pattern):
        return bool(re.search(pattern, self))

def detect_machine():
    systemHostname=socket.gethostname()
    logger = logging.getLogger(__name__)
    logger.debug(f"System Hostname retrieved as {systemHostname}")

    match RegexEqual(systemHostname):
        case (
           r"adecflow0[12].acorn.wcoss2.ncep.noaa.gov" |
           r"alogin0[123].acorn.wcoss2.ncep.noaa.gov"
        ):
            os.environ["MACHINE_ID"]="acorn"
            machineID="acorn"
        case r"derecho[1-8].hsn.de.hpc.ucar.edu":
            os.environ["MACHINE_ID"]="derecho"
            machineID="derecho"
        case r"discover3[1-5].prv.cube":
            os.environ["MACHINE_ID"]="discover"
            machineID="discover"
        case r"login0[1-2].expanse.sdsc.edu":
            os.environ["MACHINE_ID"]="expanse"
            machineID="expanse"
        case (
            r"gaea5[1-8]" |
            r"gaea5[1-8].ncrc.gov"
        ):
            os.environ["MACHINE_ID"]="gaeac5"
            machineID="gaeac5"
        case (
            r"gaea6[1-8]" |
            r"gaea6[1-8].ncrc.gov"
        ):
            os.environ["MACHINE_ID"]="gaeac6"
            machineID="gaeac6"
        case (
            r"login[1-4].frontera.tacc.utexas.edu" |
            r"c*.frontera.tacc.utexas.edu"
        ):
            os.environ["MACHINE_ID"]="frontera"
            machineID="frontera"
        case (
            r"hfe0[1-9]" |
            r"hfe0-2]" |
            r"hecflow01"
        ):
            os.environ["MACHINE_ID"]="hera"
            machineID="hera"
        case r"[Hh]ercules-login-[1-4].[Hh][Pp][Cc].[Mm]s[Ss]tate.[Ee]du":
            os.environ["MACHINE_ID"]="hercules"
            machineID="hercules"
        case (
            r"fe[1-8]" |
            r"tfe[12]"
        ):
            os.environ["MACHINE_ID"]="jet"
            machineID="jet"
        case r"Orion-login-[1-4].HPC.MsState.Edu":
            os.environ["MACHINE_ID"]="orion"
            machineID="orion"
        case r"s4-submit.ssec.wisc.edu":
            os.environ["MACHINE_ID"]="s4"
            machineID="s4"
        case r"login[1-4].stampede2.tacc.utexas.edu":
            os.environ["MACHINE_ID"]="stampede"
            machineID="stampede"
        case (
            r"clogin0[1-9].cactus.wcoss2.ncep.noaa.gov" |
            r"clogin10.cactus.wcoss2.ncep.noaa.gov" |
            r"dlogin0[1-9].dogwood.wcoss2.ncep.noaa.gov" |
            r"dlogin10.dogwood.wcoss2.ncep.noaa.gov"
        ):
            os.environ["MACHINE_ID"]="wcoss2"
            machineID="wcoss2"
        case _:
            logger.error("Unsupported Machine.")
            raise TypeError("Unsupported Machine.")
    
    logger.info(f"Machine ID set as: {machineID}")
    return machineID
        
if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    if "MACHINE_ID" in os.environ:
        logger.warning("MACHINE_ID was set before starting script, safely exiting")
        sys.exit()
    machineID = detect_machine()