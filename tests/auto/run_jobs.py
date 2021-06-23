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
from prep_jobs import GHInterface
import bl
import rt
import setup_jobs
import process_jobs


class Job:

    def __init__(self, file):
        logging.info("Initializing Job Class")
        self.file = file
        logging.debug(f'Job File: {file}')
        self.has_dict_been_updated = False

        self.read_dict()
        logging.info("Finished Inlitializing Job Class")
        self.get_pr_obj()

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
        logging.debug(f'Updating "{key}" from "{self.dict[key]}" '
                      f'with "{value}"')
        self.dict[key] = value
        self.write_dict()
        self.has_dict_been_updated = True
        logging.info('Finished updating key in Job dictionary')

    def get_value(self, key):
        logging.info('Getting value from Job dictionary')
        logging.debug('Has dictionary been updated?: '
                      f'{self.has_dict_been_updated}')
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

        def send_comment_text():
            # MOVE THIS TO TAKE job_dict INFORMATION AND SEND COMMENT IF NEEDED
            logging.info('Sending information to GitHub PR')
            comment_text = f'Machine: {self.get_value("Machine")}\n'\
                           f'Compiler: {self.get_value("Compiler")}\n'\
                           f'Status: {self.get_value("Status")}\n'\
                           f'PR Dir: {self.get_value("PR Dir")}\n'
            if self.get_value('Failed Tests') is not None:
                comment_text += f'Failed Tests: {self.get_value("Failed Tests")}\n'
            comment_text += f'Notes: {self.get_value("Notes")}\n'
            logging.debug(f'Sending comment text to Github: {comment_text}')
            self.pull_request.create_issue_comment(comment_text)
            logging.info('Finished sending information to GitHub PR')

        send_comment_text()
        logging.info('Finished a processing failure')

    def get_pr_obj(self):
        logging.info('Getting Pull Request Object from pyGitHub')
        ghinterface_obj = GHInterface()
        self.pull_request = ghinterface_obj.client.get_repo(self.get_value(
                       'Repo ID')).get_pull(self.get_value('PR Number'))
        logging.debug(f'Type of pull_request is: {type(self.pull_request)}')
        logging.info('Finished getting pull request object from pyGitHub')

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
        logging.debug(f'pull_request.mergeable: {self.pull_request.mergeable}')
        if not self.pull_request.mergeable:
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

    def failed_tests_to_conf(self):
        pr_repo_loc = f'{self.get_value("PR Dir")}/'\
                      f'{self.pull_request.head.repo.name}'
        logging.info('Creating rt_auto.conf file for failed tests')
        rt_conf_file = 'tests/rt.conf'
        fail_string_list = self.get_value('Failed Tests')
        rt_auto_conf_file = open('rt_auto.conf', 'a')
        has_compile_line_changed = False
        if os.path.exists(f'{pr_repo_loc}/{rt_conf_file}'):
            with open(f'{pr_repo_loc}/{rt_conf_file}') as f:
                for line in f:
                    if 'COMPILE' in line:
                        current_compile_line = line
                        has_compile_line_changed = True
                    if 'RUN' in line:
                        test = line.split('|')[1].strip()
                        if any(test in x for x in fail_string_list):
                            if has_compile_line_changed:
                                rt_auto_conf_file.write(
                                    f'{current_compile_line}\n')
                                has_compile_line_changed = False
                            rt_auto_conf_file.write(f'{line}\n')
            rt_auto_conf_file.close()
            self.update_key('Conf File', 'rt_auto.conf')
        else:
            logging.error('Could not read rt.conf')
            notes = self.get_value('Notes')
            notes += 'Could not read rt.conf\n'
            self.update_key('Notes', notes)
            self.failed()
            raise FileNotFoundError('Could not read rt.conf')
        logging.info('Finished creating rt_auto.conf file for failed tests')

    # def process_logfile(self):
    #     pr_repo_loc = f'{self.get_value("PR Dir")}/'\
    #                   f'{self.pull_request.head.repo.name}'
    #     logging.info('Processing Log File')
    #     machine = self.get_value('Machine')
    #     compiler = self.get_value('Compiler')
    #     logfile = f'tests/RegressionTests_{machine}.{compiler}.log'
    #     rt_dirs = []
    #     failed_jobs = []
    #     fail_string_list = ['Test', 'failed']
    #     logging.debug(f'Checking Path {pr_repo_loc}/{logfile}')
    #     if os.path.exists(f'{pr_repo_loc}/{logfile}'):
    #         with open(f'{pr_repo_loc}/{logfile}') as f:
    #             for line in f:
    #                 if all(x in line for x in fail_string_list):
    #                     failed_jobs.extend(f'{line.rstrip(chr(10))}')
    #                 elif 'working dir' in line and not rt_dirs:
    #                     rt_dirs = self.get_value('RT Dirs')
    #                     if rt_dirs is None:
    #                         rt_dirs = [os.path.split(line.split()[-1])[0]]
    #                     else:
    #                         rt_dirs.extend(os.path.split(line.split()[-1])[0])
    #                     self.update_key('RT Dirs', rt_dirs)
    #                 elif 'SUCCESSFUL' in line:
    #                     notes = self.get_value('Notes')
    #                     notes += 'RT Log Shows Success\n'
    #                     self.update_key('Notes', notes)
    #                     logging.info('Finished Processing Log File')
    #                     return True
    #         logging.error('Could not find "SUCCESSFUL" in log file, '
    #                       'assuming a failure')
    #         notes = self.get_value('Notes')
    #         notes += 'Could not find "SUCCESSFUL" in log file, '\
    #                  'assuming a failure\n'
    #         self.update_key('Notes', notes)
    #         self.update_key('Failed Tests', failed_jobs)
    #         self.failed_tests_to_conf()
    #         self.failed()
    #         raise ValueError('Could not find "SUCCESSFUL" in log file')
    #     else:
    #         logging.error(f'Could not find {machine}.{compiler} log')
    #         notes = self.get_value('Notes')
    #         notes += f'Could not find {machine}.{compiler} log\n'
    #         self.update_key('Notes', notes)
    #         self.failed()
    #         raise FileNotFoundError(f'Could not find {machine}.{compiler} log')

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

    # STEPS
    # Prep - DONE SEPARATELY
    # Setup
    # BL
    # RT
    # Process
    # Finished -> Processed (after process_jobs)

    def check_fixed(self):
        if self.get_value('Job') == 'Setup':
            setup_jobs.run(self)
        elif self.get_value('Job') == 'BL':
            bl.run(self)
        elif self.get_value('Job') == 'RT':
            rt.run(self)
        elif self.get_value('Job') == 'Process':
            process_jobs.run(self)
        else:
            logging.error('Status is "Fixed" but Job is '
                          'unidentifiable')
            notes = self.get_value('Notes')
            notes += 'Status is "Fixed" but Job is '\
                     'unidentifiable\n'
            self.update_key('Notes', notes)
            self.failed()
            raise RuntimeError('Status is "Fixed" but Job is '
                               'unidentifiable')

    def check_finished(self):
        if self.get_value('Job') == 'Prep':
            setup_jobs.run(self)
            sys.exit()
        elif self.get_value('Job') == 'Setup':
            if self.get_value('New Baselines'):
                bl.run(self)
            else:
                rt.run(self)
        elif self.get_value('Job') == 'BL':
            process_jobs.run(self)
        elif self.get_value('Job') == 'RT':
            process_jobs.run(self)
        else:
            logging.error('Status is "Finished" but Job is '
                          'unidentifiable')
            notes = self.get_value('Notes')
            notes += 'Status is "Finished" but Job is '\
                     'unidentifiable\n'
            self.update_key('Notes', notes)
            self.failed()
            raise RuntimeError('Status is "Finished" but Job is '
                               'unidentifiable')

    def run(self):
        logging.info('Processing Job Card')
        self.setup_env()
        self.check_and_remove_old_job()
        if self.get_value('Status') == 'Failed':
            logging.info('Job in "Failed" status, doing nothing')
            return

        elif self.get_value('Status') == 'Completed':
            logging.info('Job is completed, not proceeding')
            return

        elif (self.get_value('Status') == 'Fixed'):
            self.check_fixed()

        elif (self.get_value('Status') == 'Finished'):
            self.check_finished()

        elif self.get_value('Status') == 'Processed':
            if self.get_value('Job') == 'BL':
                rt.run(self)
            elif self.get_value('Job') == 'RT':
                self.update_key('Status', 'Completed')
                logging.info('Regression Testing Processed, Job Completed')
                return
        else:
            logging.error('Unknown Status')
            notes = self.get_value('Notes')
            notes += 'Unknown Status\n'
            self.update_key('Notes', notes)
            self.failed()
            raise RuntimeError('Unknown Status')


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
