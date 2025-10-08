help([[
loads modules needed for proper UFSWM RT operation on Ursa
]])

prepend_path("MODULEPATH", "/contrib/spack-stack/spack-stack-1.9.2/envs/ue-oneapi-2024.2.1/install/modulefiles/Core")
prepend_path("MODULEPATH", "/contrib/spack-stack/spack-stack-1.9.2/envs/ue-oneapi-2024.2.1/install/modulefiles/intel-oneapi-mpi/2021.13-haww6b3/gcc/12.4.0")

stack_oneapi_ver=os.getenv("stack_oneapi_ver") or "2024.2.1"
load(pathJoin("stack-oneapi", stack_oneapi_ver))

stack_impi_ver=os.getenv("stack_impi_ver") or "2021.13"
load(pathJoin("stack-intel-oneapi-mpi", stack_impi_ver))

nccmp_ver=os.getenv("nccmp_ver") or "1.9.1.0"
load(pathJoin("nccmp", nccmp_ver))

--python_ver=os.getenv("python_ver") or "3.11.7"
python_ver=os.getenv("python_ver") or "3.9"
--load(pathJoin("stack-python", python_ver))
load(pathJoin("python", python_ver))

ecflow_ver=os.getenv("ecflow_ver") or "5.11.4"
load(pathJoin("ecflow", ecflow_ver))

rocoto_ver=os.getenv("rocoto_ver") or "1.3.7"
load(pathJoin("rocoto", rocoto_ver))

setenv("MACHINE_ID", "ursa")

whatis("Description: UFSWM RT run environment")
