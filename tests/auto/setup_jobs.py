"""Automation of UFS Regression Testing

This script automates the process of UFS regression testing for code managers
at NOAA-EMC

This script should be started through rt_auto.sh so that env vars are set up
prior to start.
"""
import os
import logging
import yaml


# TODO: Write compile dictionaries to yaml
class Rt_compile:

    def __init__(self, number, conf_line):

        compile_dict = {}
        compile_dict['number'] = number
        compile_dict['debug'] = False
        compile_dict['bit32'] = False
        compile_dict['repro'] = False
        compile_dict['multigases'] = False
        compile_dict['status'] = None
        compile_dict['conf_line'] = conf_line
        compile_dict['task_list'] = []

        splitline = compile_dict['conf_line'].split('|')
        infos = splitline[1].split(' ')
        for info in infos:
            info_split = info.split('=')
            if info_split[0].strip() == 'APP':
                compile_dict['app'] = info_split[1]
            elif info_split[0].strip() == '32BIT':
                compile_dict['bit32'] = True
            elif info_split[0].strip() == 'DEBUG':
                compile_dict['debug'] = True
            elif info_split[0].strip() == 'SUITES':
                compile_dict['suites'] = info_split[1].split(',')
            elif info_split[0].strip() == 'REPRO':
                compile_dict['repro'] = True
            elif info_split[0].strip() == 'MULTI_GASES':
                compile_dict['multigases'] = True
        compile_dict['fv3'] = splitline[3].strip()
        self.compile_dict = compile_dict

    def __repr__(self):
        return 'Rt_compile()'

    def __str__(self):
        myret = f'Compile: {self.compile_dict["number"]}\n'
        myret += f'App: {self.compile_dict["app"]}\n'
        myret += f'Debug: {self.compile_dict["debug"]}\n'
        myret += f'32BIT: {self.compile_dict["bit32"]}\n'
        myret += f'Suites: {self.compile_dict["suites"]}\n'
        myret += f'Repro: {self.compile_dict["repro"]}\n'
        myret += f'Multigases: {self.compile_dict["multigases"]}\n'
        myret += f'FV3: {self.compile_dict["fv3"]}\n'
        myret += f'Status: {self.compile_dict["status"]}\n'
        myret += f'Conf Line: {self.compile_dict["conf_line"]}\n'
        myret += 'Tasks:\n'
        for task in self.compile_dict["task_list"]:
            myret += f'--{task["name"]}\n'

        return myret

    def add_task(self, task_dict):
        self.compile_dict['task_list'].append(task_dict)


class Rt_task:
    '''
    This function takes a RUN line from rt.conf and creates a Rt_task object
    '''

    def __init__(self, compile, conf_line):
        task_dict = {}
        task_dict['compile'] = compile
        task_dict['conf_line'] = conf_line
        # self.compile = compile
        # self.conf_line = conf_line

        splitline = task_dict['conf_line'].split('|')
        task_dict['name'] = splitline[1].strip()
        # self.name = splitline[1].strip()
        if compile.compile_dict["repro"]:
            task_dict['name'] += '_repro'
            # self.name += '_repro'
        task_dict['fv3'] = splitline[3].strip()
        task_dict['dependency'] = splitline[4].strip()
        task_dict['status'] = None
        # self.fv3 = splitline[3].strip()
        # self.dependency = splitline[4].strip()
        # self.status = None
        self.task_dict = task_dict
        compile.add_task(self.task_dict)

    def __repr__(self):
        return 'Rt_task()'

    def __str__(self):
        myret = f'Compile: {self.task_dict["compile"]}\n'
        myret += f'Conf Line: {self.task_dict["conf_line"]}'
        myret += f'Name: {self.task_dict["name"]}\n'
        myret += f'Dependency: {self.task_dict["dependency"]}\n'
        myret += f'FV3: {self.task_dict["fv3"]}\n'
        myret += f'Status: {self.task_dict["status"]}\n'

        return myret


def clone_pr_repo(job_obj):
    logging.info('Cloning PR Repo')
    logging.debug(f'pull_request: {job_obj.pull_request}')
    repo_name = job_obj.pull_request.head.repo.name
    logging.debug(f'repo_name: {repo_name}')
    branch = job_obj.pull_request.head.ref
    logging.debug(f'branch: {branch}')
    git_url = job_obj.pull_request.head.repo.html_url.split('//')
    git_url = f'{git_url[0]}//${{ghapitoken}}@{git_url[1]}'
    logging.debug(f'git_url: {git_url}')
    pr_repo_loc = f'{job_obj.get_value("PR Dir")}/{repo_name}'
    logging.debug(f'pr_repo_loc: {pr_repo_loc}')

    # If the directory already exists, we don't need to create it again
    create_repo_commands = []
    if not os.path.exists(job_obj.get_value("PR Dir")):
        logging.debug('I do not see the PR dir, creating it')
        os.makedirs(job_obj.get_value("PR Dir"))
        create_repo_commands.extend([
            [f'git clone -b {branch} {git_url}', job_obj.get_value("PR Dir")],
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
        job_obj.run_commands(create_repo_commands)
    except Exception:
        job_obj.failed()
    logging.info('Finished Cloning PR Repo')


def process_rt_conf(job_obj):
    compile_num = 1
    compile_list = []
    machine = job_obj.get_value('Machine')
    compiler = job_obj.get_value('Compiler')
    conf_file_loc = f'{job_obj.get_value("PR Dir")}/ufs-weather-model/tests/'\
                    f'{job_obj.get_value("Conf File")}'
    with open(conf_file_loc) as f:
        for line in f:
            splitline = line.split('|')
            if splitline[0].strip() == 'COMPILE':
                machine_info = splitline[2].split(' ')
                if ('-' in machine_info
                   and f'{machine}.{compiler}' in machine_info):
                    continue
                elif ('+' in machine_info
                      and f'{machine}.{compiler}' not in machine_info):
                    continue
                compile_list.append(Rt_compile(compile_num, line))
                compile_num += 1
            elif splitline[0].strip() == 'RUN':
                machine_info = splitline[2].split(' ')
                if ('-' in machine_info
                   and f'{machine}.intel' in machine_info):
                    continue
                elif ('+' in machine_info
                      and f'{machine}.intel' not in machine_info):
                    continue
                Rt_task(compile_list[-1], line)
    return compile_list


def compile_tasks_to_file(job_obj, compile_list):
    for compile in compile_list:
        with open(f'{job_obj.get_value("PR Dir")}'
                  '/ufs-weather-model/tests/'
                  f'compile_{compile.compile_dict["number"]}.yaml',
                  'w') as file:
            yaml.dump(compile.compile_dict, file)
        for task in compile.compile_dict['task_list']:
            print(f'{compile.compile_dict["task_list"]}')
            with open(f'{job_obj.get_value("PR Dir")}'
                      '/ufs-weather-model/tests/'
                      f'{task.task_dict["name"]}.yaml',
                      'w') as file2:
                yaml.dump(task.task_dict, file2)


def run(job_obj):
    job_obj.update_key('Job', 'Setup')
    job_obj.update_key('Status', 'Started')
    clone_pr_repo(job_obj)
    compile_list = process_rt_conf(job_obj)
    compile_tasks_to_file(job_obj, compile_list)
    job_obj.update_key('Status', 'Finished')
    logging.info('Finished Processing Job Card')
