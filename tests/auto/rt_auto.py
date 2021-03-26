"""Automation of UFS Regression Testing

This script automates the process of UFS regression testing for code managers
at NOAA-EMC

This script should be started through rt_auto.sh so that env vars are set up
prior to start.
"""
from github import Github as gh
import argparse
import datetime
import subprocess
import re
import os
import logging
import importlib


class GHInterface:
    '''
    This class stores information for communicating with GitHub
    ...

    Attributes
    ----------
    GHACCESSTOKEN : str
      API token to autheticate with GitHub
    client : pyGitHub communication object
      The connection to GitHub to make API requests
    '''

    def __init__(self):
        self.logger = logging.getLogger('GHINTERFACE')
        try:
            self.client = gh(os.getenv('ghapitoken'))
        except Exception as e:
            self.logger.critical(f'Exception is {e}')
            raise(e)


def parse_args_in():
    ''' Parse all input arguments coming from rt_auto.sh '''
    logger = logging.getLogger('PARSE_ARGS_IN')
    # Create Parse
    logger.info('Parsing input arguments')
    parser = argparse.ArgumentParser()

    # Setup Input Arguments
    choices = ['cheyenne', 'hera', 'orion', 'gaea', 'jet', 'wcoss_dell_p3']
    parser.add_argument('-n', '--name', help='Machine Name', required=True,
                        choices=choices, type=str)
    parser.add_argument('-g', '--group', help='Machine Group',
                        required=True, type=str)
    parser.add_argument('-b', '--basedir', help='Machine Base Directory',
                        required=True, type=str)
    parser.add_argument('-s', '--stmp', help='Machine STMP Path',
                        required=True, type=str)
    parser.add_argument('-p', '--ptmp', help='Machine PTMP Path',
                        required=True, type=str)

    # Get Arguments
    args = parser.parse_args()

    return args


def input_data(args):
    ''' Create dictionaries of data needed for processing UFS pull requests '''
    logger = logging.getLogger('INPUT_DATA')
    logger.info('Creating dictionaries for input data')

    # WORKDIR=${BASEDIR}/${GROUP}/${USER}/autort/pr
    #
    # NEW_BASELINE=${STMP}/${USER}/FV3_RT/REGRESSION_TEST
    # BLDIR=${BASEDIR}/${GROUP}/${USER}/RT/NEMSfv3gfs
    machine_dict = {
        'name': args.name,
        'group': args.group,
        'basedir': args.basedir,
        'stmp': args.stmp,
        'ptmp': args.ptmp
    }
    repo_list_dict = [{
        'name': 'ufs-weather-model',
        'address': 'BrianCurtis-NOAA/ufs-weather-model',
        'base': 'develop'
    }]
    action_list = ['RT', 'BL']
    }]

    return machine_dict, repo_list_dict, action_list_dict


def set_action_from_label(machine, actions, label):
    ''' Match the label that initiates a job with an action in the dict'''
    # <machine>-<compiler>-<test> i.e. hera-gnu-RT
    logger = logging.getLogger('MATCH_LABEL_WITH_ACTIONS')
    logger.info('Setting action from Label')
    split_label = label.name.split('-')
    # Make sure it has three parts
    if len(split_label) != 3:
        return False, False
    # Break the parts into their variables
    label_machine = split_label[0]
    label_compiler = split_label[1]
    label_action = split_label[2]
    # check machine name matches
    if not re.match(label_machine, machine['name']):
        return False, False
    # Compiler must be intel or gnu
    if not str(label_compiler) in ["intel", "gnu"]:
        return False, False
    action_match = next((action for action in actions
                         if re.match(action, label_action)), False)

    logging.info(f'Compiler: {label_compiler}, Action: {action_match}')
    return label_compiler, action_match


def get_preqs_with_actions(repos, machine, ghinterface_obj, actions):
    ''' Create list of dictionaries of a pull request
        and its machine label and action '''
    logger = logging.getLogger('GET_PREQS_WITH_ACTIONS')
    logger.info('Getting Pull Requests with Actions')
    gh_preqs = [ghinterface_obj.client.get_repo(repo['address'])
                .get_pulls(state='open', sort='created', base=repo['base'])
                for repo in repos]
    each_pr = [preq for gh_preq in gh_preqs for preq in gh_preq]
    preq_labels = [{'preq': pr, 'label': label} for pr in each_pr
                   for label in pr.get_labels()]

    jobs = []
    # return_preq = []
    for pr_label in preq_labels:
        compiler, match = set_action_from_label(machine, actions,
                                                pr_label['label'])
        if match:
            pr_label['action'] = match.copy()
            # return_preq.append(pr_label.copy())
            jobs.append(Job(pr_label.copy(), ghinterface_obj, machine, compiler))

    return jobs


