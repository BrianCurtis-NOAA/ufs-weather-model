import re
import os
import glob
import yaml


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

        self.number = number
        self.conf_line = conf_line
        splitline = self.conf_line.split('|')
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

    def add_task(self, rt_task):
        self.task_list.append(rt_task)

    def save_to_file(self):
        with open(f'./pr/{self.compile_dict["number"]/}', 'w') as file:
            yaml.dump(self.compile_dict, file)


class Rt_task:
    '''
    This function takes a RUN line from rt.conf and creates a Rt_task object
    '''

    def __init__(self, compile, conf_line):
        self.compile = compile
        self.conf_line = conf_line

        splitline = self.conf_line.split('|')
        self.name = splitline[1].strip()
        if compile.repro:
            self.name += '_repro'

        self.fv3 = splitline[3].strip()
        self.dependency = splitline[4].strip()
        self.status = None
        compile.add_task(self)

    def __repr__(self):
        return 'Rt_task()'

    def __str__(self):
        myret = f'Compile: {self.compile}\n'
        myret += f'Conf Line: {self.conf_line}'
        myret += f'Name: {self.name}\n'
        myret += f'Dependency: {self.dependency}\n'
        myret += f'FV3: {self.fv3}\n'
        myret += f'Status: {self.status}\n'

        return myret


def setup_env():
    hostname = os.getenv('HOSTNAME')
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
        compilers = ['gnu']
    else:
        raise KeyError(f'Hostname: {hostname} does not match '
                       'for a supported system. Exiting.')
    return machine, compilers


def process_rt_conf(machine, compiler):
    compile_num = 1
    compile_list = []
    if compiler == 'intel':
        rt_conf_filename = 'rt.conf'
    else:
        rt_conf_filename = f'rt_{compiler}.conf'
    with open(f'../{rt_conf_filename}') as f:
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
                            break
            except (FileNotFoundError, IndexError):
                task.status = 'Failed'
            if task.status == 'Failed':
                failure = True

    return failure


def main():
    machine, compilers = setup_env()
    compiler = 'intel'
    compiles = process_rt_conf(machine, compiler)
    failure = update_status(compiles, machine)
    if failure:
        write_new_conf(compiles)
        print('===========\nHERE IS WHERE I WOULD CHANGE JOB CARD "CONF File"')


if __name__ == '__main__':
    main()
