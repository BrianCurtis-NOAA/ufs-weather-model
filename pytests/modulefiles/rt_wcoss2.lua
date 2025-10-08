help([[
loads modules needed for proper UFSWM RT operation on WCOSS2/Acorn
]])

ecflow_ver=os.getenv("ecflow_ver") or "5.6.0.13"
load(pathJoin("ecflow", ecflow_ver))

PrgEnv_intel_ver=os.getenv("PrgEnv_intel_ver") or "8.1.0"
load(pathJoin("PrgEnv-intel", PrgEnv_intel_ver))

intel_ver=os.getenv("intel_ver") or "19.1.3.304"
load(pathJoin("intel", intel_ver))

craype_ver=os.getenv(craype_ver) or "2.7.13"
load(pathJoin("craype", craype_ver))

cray_mpich_ver=os.getenv("cray_mpich_ver") or "8.1.12"
load(pathJoin("cray-mpich", cray_mpich_ver))

netcdf_ver=os.getenv("netcdf_ver") or "4.9.2"
load(pathJoin("netcdf-D", netcdf_ver))

pnetcdf_ver=os.getenv("pnetcdf_ver") or "1.12.2"
load(pathJoin("pnetcdf-D", pnetcdf_ver))

hdf5_ver=os.getenv("hdf5_ver") or "1.14.0"
load(pathJoin("hdf5-D", hdf5_ver))

nccmp_ver=os.getenv("nccmp_ver") or "1.9.0
load(pathJoin("nccmp-D", nccmp_ver))

python_ver=os.getenv("python_ver") or "3.8.6"
load(pathJoin("python", python_ver))

setenv("MACHINE_ID", "wcoss2")

whatis("Description: UFSWM RT run environment")