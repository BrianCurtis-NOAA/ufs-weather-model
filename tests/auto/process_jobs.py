class Rt_compile:

    def __init__(self, number, app, debug=False, bit32=False, suites=None,
                 machine_skip=None, machine_only=None):
        self.number = number
        self.app = app
        self.debug = debug
        self.bit32 = bit32
        self.suites = suites
        self.status = None
        self.machine_skip = machine_skip
        self.machine_only = machine_only
        self.task_list = []

    def add_task(self, rt_task):
        self.task_list.append(rt_task)


class Rt_task:

    def __init__(self, compile, name, dependency=None, machine_skip=None,
                 machine_only=None):
        self.compile = compile
        self.name = name
        self.dependency = dependency
        self.status = None
        self.machine_skip = machine_skip
        self.machine_only = machine_only


def process_rt_conf():
    compile_num = 1
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
                if machine_info[0] == '-':
                    machine_skip = machine_info[1:]
                elif machine_info[0] == '+':
                    machine_only = machine_info[1:]
                else:
                    machine_skip = None
                    machine_only = None
                compile_list.append(Rt_compile(compile_num, app, debug, bit32,
                                    suites, machine_skip, machine_only))
                compile_num = compile_num + 1
            elif splitline[0].strip() == 'RUN':
                compile = compile_list[-1]
                name = splitline[1].strip()
                machine_info = splitline[2].split(' ')
                if machine_info[0] == '-':
                    machine_skip = machine_info[1:]
                elif machine_info[0] == '+':
                    machine_only = machine_info[1:]
                else:
                    machine_skip = None
                    machine_only = None
                dependency = splitline[-1]
                print(type(Rt_task(compile, name, dependency, machine_skip,
                                  machine_only)))
                compile_list[-1].add_task(Rt_task(compile, name, dependency,
                                          machine_skip, machine_only))
    return compile_list
