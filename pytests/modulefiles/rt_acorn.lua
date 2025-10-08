help([[
loads modules needed for proper UFSWM RT operation on WCOSS2/Acorn
]])

ecflow_ver=os.getenv("ecflow_ver") or "5.6.0.13"
load(pathJoin("ecflow", ecflow_ver))

PrgEnv_intel_ver=os.getenv("PrgEnv_intel_ver") or "8.1.0"
load(pathJoin("PrgEnv-intel", PrgEnv_intel_ver))

intel_ver=os.getenv("intel_ver") or "19.1.3.304"
load(pathJoin("intel", intel_ver))

python_ver=os.getenv("python_ver") or "3.8.6"
load(pathJoin("python", python_ver))

whatis("Description: UFSWM RT run environment")