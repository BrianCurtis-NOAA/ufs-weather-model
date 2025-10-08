help([[
loads modules needed for proper UFSWM RT operation on GaeaC6
]])

append_path("MODULEPATH", "/ncrc/proj/epic/c6/modulefiles")
rocoto_ver=os.getenv("rocoto_ver") or "1.3.7"
load(pathJoin("rocoto", rocoto_ver))

prepend_path("MODULEPATH", "/ncrc/proj/epic/spack-stack/c6/spack-stack-1.9.2/envs/ue-intel-2023.2.0/install/modulefiles/Core")
stack_intel_ver=os.getenv("stack-intel") or "2023.2.0"
load(pathJoin("stack-intel", stack_intel_ver))

cray_mpi_ver=os.getenv("cray-mpich") or "8.1.30"
load(pathJoin("cray-mpich", cray_mpi_ver))

python_ver=os.getenv("python_ver") or "3.11"
load(pathJoin("python", python_ver))

nccmp_ver=os.getenv("nccmp_ver") or "1.9.1.0"
load(pathJoin("nccmp", nccmp_ver))

append_path("PYTHONPATH", "/ncrc/proj/epic/spack-stack/c6/spack-stack-1.9.2/envs/ue-intel-2023.2.0/install/modulefiles/gcc/12.3.0")
ecflow_ver=os.getenv("ecflow_ver") or "5.11.4"
load(pathJoin("ecflow", ecflow_ver))

setenv("MACHINE_ID", "gaeac6")

whatis("Description: UFSWM RT run environment")