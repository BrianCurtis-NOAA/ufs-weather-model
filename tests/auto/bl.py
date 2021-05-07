# Imports
import datetime
import logging
import os


def run(job_obj):
    job_obj.update_key('Job', 'BL')
    job_obj.update_key('Status', 'Running')
    pull_request = job_obj.get_pr_obj()
    bldate = get_bl_date(job_obj, pull_request)
    rtbldir, blstore = set_directories(job_obj)
    bldir = f'{blstore}/develop-{bldate}/'\
            f'{job_obj.get_value("Compiler").upper()}'
    if not check_for_bl_dir(bldir):
        run_regression_test(job_obj, pull_request)
        post_process(job_obj, pull_request, rtbldir, bldir)
        job_obj.update_key('Status', 'Completed')


def set_directories(job_obj):
    compiler = job_obj.get_value('Compiler')
    machine = job_obj.get_value('Machine')
    if machine == 'hera':
        blstore = '/scratch1/NCEPDEV/nems/emc.nemspara/RT/NEMSfv3gfs'
        rtbldir = '/scratch1/NCEPDEV/stmp4/emc.nemspara/FV3_RT/'\
                  f'REGRESSION_TEST_{compiler.upper()}'
    elif machine == 'jet':
        blstore = '/lfs4/HFIP/h-nems/emc.nemspara/RT/NEMSfv3gfs/'
        rtbldir = '/lfs4/HFIP/h-nems/emc.nemspara/RT_BASELINE/'\
                  'emc.nemspara/FV3_RT/'\
                  f'REGRESSION_TEST_{compiler.upper()}'
    elif machine == 'gaea':
        blstore = '/lustre/f2/pdata/ncep_shared/emc.nemspara/RT/NEMSfv3gfs'
        rtbldir = '/lustre/f2/scratch/emc.nemspara/FV3_RT/'\
                  f'REGRESSION_TEST_{compiler.upper()}'
    elif machine == 'orion':
        blstore = '/work/noaa/nems/emc.nemspara/RT/NEMSfv3gfs'
        rtbldir = '/work/noaa/stmp/bcurtis/stmp/bcurtis/FV3_RT/'\
                  f'REGRESSION_TEST_{compiler.upper()}'
    elif machine == 'cheyenne':
        blstore = '/glade/p/ral/jntp/GMTB/ufs-weather-model/RT'
        rtbldir = '/glade/scratch/briancurtis/FV3_RT/'\
                  f'REGRESSION_TEST_{compiler.upper()}'
    else:
        logging.critical(f'Machine {machine} is not supported')
        raise KeyError

    logging.debug(f'machine: {machine}')
    logging.debug(f'compiler: {compiler}')
    logging.debug(f'blstore: {blstore}')
    logging.debug(f'rtbldir: {rtbldir}')

    return rtbldir, blstore


def check_for_bl_dir(bldir):
    logging.info('Checking if baseline directory exists')
    if os.path.exists(bldir):
        logging.error(f'Baseline dir: {bldir} exists. It should not, yet.')
        raise FileExistsError
    return False


def create_bl_dir(bldir):
    if not check_for_bl_dir(bldir):
        os.makedirs(bldir)
        if not os.path.exists(bldir):
            logging.error(f'Someting went wrong creating {bldir}')
            raise FileNotFoundError


def run_regression_test(job_obj, pull_request):
    compiler = job_obj.get_value('Compiler')
    pr_repo_loc = f'{job_obj.get_value("PR Dir")}/'\
                  f'{pull_request.head.repo.name}'
    logging.debug(f'pr_repo_loc: {pr_repo_loc}')
    if compiler == 'gnu':
        rt_command = [[f'export RT_COMPILER="{compiler}" && cd tests '
                       '&& /bin/bash --login ./rt.sh -e -c -l rt_gnu.conf',
                       pr_repo_loc]]
    elif compiler == 'intel':
        rt_command = [[f'export RT_COMPILER="{compiler}" && cd tests '
                       '&& /bin/bash --login ./rt.sh -e -c', pr_repo_loc]]
    logging.debug(f'rt_command: {rt_command}')
    job_obj.run_commands(rt_command)


