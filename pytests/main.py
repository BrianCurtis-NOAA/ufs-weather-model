import logging
import argparse
import ecflow as ECF
import os
import re
import yaml
import shutil
from typing import Any #Type Hinting

def parse_args():
    logger : logging.Logger = logging.getLogger(__name__)
    logger.info("Parsing command line arguments.")
    parser : argparse.ArgumentParser = argparse.ArgumentParser(description="Run regression tests.")
    parser.add_argument('-a', '--accnr', nargs=1, type=str, help='Account number', required=True)
    parser.add_argument('-l', '--conf-file', nargs=1, type=str, help='Conf file')
    parser.add_argument('-o', '--compile-only', action='store_true', help='Compile only flag')
    parser.add_argument('-w', '--skip-check-results', action='store_true', help='Skip check results flag')
    create_or_compare : argparse._MutuallyExclusiveGroup = parser.add_mutually_exclusive_group()
    create_or_compare.add_argument('-c', '--create-baseline', action='store_true', help='Create baseline flag')
    create_or_compare.add_argument('-m', '--compare-manual', action='store_true', help='Use new baseline RTPWD')
    tests_database : argparse._MutuallyExclusiveGroup = parser.add_mutually_exclusive_group()
    tests_database.add_argument('-n', '--single-test', nargs=2, type=str, help='Run single test with format "testname compiler"')
    tests_database.add_argument('-b', '--tests-from-file', nargs='?', type=str, help='use tests list from file')
    keep_or_delete_rundir : argparse._MutuallyExclusiveGroup = parser.add_mutually_exclusive_group()
    keep_or_delete_rundir.add_argument('-k', '--keep-rundir', action='store_true', help='Keep run directory flag')
    keep_or_delete_rundir.add_argument('-d', '--delete-rundir', action='store_true', help='Delete run directory flag')
    workflow_manager : argparse._MutuallyExclusiveGroup = parser.add_mutually_exclusive_group(required=True)
    workflow_manager.add_argument('-r', '--rocoto', action='store_true', help='Use ROCOTO workflow manager')
    workflow_manager.add_argument('-e', '--ecflow', action='store_true', help='Use ECFLOW workflow manager')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output flag')
    args = parser.parse_args()
    logger.info("Finished Parsing command line arguments.")

    return args

def parse_yaml(file_in):
    logger : logging.Logger = logging.getLogger(__name__)
    _var_matcher = re.compile(r"\${([^}^{]+)}")
    _tag_matcher = re.compile(r"[^$]*\${([^}^{]+)}.*")

    def _path_constructor(_loader: Any, node: Any):
        def replace_fn(match):
            envparts = f"{match.group(1)}:".split(":")
            return os.environ.get(envparts[0], envparts[1])
        return _var_matcher.sub(replace_fn, node.value)


    def load_yaml(filename: str) -> dict:
        yaml.add_implicit_resolver("!envvar", _tag_matcher, None, yaml.SafeLoader)
        yaml.add_constructor("!envvar", _path_constructor, yaml.SafeLoader)
        try:
            with open(filename, "r") as f:
                return yaml.safe_load(f.read())
        except (FileNotFoundError, PermissionError, ParserError):
            return dict()


    config = load_yaml(file_in)

    return config


def process_path(path: str, must_exist: bool=False, create_path: bool=False,
                 delete_before: bool=False) -> bool:
    logger : logging.Logger = logging.getLogger(__name__)
    if os.path.exists(path):
        path_exists = True
        logger.debug(f"Path {path} exists.")
    else:
        path_exists = False
        logger.debug(f"Path {path} does not exist.")
    
    if must_exist and (not path_exists):
        raise FileNotFoundError(f"Path {path} does not exist.")
    if create_path and (not path_exists):
        #os.makedirs(path, exist_ok=True)
        logger.info(f"Creating path {path}.")
        path_exists = True
    if delete_before and path_exists:
        if os.path.isfile(path):
            #os.remove(path)
            logger.info(f"Removing file {path}.")
        else:
            #shutil.rmtree(path)
            logger.info(f"Removing directory {path} and all its contents.")
        path_exists = False
        if create_path:
            #os.makedirs(path, exist_ok=True)
            logger.info(f"Creating path {path}.")
            path_exists = True
    
    return path_exists


def main():
    logger : logging.Logger = logging.getLogger(__name__)
    logging.basicConfig(filename='main.log', filemode='w', level=logging.DEBUG)
    logger.info("Starting Regression Testing.")

    machine_id = os.environ['MACHINE_ID']
    logger.info(f'Machine ID: {machine_id}')

    args = parse_args()
    logger.debug(f'Command line arguments: {args}')
    logger.debug(f'args.ecflow: {args.ecflow}, args.rocoto: {args.rocoto}')

    main_pid=os.getpid()
    os.environ['MAIN_PID'] = str(main_pid)
    logger.debug(f'Main PID: {main_pid}')

    config = parse_yaml('user_config.yml')
    
    machine_config = config['machine'][(machine_id)]
    logger.debug(f'Machine config: {machine_config}')
    for key,iten in machine_config.items():
        os.environ[key] = str(iten)
    
    main_config = config['main']
    logger.debug(f'main_config: {main_config}')
    for key,iten in main_config.items():
        os.environ[key] = str(iten)

    rt_config = parse_yaml('rt_config.yml')
    logger.debug(f'rt_config: {rt_config}')
    for key,iten in rt_config.items():
        os.environ[key] = str(iten)

    process_path(machine_config['PTMP'], must_exist=True, create_path=True, delete_before=False)
    process_path(machine_config['STMP'], must_exist=True, create_path=True, delete_before=False)
    process_path(machine_config['DISKNM'], must_exist=True, create_path=False, delete_before=False)
    process_path(rt_config['RUNDIR_ROOT'], must_exist=False, create_path=True, delete_before=False)
    process_path(rt_config['RTPWD'], must_exist=True, create_path=False, delete_before=False)
    process_path(rt_config['INPUTDATA_ROOT'], must_exist=True, create_path=False, delete_before=False)
    process_path(rt_config['INPUTDATA_ROOT_WW3'], must_exist=True, create_path=False, delete_before=False)
    process_path(rt_config['INPUTDATA_LM4'], must_exist=True, create_path=False, delete_before=False)
    if args.create_baseline:
        process_path(rt_config['NEW_BASELINE'], must_exist=False, create_path=True, delete_before=True)

    logger.info("End of Regression Testing.")

if __name__ == "__main__":
    main()