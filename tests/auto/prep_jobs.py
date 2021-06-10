"""Automation of UFS Regression Testing

This script automates the process of UFS regression testing for code managers
at NOAA-EMC

This script should be started through rt_auto.sh so that env vars are set up
prior to start.
"""
from github import Github as gh
import re
import os
import logging
import yaml


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
        logging.debug('initializing GitHub interface using pyGitHub')
        filename = 'accesstoken'

        if os.path.exists(filename):
            if oct(os.stat(filename).st_mode)[-3:] != 600:
                with open(filename) as f:
                    os.environ['ghapitoken'] = f.readline().strip('\n')
            else:
                logging.error('accesstoken permission needs to be "600" ')
                raise Exception('accesstoken permission needs to be "600" ')
        else:
            logging.error('Cannot find file "accesstoken"')
            raise FileNotFoundError('Cannot find file "accesstoken"')

        try:
            self.client = gh(os.getenv('ghapitoken'))
        except Exception as e:
            logging.critical(f'Exception is {e}')
            raise Exception


def setup_env():
    hostname = os.getenv('HOSTNAME')
    logging.debug(f'Hostname: {hostname}')
    if bool(re.match(re.compile('hfe.+'), hostname)):
        machine = 'hera'
        compilers = ['gnu', 'intel']
    elif bool(re.match(re.compile('fe.+'), hostname)):
        machine = 'jet'
        compilers = ['intel']
    elif bool(re.match(re.compile('gaea.+'), hostname)):
        machine = 'gaea'
        compilers = ['intel']
    elif bool(re.match(re.compile('Orion-login.+'), hostname)):
        machine = 'orion'
        compilers = ['intel']
    elif bool(re.match(re.compile('chadmin.+'), hostname)):
        machine = 'cheyenne'
        compilers = ['gnu', 'intel']
    elif bool(re.match(re.compile('neon'), hostname)):
        machine = 'neon'
        compilers = ['gnu', 'intel']
    else:
        raise KeyError(f'Hostname: {hostname} does not match '
                       'for a supported system. Exiting.')
    logging.debug(f'Machine: {machine}, Compilers: {compilers}')
    return machine, compilers


def create_job_yaml(machine, compilers, ghinterface_obj, repo, pull_request):
    # SEARCH FOR CURRENT JOB BASED ON PULL REQUEST ID AND COMPILER
    # CREATE YAML FILE PER COMPILER BASED ON LABELS IN PULL REQUEST
    for compiler in compilers:
        if os.path.exists(f'./{pull_request.number}-{compiler}.yaml'):
            continue
        job_dict = get_default_job_dict()
        job_dict['Machine'] = machine
        job_dict['Compiler'] = compiler
        job_dict['Repo ID'] = repo.id
        job_dict['PR Number'] = pull_request.number
        job_dict['PR Dir'] = f'{os.getcwd()}/pr/'\
                             f'{pull_request.number}/{compiler}'
        for label in pull_request.get_labels():
            if label.name == 'Baseline Change':
                job_dict['New Baselines'] = True

        if compiler == 'intel':
            job_dict['Conf File'] = 'rt.conf'
        else:
            job_dict['Conf File'] = f'rt_{compiler}.conf'

        with open(f'./{pull_request.number}-{compiler}.yaml', 'w') as file:
            yaml.dump(job_dict, file)


def get_actionable_pull_requests(pull_requests):
    actionable_prs = []
    for pull_request in pull_requests:
        for label in pull_request.get_labels():
            if label.name == 'AutoRT':
                actionable_prs.append(pull_request)

    return actionable_prs


def get_default_job_dict():
    job_dict = {}
    job_dict['Machine'] = None
    job_dict['Compiler'] = None
    job_dict['Job'] = None
    job_dict['Repo ID'] = None
    job_dict['PR Number'] = None
    job_dict['Status'] = 'New'
    job_dict['PR Dir'] = None
    job_dict['RT Dirs'] = None  # Need to know what to delete afterwards
    job_dict['New Baselines'] = False
    job_dict['Conf File'] = None
    job_dict['Notes'] = ''
    job_dict['Failed Tests'] = None

    return job_dict


def main():
    logging.basicConfig(format='%(asctime)s, %(levelname)-8s '
                               '[%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename='autort.log',
                        level=logging.DEBUG)
    logging.info('Starting Job Setup')

    # setup environment
    logging.info('Getting the environment setup')
    machine, compilers = setup_env()

    # setup interface with GitHub
    logging.info('Setting up GitHub interface.')
    ghinterface_obj = GHInterface()

    # get all pull requests from the GitHub object
    # and turn them into Job objects
    logging.info('Getting all pull requests')
    repo = ghinterface_obj.client.get_repo('BrianCurtis-NOAA/ufs-weather-model',
                                           'develop')
    logging.getLogger('github').setLevel(logging.WARNING)
    pull_requests = repo.get_pulls()
    actionable_pull_requests = get_actionable_pull_requests(pull_requests)
    for apr in actionable_pull_requests:
        create_job_yaml(machine, compilers, ghinterface_obj, repo, apr)

    logging.info('Script Finished')


if __name__ == '__main__':
    main()
