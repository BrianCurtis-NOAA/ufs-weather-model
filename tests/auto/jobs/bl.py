# Imports
import datetime
import logging
import os
import sys


def run(job_obj):
    logger = logging.getLogger('BL/RUN')
    workdir, rtbldir, blstore = set_directories(job_obj)
    branch, pr_repo_loc, repo_dir_str = clone_pr_repo(job_obj, workdir)
    run_regression_test(job_obj, pr_repo_loc)
    post_process(job_obj, pr_repo_loc, repo_dir_str, rtbldir, blstore, branch)


def set_directories(job_obj):
    logger = logging.getLogger('BL/SET_DIRECTORIES')
    if job_obj.machine['name'] == 'hera':
        workdir = '/scratch1/NCEPDEV/nems/Brian.Curtis/autort/pr'
        blstore = '/scratch1/NCEPDEV/nems/Brian.Curtis/RT/NEMSfv3gfs'
        rtbldir = '/scratch1/NCEPDEV/stmp4/Brian.Curtis/FV3_RT/'\
                f'REGRESSION_TEST_{job_obj.compiler.upper()}'
    elif job_obj.machine['name'] == 'jet':
        workdir = '/lfs4/HFIP/h-nems/emc.nemspara/autort/pr'
        blstore = '/lfs4/HFIP/hfv3gfs/RT/NEMSfv3gfs/'
        rtbldir = '/lfs4/HFIP/hfv3gfs/emc.nemspara/RT_BASELINE/'\
               f'emc.nemspara/FV3_RT/REGRESSION_TEST_{job_obj.compiler.upper()}'
    elif job_obj.machine['name'] == 'gaea':
        workdir = '/lustre/f2/pdata/ncep/Brian.Curtis/autort/pr'
        blstore = '/lustre/f2/pdata/esrl/gsd/ufs/ufs-weather-model/RT'
        rtbldir = '/lustre/f2/scratch/Brian.Curtis/FV3_RT/'\
               f'REGRESSION_TEST_{job_obj.compiler.upper()}'
    elif job_obj.machine['name'] == 'orion':
        workdir = '/work/noaa/nems/emc.nemspara/autort/pr'
        blstore = '/work/noaa/nems/emc.nemspara/RT/NEMSfv3gfs'
        rtbldir = '/work/noaa/stmp/bcurtis/stmp/bcurtis/FV3_RT/'\
               f'REGRESSION_TEST_{job_obj.compiler.upper()}'
    elif job_obj.machine['name'] == 'cheyenne':
        workdir = '/glade/work/heinzell/fv3/ufs-weather-model/auto-rt'
        blstore = '/glade/p/ral/jntp/GMTB/ufs-weather-model/RT'
        rtbldir = '/glade/work/heinzell/FV3_RT/'\
               f'REGRESSION_TEST_{job_obj.compiler.upper()}'
    else:
        raise KeyError(f'Machine {job_obj.machine["name"]} is not '\
                        'supported for this job')

    logger.info(f'machine: {job_obj.machine["name"]}')
    logger.info(f'workdir: {workdir}')
    logger.info(f'blstore: {blstore}')
    logger.info(f'rtbldir: {rtbldir}')

    return workdir, rtbldir, blstore


def create_bl_dir(job_obj, bldate, blstore):
    logger = logging.getLogger('BL/CREATE_BL_DIR')
    bldir = f'{blstore}/develop-{bldate}/{job_obj.compiler.upper()}'
    logger.info(f'Build Dir: {bldir}')
    if os.path.exists(bldir):
        raise FileExistsError(f'Baseline dir: {bldir} exists. It should not.')
    else:
        os.makedirs(bldir)
        if not os.path.exists(bldir):
            raise Exception(f'Something went wrong creating {bldir}')

    return bldir


def get_bl_date(job_obj):
    logger = logging.getLogger('BL/GET_BL_DATE')
    for line in job_obj.preq_dict['preq'].body.splitlines():
        if 'BL_DATE:' in line:
            bldate = line
            bldate = bldate.replace('BL_DATE:', '')
            bldate = bldate.replace(' ', '')
            if len(bldate) != 8:
                raise ValueError(f'Date: {bldate} is not formatted YYYYMMDD')
            logger.info(f'bldate: {bldate}')
            bl_format = '%Y%m%d'
            try:
                datetime.datetime.strptime(bldate, bl_format)
            except ValueError:
                logger.info(f'Date {bldate} is not formatted YYYYMMDD')
                raise ValueError
    return bldate


def run_regression_test(job_obj, pr_repo_loc):
    logger = logging.getLogger('BL/RUN_REGRESSION_TEST')
    if job_obj.compiler == 'gnu':
        rt_command = [[f'export RT_COMPILER="{job_obj.compiler}" && cd tests '
                       '&& /bin/bash --login ./rt.sh -e -c -l rt_gnu.conf',
                       pr_repo_loc]]
    elif job_obj.compiler == 'intel':
        rt_command = [[f'export RT_COMPILER="{job_obj.compiler}" && cd tests '
                       '&& /bin/bash --login ./rt.sh -e -c', pr_repo_loc]]
    job_obj.run_commands(logger, rt_command)


