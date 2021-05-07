"""Automation of UFS Regression Testing

This script automates the process of UFS regression testing for code managers
at NOAA-EMC

This script should be started through rt_auto.sh so that env vars are set up
prior to start.
"""
import subprocess
import os
import logging
import yaml
from setup_jobs import GHInterface
import bl
import rt


class Job:

    def __init__(self, file):
        logging.info("Initializing Job Class")
        self.file = file
        logging.debug(f'Job File: {file}')
        self.has_dict_been_updated = False

        self.read_dict()
        logging.info("Finished Inlitializing Job Class")

    def read_dict(self):
        logging.info('Reading Job File')
        with open(self.file) as infile:
            self.dict = yaml.full_load(infile)
        logging.info('Finished Reading Job File')

    def write_dict(self):
        logging.info('Writing Dict to Job File')
        with open(self.file, 'w') as outfile:
            yaml.dump(self.dict, outfile)
        logging.info('Finished Writing to Job File')

    def update_key(self, key, value):
        logging.info('Updating a key in Job dictionary')
        logging.debug(f'Updating "{key}" from "{self.dict[key]}" with "{value}"')
        self.dict[key] = value
        self.write_dict()
        self.has_dict_been_updated = True
        logging.info('Finished updating key in Job dictionary')

    def get_value(self, key):
        logging.info('Getting value from Job dictionary')
        logging.debug(f'Has dictionary been updated?: {self.has_dict_been_updated}')
        if self.has_dict_been_updated:
            self.read_dict()
            self.has_dict_been_updated = False
        value = self.dict[key]
        logging.debug(f'Received value "{value}" from key "{key}"')
        logging.info('Finished getting value from Job dictionary')
        return value

    def failed(self):
        logging.error('Job has failed')
        logging.info('Processing a failure')
        self.update_key('Status', 'Failed')
        self.send_comment_text()
        logging.info('Finished a processing failure')

    def send_comment_text(self):
        # MOVE THIS TO TAKE job_dict INFORMATION AND SEND COMMENT IF NEEDED
        logging.info('Sending information to GitHub PR')
        pull_request = self.get_pr_obj()
        comment_text = f'''
        Machine: {self.get_value("Machine")}
        Compiler: {self.get_value("Compiler")}
        Status: {self.get_value("Status")}
        PR Dir: {self.get_value("PR Dir")}
        '''
        if self.get_value('Failed Tests') is not None:
            comment_text += f'Failed Tests: {self.get_value("Failed Tests")}\n'
        comment_text += f'Notes: {self.get_value("Notes")}\n'
        logging.debug(f'Sending comment text to Github: {comment_text}')
        pull_request.create_issue_comment(comment_text)
        logging.info('Finished sending information to GitHub PR')

    def get_pr_obj(self):
        logging.info('Getting Pull Request Object from pyGitHub')
        ghinterface_obj = GHInterface()
        pull_request = ghinterface_obj.client.get_repo(self.get_value(
                       'Repo ID')).get_pull(self.get_value('PR Number'))
        logging.debug(f'Type of pull_request is: {type(pull_request)}')
        logging.info('Finished getting pull request object from pyGitHub')
        return pull_request

    def clone_pr_repo(self):
        logging.info('Cloning PR Repo')
        self.update_key('Job', 'Cloning PR Repo')
        self.update_key('Status', 'Running')
        pull_request = self.get_pr_obj()
        logging.debug(f'pull_request: {pull_request}')
        repo_name = pull_request.head.repo.name
        logging.debug(f'repo_name: {repo_name}')
        branch = pull_request.head.ref
        logging.debug(f'branch: {branch}')
        git_url = pull_request.head.repo.html_url.split('//')
        git_url = f'{git_url[0]}//${{ghapitoken}}@{git_url[1]}'
        logging.debug(f'git_url: {git_url}')
        pr_repo_loc = f'{self.get_value("PR Dir")}/{repo_name}'
        logging.debug(f'pr_repo_loc: {pr_repo_loc}')

        # If the directory already exists, we don't need to create it again
        create_repo_commands = []
        if not os.path.exists(self.get_value("PR Dir")):
            logging.debug('I do not see the PR dir, creating it')
            os.makedirs(self.get_value("PR Dir"))
            create_repo_commands.extend([
                [f'git clone -b {branch} {git_url}', self.get_value("PR Dir")],
                ['git config user.email "brian.curtis@noaa.gov"', pr_repo_loc],
                ['git config user.name "Brian Curtis"', pr_repo_loc]
            ])
        else:
            logging.debug('I already see the PR Dir, not creating it again')
            create_repo_commands.extend([
                [f'git pull origin {branch}', pr_repo_loc]
            ])
        create_repo_commands.extend([
            ['git submodule update --init --recursive', pr_repo_loc]
        ])
        logging.debug(f'create_repo_commands: {create_repo_commands}')
        try:
            self.run_commands(create_repo_commands)
        except Exception:
            self.failed()
        self.update_key('Status', 'Completed')
        logging.info('Finished Cloning PR Repo')

    def run_commands(self, commands_with_cwd):
        logging.info('Running Commands')
        for command, in_cwd in commands_with_cwd:
            logging.info(f'Running `{command}`')
            logging.debug(f'in location "{in_cwd}"')
            try:
                output = subprocess.Popen(command, shell=True, cwd=in_cwd,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT)
            except Exception as e:
                logging.error(f'Exception: {e}')
                raise RuntimeError(e)
            else:
                try:
                    out, err = output.communicate()
                    out = [] if not out else out.decode('utf8').split('\n')
                    logging.debug(out)
                except Exception as e:
                    err = [] if not err else err.decode('utf8').split('\n')
                    logging.error(f'Exception: {e}')
                    logging.error(f'Command Error {err}')
                    raise RuntimeError(e)
                else:
                    logging.info(f'`{command}` Completed')
        logging.info('Finished Rinning Commands')

    def check_and_remove_old_job(self):
        logging.info("Checking if PR is mergable and removing if not")
        removal_commands = []
        pull_request = self.get_pr_obj()
        logging.debug(f'pull_request.mergeable: {pull_request.mergeable}')
        if not pull_request.mergeable:
            pr_num = self.get_value('PR Number')
            rt_dirs = self.get_value('RT Dirs')
            removal_commands.extend([
                [f'rm -rf {os.getcwd()}/pr/{pr_num}', os.getcwd()]
            ])
            for rt_dir in rt_dirs:
                removal_commands.extend([
                    [f'rm -rf {rt_dir}', os.getcwd()]
                ])
            logging.debug(f'removal_commands: {removal_commands}')
            try:
                self.run_commands(removal_commands)
            except RuntimeError:
                logging.critical('Issues removing old files/directories')
                notes = self.get_value('Notes')
                notes += 'Issues removing old files/directories from '\
                         f'closed/merged PR {os.getcwd()}/pr/{pr_num}. '\
                         'Please remove manually\n'
                self.update_key('Notes', notes)
                self.failed()
                raise RuntimeError('Issue removing old files/directories')
        logging.info('Finished checking if PR is mergable and removing if not')

    def setup_env(self):
        logging.info('Setting up HPC accouunt information')
        machine = self.get_value('Machine')
        logging.debug(f':machine {machine}')
    
        if machine == 'jet':
            os.environ['ACCNR'] = 'h-nems'
        elif machine == 'gaea':
            os.environ['ACCNR'] = 'nggps_emc'
        elif machine == 'cheyenne':
            os.environ['ACCNR'] = 'P48503002'
    
        logging.info('Finished setting up HPC account information')

    def run(self):
        logging.info('Processing Job Card')
        self.setup_env()
        self.check_and_remove_old_job()
        if self.get_value('Status') == 'New':
            logging.debug('Status is "New"')
            self.clone_pr_repo()
            # Here we check to run BL
            if self.get_value('New Baselines'):
                logging.debug('PR requests "New Baselines", running "BL" job')
                bl.run(self)
                # Once completed successfully, run the RT
                if self.get_value('Job') == 'BL' \
                   and self.get_value('Status') == 'Completed':
                    rt.run(self)
                else:
                    logging.error('Baseline creation failed')
                    notes = self.get_value('Notes')
                    notes += 'Baseline creation failed\n'
                    self.update_key('Notes', notes)
                    self.failed()
                    raise RuntimeError('Baseline creation failed')
            else:
                # Just run the RT
                logging.debug('I do not see "New Baselines", running "RT" job')
                rt.run(self)
                if self.get_value('Job') == 'RT' \
                   and self.get_value('Status') == 'Failed':
                    logging.error('Regression testing job failed')
                    notes = self.get_value('Notes')
                    notes += 'Regression test job failed\n'
                    self.update_key('Notes', notes)
                    self.failed()
                    raise RuntimeError('Regression test job failed')
        elif self.get_value('Status') == 'Fixed':
            logging.debug('I see a status of "Fixed" in job card')
            if self.get_value('Job') == 'BL':
                bl.run(self)
            elif self.get_value('Job') == 'RT':
                rt.run(self)
            elif self.get_value('Job') == 'Cloning PR Repo':
                self.update_key('Status', 'New')
                self.run()
            else:
                logging.error('I cannot identify where to start' \
                              'Please change job card "Status" to "New"')
                notes = self.get_value('Notes')
                notes += 'Saw "Fixed" in job card, but can not identify '\
                         'where to start. Please change "Status" to "New"\n'
                self.update_key('Notes', notes)
                self.failed()
                raise RuntimeError('Unable to identify where to start')
        else:
            logging.error('Status is not "New" or "Fixed", please set')
            notes = self.get_value('Notes')
            notes += 'Job Card Status is not "New" or "Fixed", please set\n'
            self.update_key('Notes', notes)
            self.failed()
            raise RunetimeError('Status is not "New" or "Fixed", please set')
        logging.info('Finished Processing Job Card')


def get_job_files():
    logging.info('Getting Job Files')
    job_file_list = []
    files = os.listdir('./')
    for file in files:
        if '.yaml' in file:
            job_file_list.append(file)
    logging.debug(f'Job File List: {job_file_list}')
    logging.info('Finished Getting Job Files')
    return job_file_list


def main():
    logging.basicConfig(format='%(asctime)s, %(levelname)-8s '
                               '[%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename='autort.log',
                        level=logging.DEBUG)
    logging.info('Starting Main')
    job_files = get_job_files()
    job_obj_list = [Job(job_file) for job_file in job_files]
    for job_obj in job_obj_list:
        job_obj.run()
    logging.info('Finishing Main')


if __name__ == '__main__':
    main()
