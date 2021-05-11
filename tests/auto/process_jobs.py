import re
import os
import glob


class Rt_compile:

    def __init__(self, number, conf_line):
        self.number = number
        self.conf_line = conf_line
        splitline = self.conf_line.split('|')
        infos = splitline[1].split(' ')
        self.bit32 = False
        self.debug = False
        self.repro = False
        self.multigases = False
        for info in infos:
            info_split = info.split('=')
            if info_split[0].strip() == 'APP':
                self.app = info_split[1]
            elif info_split[0].strip() == '32BIT':
                self.bit32 = True
            elif info_split[0].strip() == 'DEBUG':
                self.debug = True
            elif info_split[0].strip() == 'SUITES':
                self.suites = info_split[1].split(',')
            elif info_split[0].strip() == 'REPRO':
                self.repro = True
            elif info_split[0].strip() == 'MULTI_GASES':
                self.multigases = True
        self.fv3 = splitline[3].strip()
        self.status = None
        self.task_list = []

    def __repr__(self):
        return 'Rt_compile()'

    def __str__(self):
        myret = f'Compile: {self.number}\n'
        myret += f'App: {self.app}\n'
        myret += f'Debug: {self.debug}\n'
        myret += f'32BIT: {self.bit32}\n'
        myret += f'Suites: {self.suites}\n'
        myret += f'Repro: {self.repro}\n'
        myret += f'Multigases: {self.multigases}\n'
        myret += f'FV3: {self.fv3}\n'
        myret += f'Status: {self.status}\n'
        myret += f'Conf Line: {self.conf_line}\n'
        myret += 'Tasks:\n'
        for task in self.task_list:
            myret += f'--{task.number:03d}_{task.name}\n'

        return myret

    def add_task(self, rt_task):
        self.task_list.append(rt_task)


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
        self.dependency = splitline[4]
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
            print(f'Found Match {match}')
            return match

    return None


def write_new_conf(compiles):
    new_conf_file = 'rt_test.conf'
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
                            f.write(thistask.conf_line)
                        f.write(task.conf_line)


def update_status(compiles, machine):
    failure = False
    for compile in compiles:
        with open(f'../log_{machine}.intel/compile_'
                  f'{compile.number:03d}.log') as f:
            for line in f:
                if 'compile is COMPLETED' in line:
                    compile.status = 'Completed'
                    break
            compile.status = 'Failed'
        if compile.status == 'Failed':
            print('Found a failed Compile')
            failure = True
            for task in compile.task_list:
                task.status = 'Failed'
        else:
            for task in compile.task_list:
                with open(glob.glob(f'../log_{machine}.intel/run_*_'
                          f'{task.name}.log')) as f:
                    for line in f:
                        if 'PASS' in line:
                            task.status = 'Completed'
                            break
                    task.status = 'Failed'
                if task.status == 'Failed':
                    print('Found a failed task')
                    failure = True
    if failure:
        write_new_conf(compiles)
        print('===========\nHERE IS WHERE I WOULD CHANGE JOB CARD "CONF File"')
    return failure


def main():
    machine, compilers = setup_env()
    compiler = 'intel'
    compiles = process_rt_conf(machine, compiler)
    failure = update_status(compiles, machine)
    print(f'Failure?: {failure}')


if __name__ == '__main__':
    main()
