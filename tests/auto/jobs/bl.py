# Imports
import datetime
import logging
import os
import sys


def run(job_obj):
    bldate = get_bl_date(job_obj)
    create_bl_dir(job_obj, bldate)
    sys.exit()
    branch, pr_repo_loc, repo_dir_str = clone_pr_repo(job_obj)
    run_regression_test(job_obj, pr_repo_loc)
    post_process(job_obj, pr_repo_loc, repo_dir_str, branch)


def create_bl_dir(job_obj, bldate):
    bldir = job_obj.machine['bldir']
    bldir += f'/develop-{bldate}'
    print(f'Build Dir: {bldir}')
    if os.path.exists(bldir):
        raise FileExistsError(f'Baseline dir: {bldir} exists. It should not.')
    else:
        print("IM HERE GEEZ")
        os.makedirs(bldir)
        if not os.path.exists(bldir):
            raise Exception(f'Something went wrong creating {bldir}')


def get_bl_date(job_obj):
    for line in job_obj.preq_dict['preq'].body.splitlines():
        if 'BLDIR:' in line:
            bldate = line
            bldate = bldate.replace('BLDIR:', '')
            bldate = bldate.replace(' ', '')

    return bldate


def run_regression_test(job_obj, pr_repo_loc):
    logger = logging.getLogger('RT/RUN_REGRESSION_TEST')
    compiler = job_obj.preq_dict["compiler"]
    if compiler == 'gnu':
        rt_command = [[f'export RT_COMPILER="{compiler}" && cd tests '
                       '&& /bin/bash --login ./rt.sh -e -l rt_gnu.conf',
                       pr_repo_loc]]
    elif compiler == 'intel':
        rt_command = [[f'export RT_COMPILER="{compiler}" && cd tests '
                       '&& /bin/bash --login ./rt.sh -e', pr_repo_loc]]
    job_obj.run_commands(logger, rt_command)


def remove_pr_data(job_obj, pr_repo_loc, repo_dir_str, rt_dir):
    logger = logging.getLogger('RT/REMOVE_PR_DATA')
    rm_command = [
                 [f'rm -rf {rt_dir}', pr_repo_loc],
                 [f'rm -rf {repo_dir_str}', pr_repo_loc]
                 ]
    job_obj.run_commands(logger, rm_command)


def clone_pr_repo(job_obj):
    ''' clone the GitHub pull request repo, via command line '''
    logger = logging.getLogger('RT/CLONE_PR_REPO')
    repo_name = job_obj.preq_dict['preq'].head.repo.name
    branch = job_obj.preq_dict['preq'].head.ref
    git_url = job_obj.preq_dict['preq'].head.repo.html_url.split('//')
    git_url = f'{git_url[0]}//${{ghapitoken}}@{git_url[1]}'
    logger.debug(f'GIT URL: {git_url}')
    logger.info('Starting repo clone')
    repo_dir_str = f'{job_obj.machine["workdir"]}/'\
                   f'{str(job_obj.preq_dict["preq"].id)}/'\
                   f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    pr_repo_loc = f'{repo_dir_str}/{repo_name}'
    job_obj.comment_text_append(f'Repo location: {pr_repo_loc}')
    create_repo_commands = [
        [f'mkdir -p "{repo_dir_str}"', job_obj.machine['workdir']],
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


def post_process(job_obj, pr_repo_loc, repo_dir_str, branch):
    ''' This is the callback function associated with the "RT" command '''
    logger = logging.getLogger('RT/MOVE_RT_LOGS')
    rt_log = f'tests/RegressionTests_{job_obj.machine["name"]}'\
             f'.{job_obj.preq_dict["compiler"]}.log'
    filepath = f'{pr_repo_loc}/{rt_log}'
    rt_dir, logfile_pass = process_logfile(job_obj, filepath)
    if logfile_pass:
        move_rt_commands = [
            [f'git pull --ff-only origin {branch}', pr_repo_loc],
            [f'git add {rt_log}', pr_repo_loc],
            [f'git commit -m "PASSED: {job_obj.machine["name"]}'
             f'.{job_obj.preq_dict["compiler"]}. Log file uploaded. skip-ci"',
             pr_repo_loc],
            ['sleep 10', pr_repo_loc],
            [f'git push origin {branch}', pr_repo_loc]
        ]
        job_obj.run_commands(logger, move_rt_commands)
        remove_pr_data(job_obj, pr_repo_loc, repo_dir_str, rt_dir)


def process_logfile(job_obj, logfile):
    logger = logging.getLogger('RT/PROCESS_LOGFILE')
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
                        f'.{job_obj.preq_dict["compiler"]} '
                        f'{job_obj.preq_dict["action"]["name"]} log')
        raise FileNotFoundError(f'Could not find {job_obj.machine["name"]}'
                                f'.{job_obj.preq_dict["compiler"]} '
                                f'{job_obj.preq_dict["action"]["name"]} log')
