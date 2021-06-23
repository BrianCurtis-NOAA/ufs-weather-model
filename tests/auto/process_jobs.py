import logging
import os
import glob
import yaml


def find_task(compiles, task_name):
    for compile in compiles:
        match = next((task for task in compile.task_list
                      if task.name == task_name), None)
        if match is not None:
            return match

    return None


def write_new_conf(compiles):
    tests_added = []
    new_conf_file = '../rt_auto.conf'
    with open(new_conf_file, 'w') as f:
        for compile in compiles:
            compile_used = False
            if compile.status == 'Failed':
                f.write(compile.conf_line)
                for task in compile.task_list:
                    f.write(task.conf_line)
            elif compile.status == 'Completed':
                for task in compile.task_list:
                    if task.status == 'Failed':
                        if not compile_used:
                            f.write(compile.conf_line)
                            compile_used = True
                        if task.dependency:
                            thistask = find_task(compiles, task.dependency)
                            if thistask.name not in tests_added:
                                tests_added.append(thistask.name)
                                f.write(thistask.conf_line)
                        if task.name not in tests_added:
                            tests_added.append(task.name)
                            f.write(task.conf_line)


def update_status(compiles, machine):
    failure = False
    for compile in compiles:
        for task in compile.task_list:
            task.status = 'Failed'
            filename_t = glob.glob(f'../log_{machine}.intel/run_*_'
                                   f'{task.name}.log')
            try:
                with open(filename_t[0]) as f:
                    for line in f:
                        if 'PASS' in line:
                            task.status = 'Completed'
            except (FileNotFoundError, IndexError):
                task.status = 'Failed'
            if task.status == 'Failed':
                failure = True

    return failure


def get_compile_file_list(job_obj):
    logging.info('Getting Compile Files')
    compile_list = []
    files = os.listdir(f'{job_obj["PR Dir"]}/ufs-weather-model/tests/auto')

    for file in files:
        if 'compile' in file and '.yaml' in file:
            compile_list.append(file)
    logging.debug(f'Compile List: {compile_list}')
    logging.info('Finished Getting Compile Files')
    return compile_list

def get_task_file_list(job_obj):
    logging.info('Getting Task Files')
    task_file_list = []
    files = os.listdir(f'{job_obj["PR Dir"]}/ufs-weather-model/tests/auto')

    for file in files:
        if not 'compile' in file and '.yaml' in file:
            task_file_list.append(file)
    logging.debug(f'Task File List: {task_file_list}')
    logging.info('Finished Getting Task Files')
    return task_file_list


def read_dict(self):
    logging.info('Reading Job File')
    with open(self.file) as infile:
        self.dict = yaml.full_load(infile)
    logging.info('Finished Reading Job File')


def run(job_obj):
    compiles = get_job_files


def run(job_obj):
    compiles = process_rt_conf(machine, compiler)
    failure = update_status(compiles, machine)
    if failure:
        write_new_conf(compiles)
        print('===========\nHERE IS WHERE I WOULD CHANGE JOB CARD "CONF File"')
