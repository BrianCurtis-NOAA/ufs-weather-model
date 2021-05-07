# Imports
import logging


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
    send_command = f'export RT_COMPILER="{compiler}" && cd tests '\
                   '&& /bin/bash --login ./rt.sh -e'
    conf_file = job_obj.get_value('Conf File')
    if conf_file is not None:
        send_command += f' -l {conf_file}'
    elif compiler == 'gnu':
        send_command += ' -l rt_gnu.conf'
    logging.debug(f'send_command: {send_command}')
    rt_command = [[send_command, pr_repo_loc]]
    logging.debug(f'rt_command: {rt_command}')
    try:
        job_obj.run_commands(rt_command)
    except RuntimeError as e:
        logging.error('"rt.sh -e" has failed')
        notes = job_obj.get_value('Notes')
        notes += '"rt.sh -e" has failed\n'
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
    logfile_pass = job_obj.process_logfile()
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
