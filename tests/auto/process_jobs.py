import re
import os


class Rt_compile:

    def __init__(self, number, app, debug=False, bit32=False, fv3=None,
                 suites=None):
        self.number = number
        self.app = app
        self.debug = debug
        self.bit32 = bit32
        self.suites = suites
        self.fv3 = fv3
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
        myret += f'FV3: {self.fv3}\n'
        myret += f'Status: {self.status}\n'
        myret += 'Tasks:\n'
        for task in self.task_list:
            myret += f'--{task.number:03d}_{task.name}\n'

        return myret

    def add_task(self, rt_task):
        self.task_list.append(rt_task)


class Rt_task:

    def __init__(self, number, compile, name, fv3=None, dependency=None):
        self.number = number
        self.compile = compile
        self.name = name
        self.fv3 = fv3
        self.dependency = dependency
        self.status = None

    def __repr__(self):
        return 'Rt_task()'

    def __str__(self):
        myret = f'Number: {self.number}\n'
        myret += f'Compile: {self.compile}\n'
        myret += f'Name: {self.name}\n'
        myret += f'Dependency: {self.dependency}\n'
        myret += f'FV3: {self.fv3}\n'
        myret += f'Status: {self.status}\n'

        return myret


def check_for_completed():
    "'compile is COMPLETED' for compiles"
    "'PASS' for run"
    pass


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


def process_rt_conf(machine):
    compile_num = 1
    task_num = 1
    compile_list = []
    with open('../rt.conf') as f:
        for line in f:
            splitline = line.split('|')
            if splitline[0].strip() == 'COMPILE':
                infos = splitline[1].split(' ')
                for info in infos:
                    bit32 = False
                    debug = False
                    suites = None
                    info_split = info.split('=')
                    if info_split[0] == 'APP':
                        app = info_split[1]
                    elif info_split[0] == '32BIT':
                        bit32 = True
                    elif info_split[0] == 'DEBUG':
                        debug = True
                    elif info_split[0] == 'SUITES':
                        suites = info_split[1].split(',')
                machine_info = splitline[2].split(' ')
                if ('-' in machine_info
                   and f'{machine}.intel' in machine_info):
                    continue
                elif ('+' in machine_info
                      and f'{machine}.intel' not in machine_info):
                    continue
                fv3 = splitline[3].strip()
                compile_list.append(Rt_compile(compile_num, app, debug, bit32,
                                    fv3, suites))
                compile_num = compile_num + 1
            elif splitline[0].strip() == 'RUN':
                compile = compile_list[-1]
                name = splitline[1].strip()
                machine_info = splitline[2].split(' ')
                if ('-' in machine_info
                   and f'{machine}.intel' in machine_info):
                    continue
                elif ('+' in machine_info
                      and f'{machine}.intel' not in machine_info):
                    continue
                fv3 = splitline[3].strip()
                if len(splitline) >= 5:
                    dependency = splitline[4]
                compile_list[-1].add_task(Rt_task(task_num, compile, name, fv3,
                                                  dependency))
                task_num = task_num+1
    return compile_list


def main():
    machine, compilers = setup_env()
    compiles = process_rt_conf(machine)
    for compile in compiles:
        print(compile)


if __name__ == '__main__':
    main()