def remove_pr_data(job_obj, pr_repo_loc, repo_dir_str, rt_dir):
    logger = logging.getLogger('BL/REMOVE_PR_DATA')
    rm_command = [
                 [f'rm -rf {rt_dir}', pr_repo_loc],
                 [f'rm -rf {repo_dir_str}', pr_repo_loc]
                 ]
    job_obj.run_commands(logger, rm_command)


def clone_pr_repo(job_obj, workdir):
    ''' clone the GitHub pull request repo, via command line '''
    logger = logging.getLogger('BL/CLONE_PR_REPO')
    repo_name = job_obj.preq_dict['preq'].head.repo.name
    branch = job_obj.preq_dict['preq'].head.ref
    git_url = job_obj.preq_dict['preq'].head.repo.html_url.split('//')
    git_url = f'{git_url[0]}//${{ghapitoken}}@{git_url[1]}'
    logger.debug(f'GIT URL: {git_url}')
    logger.info('Starting repo clone')
    repo_dir_str = f'{workdir}/'\
                   f'{str(job_obj.preq_dict["preq"].id)}/'\
                   f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    pr_repo_loc = f'{repo_dir_str}/{repo_name}'
    job_obj.comment_text_append(f'Repo location: {pr_repo_loc}')
    create_repo_commands = [
        [f'mkdir -p "{repo_dir_str}"', os.getcwd()],
        [f'git clone -b {branch} {git_url}', repo_dir_str],
        ['git submodule update --init --recursive',
         f'{repo_dir_str}/{repo_name}'],
        ['git config user.email "brian.curtis@noaa.gov"',
         f'{repo_dir_str}/{repo_name}'],
        ['git config user.name "Brian Curtis"',
         f'{repo_dir_str}/{repo_name}']
    ]

    job_obj.run_commands(logger, create_repo_commands)

    logger.info('Finished repo clone')
    return branch, pr_repo_loc, repo_dir_str


def post_process(job_obj, pr_repo_loc, repo_dir_str, rtbldir, blstore, branch):
    logger = logging.getLogger('BL/MOVE_RT_LOGS')
    rt_log = f'tests/RegressionTests_{job_obj.machine["name"]}'\
             f'.{job_obj.compiler}.log'
    filepath = f'{pr_repo_loc}/{rt_log}'
    rt_dir, logfile_pass = process_logfile(job_obj, filepath)
    if logfile_pass:
        bldate = get_bl_date(job_obj)
        bldir = create_bl_dir(job_obj, bldate, blstore)
        move_bl_command = [[f'mv {rtbldir}/* {bldir}/', pr_repo_loc]]
        job_obj.run_commands(logger, move_bl_command)
        update_rt_sh(job_obj, pr_repo_loc, bldate, branch)
        remove_pr_data(job_obj, pr_repo_loc, repo_dir_str, rt_dir)


def update_rt_sh(job_obj, pr_repo_loc, bldate, branch):
    logger = logging.getLogger('BL/UPDATE_RT_SH')
    with open(f'{pr_repo_loc}/tests/rt.sh', 'r') as f:
        with open(f'{pr_repo_loc}/tests/rt.sh.new', 'w') as w:
            for line in f:
                if 'BL_CURR_DIR=develop-' in line:
                    w.write(f'BL_CURR_DIR=develop-{bldate}\n')
                else:
                    w.write(line)

    move_rtsh_commands = [
        [f'git pull --ff-only origin {branch}', pr_repo_loc],
        [f'mv {pr_repo_loc}/tests/rt.sh.new {pr_repo_loc}/tests/rt.sh', pr_repo_loc],

        [f'git add {pr_repo_loc}/tests/rt.sh', pr_repo_loc],
        [f'git commit -m "BL JOBS PASSED: {job_obj.machine["name"]}'
         f'.{job_obj.compiler}. Updated rt.sh with new develop date: '
         f'{bldate}"',
         pr_repo_loc],
        ['sleep 10', pr_repo_loc],
        [f'git push origin {branch}', pr_repo_loc]
        ]
    job_obj.run_commands(logger, move_rtsh_commands)


def process_logfile(job_obj, logfile):
    logger = logging.getLogger('BL/PROCESS_LOGFILE')
    rt_dir = []
    if os.path.exists(logfile):
        with open(logfile) as f:
            for line in f:
                if 'FAIL' in line:
                    job_obj.comment_text_append(f'{line}')
                if 'working dir' in line and not rt_dir:
                    rt_dir = os.path.split(line.split()[-1])[0]
                    job_obj.comment_text_append(f'Please manually delete: '
                                                f'{rt_dir}')
                elif 'SUCCESSFUL' in line:
                    return rt_dir, True
        job_obj.job_failed(logger, f'{job_obj.preq_dict["action"]["name"]}',
                           STDOUT=False)
    else:
        logger.critical(f'Could not find {job_obj.machine["name"]}'
                        f'.{job_obj.compiler} '
                        f'{job_obj.preq_dict["action"]["name"]} log')
        raise FileNotFoundError(f'Could not find {job_obj.machine["name"]}'
                                f'.{job_obj.compiler} '
                                f'{job_obj.preq_dict["action"]["name"]} log')
