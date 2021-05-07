# Imports
import logging
import os


def run(job_obj):
    job_obj.update_key('Job', 'RT')
    job_obj.update_key('Status', 'Running')
    logging.info('Starting "RT" Task')
    pull_request = job_obj.get_pr_obj()
    run_regression_test(job_obj, pull_request)
    post_process(job_obj, pull_request)
    job_obj.update_key('Status', 'Completed')
    logging.info('Finished "RT" Task')


def run_regression_test(job_obj, pull_request):
    logging.info("Starting to run regression tests from rt.sh")
    compiler = job_obj.get_value('Compiler')
    pr_repo_loc = f'{job_obj.get_value("PR Dir")}/'\
                  f'{pull_request.head.repo.name}'
    logging.debug(f'pr_repo_loc: {pr_repo_loc}')
    if compiler == 'gnu':
        rt_command = [[f'export RT_COMPILER="{compiler}" && cd tests '
                       '&& /bin/bash --login ./rt.sh -e -l rt_gnu.conf',
                       pr_repo_loc]]
    elif compiler == 'intel':
        rt_command = [[f'export RT_COMPILER="{compiler}" && cd tests '
                       '&& /bin/bash --login ./rt.sh -e', pr_repo_loc]]
    try:
        job_obj.run_commands(rt_command)
    except RuntimeError as e:
        logging.error('rt.sh has failed')
        notes = job_obj.get_value('Notes')
        notes += 'rt.sh has failed\n'
        job_obj.update_key('Notes', notes)
        job_obj.failed()
        raise RuntimeError(e)


def post_process(job_obj, pull_request):
    pr_repo_loc = f'{job_obj.get_value("PR Dir")}/'\
                  f'{pull_request.head.repo.name}'
    branch = pull_request.head.ref
    machine = job_obj.get_value('Machine')
    compiler = job_obj.get_value('Compiler')
    rt_log = f'tests/RegressionTests_{machine}.{compiler}.log'
    log_filepath = f'{pr_repo_loc}/{rt_log}'
    logfile_pass = process_logfile(job_obj)
    if logfile_pass:
        if pull_request.maintainer_can_modify:
            move_rt_commands = [
                [f'git pull --ff-only origin {branch}', pr_repo_loc],
                [f'git add {rt_log}', pr_repo_loc],
                [f'git commit -m "AutoRT: {machine}.{compiler}'
                 f' Log File.\n\non-behalf-of @ufs-community"',
                 pr_repo_loc],
                ['sleep 10', pr_repo_loc],
                [f'git push origin {branch}', pr_repo_loc]
            ]
            try:
                job_obj.run_commands(move_rt_commands)
            except RuntimeError as e:
                logging.error('Committing log file has failed')
                notes = job_obj.get_value('Notes')
                notes += 'Committing log file has failed\n'
                job_obj.update_key('Notes', notes)
                job_obj.failed()
                raise RuntimeError(e)
        else:
            logging.critical('Cannot upload log file, blocked by PR Author')
            notes = job_obj.get_value('Notes')
            notes += 'Cannot upload log file as it is blocked by PR Author\n'
            job_obj.update_key('Notes', notes)
            job_obj.failed()
            raise RuntimeError('Blocked from uploading log file by PR Author')


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