def post_process(job_obj, pull_request, rtbldir, bldir):
    pr_repo_loc = f'{job_obj.get_value("PR Dir")}/'\
                  f'{pull_request.head.repo.name}'
    logging.debug(f'pr_repo_loc: {pr_repo_loc}')
    machine = job_obj.get_value('Machine')
    compiler = job_obj.get_value('Compiler')
    rt_log = f'tests/RegressionTests_{machine}.{compiler}.log'
    logging.debug(f'rt_log: {rt_log}')
    log_filepath = f'{pr_repo_loc}/{rt_log}'
    logfile_pass = process_logfile(job_obj, log_filepath)
    if logfile_pass:
        create_bl_dir(bldir)
        move_bl_command = [[f'mv {rtbldir}/* {bldir}/', pr_repo_loc]]
        logging.debug(f'move_bl_command: {move_bl_command}')
        job_obj.run_commands(move_bl_command)


def get_bl_date(job_obj, pull_request):
    logging.info('Starting to get BL date')
    BLDATEFOUND = False
    pr_repo_loc = f'{job_obj.get_value("PR Dir")}/'\
                  f'{pull_request.head.repo.name}'
    logging.debug(f'pr_repo_loc: {pr_repo_loc}')
    with open(f'{pr_repo_loc}/tests/rt.sh', 'r') as f:
        for line in f:
            if 'BL_DATE=' in line:
                logging.info('Found BL_DATE in line')
                BLDATEFOUND = True
                bldate = line
                bldate = bldate.rstrip('\n')
                bldate = bldate.replace('BL_DATE=', '')
                bldate = bldate.strip(' ')
                logging.debug(f'bldate is "{bldate}"')
                logging.debug(f'Type bldate: {type(bldate)}')
                try:
                    datetime.datetime.strptime(bldate, '%Y%m%d')
                except ValueError:
                    logging.error(f'Date {bldate} is not formatted YYYYMMDD')
                    raise ValueError
    if not BLDATEFOUND:
        logging.error('Could not find BL_DATE in rt.sh')
        notes = job_obj.get_value('Notes')
        notes += 'Could not find BL_DATE in rt.sh\n'
        job_obj.update_key('Notes', notes)
        job_obj.failed()
        raise ValueError('Could not find BL_DATE in rt.sh')
    logging.info('Finished getting BL date')

    return bldate


def process_logfile(job_obj):
    logging.info('Processing Log File')
    machine = job_obj.get_value('Machine')
    compiler = job_obj.get_value('Compiler')
    logfile = f'tests/RegressionTests_{machine}.{compiler}.log'
    rt_dirs = []
    failed_jobs = []
    fail_string_list = ['Test', 'failed']
    if os.path.exists(logfile):
        with open(logfile) as f:
            for line in f:
                if all(x in line for x in fail_string_list):
                    failed_jobs.extend(f'{line.rstrip(chr(10))}')
                elif 'working dir' in line and not rt_dirs:
                    rt_dirs = job_obj.get_value('RT Dirs')
                    rt_dirs.extend(os.path.split(line.split()[-1])[0])
                    job_obj.update_key('RT Dirs', rt_dirs)
                elif 'SUCCESSFUL' in line:
                    logging.info('Finished Processing Log File')
                    return True
        logging.error('Could not find "SUCCESSFUL" in log file, '
                      'assuming a failure')
        notes = job_obj.get_value('Notes')
        notes += 'Could not find "SUCCESSFUL" in log file, '\
                 'assuming a failure\n'
        job_obj.update_key('Notes', notes)
        job_obj.update_key('Failed Tests', failed_jobs)
        job_obj.failed()
        raise ValueError('Could not find "SUCCESSFUL" in log file')
    else:
        logging.error(f'Could not find {machine}.{compiler} log')
        notes = job_obj.get_value('Notes')
        notes += f'Could not find {machine}.{compiler} log\n'
        job_obj.update_key('Notes', notes)
        job_obj.failed()
        raise FileNotFoundError(f'Could not find {machine}.{compiler} log')
