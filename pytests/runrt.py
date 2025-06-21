import machine
import os
import logging
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Run RT tests")
    workflow_manager = parser.add_mutually_exclusive_group(required=True)
    workflow_manager.add_argument('-e', '--ecflow', action='store_true', help='Use ecFlow workflow manager')
    workflow_manager.add_argument('-r', '--rocoto', action='store_true', help='Use Rocoto workflow manager')
    retainer = parser.add_mutually_exclusive_group(required=False)
    retainer.add_argument('-k', '--keep', action='store_true', help='Keep run directory after completion')
    retainer.add_argument('-d', '--delete', action='store_true', help='Delete run directories that are not used by other tests')
    baselines = parser.add_mutually_exclusive_group(required=False)
    baselines.add_argument('-b', '--baseline_list', action='store_true', help='use the file listed here as a baseline list')
    baselines.add_argument('-n', '--single_baseline', action='store_true', help='Only use a single baseline')
    create_or_compare = parser.add_mutually_exclusive_group(required=False)
    create_or_compare.add_argument('-c', '--create', action='store_true', help='Create new baseline results')
    create_or_compare.add_argument('-m', '--compare', action='store_true', help='Compare against new baseline results')
    parser.add_argument('-a', metavar='account', required=True, help='Account to use for HPC queue')
    parser.add_argument('-h', action='store_true', help='Display this help')
    parser.add_argument('-l', metavar='file', help='Run tests specified in <file>')
    parser.add_argument('-o', action='store_true', help='Compile only, skip tests')
    parser.add_argument('-v', action='store_true', help='Verbose output')
    parser.add_argument('-w', action='store_true', help='For weekly_test, skip comparing baseline results')

    args = parser.parse_args()
    if args.h:
        parser.print_help()
        exit(0)
    return args

def main():
    logger = logging.getLogger(__name__)
    machineID = machine.detect_machine()
    args = parse_args()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(filename)s:%(funcName)s:%(lineno)s **%(levelname)s**: %(message)s')
    main()