class Job:
    '''
    This class stores all information needed to run jobs on this machine.
    This class provides all methods needed to run all jobs.
    ...

    Attributes
    ----------
    preq_dict: dict
        Dictionary of all data that comes from the GitHub pull request
    ghinterface_obj: object
        An interface to GitHub setup through class GHInterface
    machine: dict
        Information about the machine the jobs will be running on
        provided by the bash script
    '''

    def __init__(self, preq_dict, ghinterface_obj, machine, compiler):
        self.logger = logging.getLogger('JOB')
        self.preq_dict = preq_dict
        try:
            self.job_mod = importlib.import_module(
                           f'jobs.{self.preq_dict["action"].lower()}')
        except Exception:
            raise ModuleNotFoundError(f'Module: \
                  {self.preq_dict["action"]} not found')
        self.ghinterface_obj = ghinterface_obj
        self.machine = machine
        self.compiler = compiler
        self.comment_text = ''
        self.failed_tests = []

    def comment_text_append(self, newtext):
        self.comment_text += f'{newtext}\n'

    def remove_pr_label(self):
        ''' Removes the PR label that initiated the job run from PR '''
        self.logger.info(f'Removing Label: {self.preq_dict["label"]}')
        self.preq_dict['preq'].remove_from_labels(self.preq_dict['label'])

    def check_label_before_job_start(self):
        # LETS Check the label still exists before the start of the job in the
        # case of multiple jobs
        label_to_check = f'{self.machine["name"]}'\
                         f'-{self.compiler}'\
                         f'-{self.preq_dict["action"]}'
        labels = self.preq_dict['preq'].get_labels()
        label_match = next((label for label in labels
                            if re.match(label.name, label_to_check)), False)

        return label_match

    def run_commands(self, logger, commands_with_cwd):
        for command, in_cwd in commands_with_cwd:
            logger.info(f'Running `{command}`')
            logger.info(f'in location "{in_cwd}"')
            try:
                output = subprocess.Popen(command, shell=True, cwd=in_cwd,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT)
            except Exception as e:
                self.job_failed(logger, 'subprocess.Popen', exception=e)
            else:
                try:
                    out, err = output.communicate()
                    out = [] if not out else out.decode('utf8').split('\n')
                    logger.info(out)
                except Exception as e:
                    err = [] if not err else err.decode('utf8').split('\n')
                    self.job_failed(logger, f'Command {command}', exception=e,
                                    out=out, err=err)
                else:
                    logger.info(f'Finished running: {command}')

    def run(self):
        logger = logging.getLogger('JOB/RUN')
        logger.info(f'Starting Job: {self.preq_dict["label"]}')
        self.comment_text_append(newtext=f'Machine: {self.machine["name"]}')
        self.comment_text_append(f'Compiler: {self.compiler}')
        self.comment_text_append(f'Job: {self.preq_dict["action"]}')
        if self.check_label_before_job_start():
            try:
                logger.info('Calling remove_pr_label')
                # self.remove_pr_label()
                logger.info('Calling Job to Run')
                self.job_mod.run(self)
                # logger.info('Calling clone_pr_repo')
                # self.clone_pr_repo()
                # logger.info('Calling execute_action')
                # self.execute_action()
            except Exception as e:
                self.job_failed(logger, 'run()', exception=e, STDOUT=False)
                logger.info('Sending comment text')
                self.send_comment_text()
        else:
            logger.info(f'Cannot find label {self.preq_dict["label"]}')

    def send_comment_text(self):
        logger = logging.getLogger('JOB/SEND_COMMENT_TEXT')
        logger.info(f'Comment Text: {self.comment_text}')
        self.comment_text_append('Please make changes and add '
                                 'the following label back:')
        self.comment_text_append(f'{self.machine["name"]}'
                                 f'-{self.compiler}'
                                 f'-{self.preq_dict["action"]}')

        self.preq_dict['preq'].create_issue_comment(self.comment_text)

    def job_failed(self, logger, job_name, exception=Exception, STDOUT=False,
                   out=None, err=None):
        self.comment_text_append(f'{job_name} FAILED. Exception:{exception}')
        logger.critical(f'{job_name} FAILED. Exception:{exception}')

        if STDOUT:
            logger.critical(f'STDOUT: {[item for item in out if not None]}')
            logger.critical(f'STDERR: {[eitem for eitem in err if not None]}')


def main():

    # handle logging
    log_filename = f'rt_auto_'\
                   f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.log'
    logging.basicConfig(filename=log_filename, filemode='w',
                        level=logging.INFO)
    logger = logging.getLogger('MAIN')
    logger.info('Starting Script')

    # handle input args
    logger.info('Parsing input args')
    args = parse_args_in()

    # get input data
    logger.info('Calling input_data().')
    machine, repos, actions = input_data(args)

    # setup interface with GitHub
    logger.info('Setting up GitHub interface.')
    ghinterface_obj = GHInterface()

    # get all pull requests from the GitHub object
    logger.info('Getting all pull requests, '
                'labels and actions applicable to this machine.')
    preq_dict = get_preqs_with_actions(repos, machine,
                                       ghinterface_obj, actions)
    # add Job objects and run them
    logger.info('Adding all jobs to an object list and running them.')
    jobs = [Job(pullreq, ghinterface_obj, machine) for pullreq in preq_dict]
    [job.run() for job in jobs]

    logger.info('Script Finished')


if __name__ == '__main__':
    main()
