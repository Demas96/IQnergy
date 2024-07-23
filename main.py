import multiprocessing
import time


class NoLimitError(Exception):
    def __str__(self):
        return ('Не задано ограничение количества процессов. '
                'Используйте .set_max_proc(n)"')


class ProcessController:

    def __init__(self):
        self.wait_tasks = 0
        self.input_task = None
        self.output_task = None
        self.input_stat = None
        self.output_stat = None
        self.data = {'wait_tasks': 0, 'alive_tasks': 0}
        self.main_proc = None
        self.max_exec_time = None
        self.tasks = []
        self.processes = []
        self.n = None

    def set_max_proc(self, n):
        self.n = n

    def send_data(self, inp):
        data = {'wait_tasks': self.wait_tasks,
                'alive_tasks': len(self.processes)}
        inp.send(data)

    def worker(self, input_stat, output_task):
        num_proc = 0
        count_proc = self.n
        self.wait_tasks = len(self.tasks)
        self.tasks[:] = [[task, self.max_exec_time] for task in self.tasks]
        start_tm = time.time()  # Время запуска очереди
        while True:
            for item in range(num_proc, len(self.tasks)):  # Первый запуск задач
                task = self.tasks[item][0]
                max_exec_time = self.tasks[item][1]
                if num_proc < len(self.tasks) and count_proc > 0 and task[0] not in multiprocessing.active_children():
                    proc = multiprocessing.Process(target=task[0], args=(task[1][0], task[1][1]), name=task[0].__name__)
                    self.processes.append([proc, time.time(), max_exec_time])
                    proc.start()
                    num_proc += 1
                    print(proc.name, 'start', round(time.time() - start_tm, 3), 'sec')
                    count_proc -= 1
                    self.wait_tasks -= 1
                    self.send_data(input_stat)

            for proc in self.processes:  # Обработка запущеных задач
                process, working_time, max_exec_time = proc
                if process not in multiprocessing.active_children():  # Проверка на завершенность задачи
                    self.processes.remove(proc)
                    count_proc += 1
                    print(proc[0].name, 'done', round(time.time() - start_tm, 3), 'sec')
                    self.send_data(input_stat)
                elif time.time() - working_time > max_exec_time:  # Остановка процесса по таймауту
                    process.terminate()
                    self.processes.remove(proc)
                    count_proc += 1
                    print(process.name, 'is terminated', round(time.time() - start_tm, 3), 'sec')
                    self.send_data(input_stat)

            if output_task.poll():
                new_task, max_exec_time = output_task.recv()
                tasks = [[task, max_exec_time] for task in new_task]
                self.tasks += tasks
                self.wait_tasks += len(tasks)

            if len(self.processes) == 0 and num_proc == len(self.tasks):  # Проверка на выполнение всех задач
                return False

    def start(self, tasks, max_exec_time):
        if self.n is None:
            raise NoLimitError  # Если не задали ограничение процессов
        if len(multiprocessing.active_children()) == 0:
            self.max_exec_time = max_exec_time
            self.output_stat, self.input_stat = multiprocessing.Pipe()
            self.output_task, self.input_task = multiprocessing.Pipe()
            self.tasks = tasks
            self.main_proc = multiprocessing.Process(target=self.worker, args=(self.input_stat, self.output_task))
            self.main_proc.start()
        else:
            self.input_task.send((tasks, max_exec_time))

    def wait(self):
        self.main_proc.join()

    def recv_data(self):
        while self.output_stat.poll():
            self.data = self.output_stat.recv()

    def wait_count(self):
        self.recv_data()
        return self.data['wait_tasks']

    def alive_count(self):
        self.recv_data()
        return self.data['alive_tasks']


def f1(a, b):
    time.sleep(2)
    return print('f1: ', a + b)


def f2(a, b):
    time.sleep(3)
    return print('f2: ', a - b)


def f3(a, b):
    time.sleep(4)
    return print('f3: ', a * b)


def f4(a, b):
    time.sleep(5)
    return print('f4: ', a / b)


def f5(a, b):
    time.sleep(2)
    return print('f5: ', a + b)


def f6(a, b):
    time.sleep(3)
    return print('f6: ', a - b)


def f7(a, b):
    time.sleep(4)
    return print('f7: ', a * b)


def f8(a, b):
    time.sleep(5)
    return print('f8: ', a / b)


if __name__ == '__main__':

    x, y = 10, 2
    tasks1 = [(f1, (x, y)), (f2, (x, y)), (f3, (x, y)), (f4, (x, y))]
    start_time = time.time()

    p = ProcessController()
    p.set_max_proc(2)
    p.start(tasks1, 4)

    print(f'Ожидают запуска {p.wait_count()} задач')
    print(f'Запущено {p.alive_count()} задач')

    time.sleep(3)
    tasks2 = [(f5, (x, y)), (f6, (x, y)), (f7, (x, y)), (f8, (x, y))]
    p.start(tasks2, 6)
    print(f'Ожидают запуска {p.wait_count()} задач')
    print(f'Запущено {p.alive_count()} задач')

    time.sleep(4)
    print(f'Ожидают запуска {p.wait_count()} задач')
    print(f'Запущено {p.alive_count()} задач')

    time.sleep(2)
    print(f'Ожидают запуска {p.wait_count()} задач')
    print(f'Запущено {p.alive_count()} задач')

    p.wait()
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 3)
    print(f'Выполнено за {elapsed_time} секунд')
