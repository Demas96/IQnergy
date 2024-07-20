import multiprocessing
import os
import signal
import time


class NoLimitError(Exception):
    def __str__(self):
        return ('Не задано ограничение количества процессов. '
                'Используйте .set_max_proc(n)"')


class ProcessController:

    def __init__(self):
        self.wait_tasks = None
        self.output_p = None
        self.input_p = None
        self.main_proc = None
        self.max_exec_time = None
        self.tasks = None
        self.processes = []
        self.n = None

    def set_max_proc(self, n):
        self.n = n

    def send_data(self, conn):
        data = {'wait_tasks': self.wait_tasks,
                'alive_tasks': len(self.processes)}
        conn.send(data)

    def worker(self, conn):
        start_tm = time.time()  # Время запуска очереди
        num_proc = 0  # Позиция задачи в очереди
        count_proc = self.n
        free = len(self.tasks) <= self.n  # Флаг отсутствия очереди
        self.wait_tasks = len(self.tasks)
        while True:
            for item in range(num_proc, len(self.tasks)):  # Первый запуск задач
                func = self.tasks[item]
                if count_proc > 0 and func[0] not in multiprocessing.active_children():
                    proc = multiprocessing.Process(target=func[0], args=(func[1][0], func[1][1]), name=func[0].__name__)
                    self.processes.append([proc, time.time(), 'run'])
                    proc.start()
                    print(proc.name, 'start', round(time.time() - start_tm, 3), 'sec')
                    count_proc -= 1
                    num_proc += 1 if num_proc < len(self.tasks) else 0
                    self.wait_tasks -= 1
                    self.send_data(conn)

            for proc in self.processes:  # Обработка запущеных задач
                if proc[0] not in multiprocessing.active_children():  # Проверка на завершенность задачи
                    self.processes.remove(proc)
                    count_proc += 1
                    free = len(self.processes) <= self.n
                    print(proc[0].name, 'done', round(time.time() - start_tm, 3), 'sec')
                    self.send_data(conn)
                elif count_proc > 0 and proc[2] == 'pause':  # Запуск задачи
                    os.kill(proc[0].pid, signal.SIGCONT)
                    proc[1], proc[2] = time.time(), 'run'
                    count_proc -= 1
                    print(proc[0].name, 'run', round(time.time() - start_tm, 3), 'sec')
                    self.send_data(conn)
                elif time.time() - proc[1] > self.max_exec_time and proc[2] == 'run' and free is False:  # Пауза
                    os.kill(proc[0].pid, signal.SIGSTOP)
                    proc[1], proc[2] = time.time(), 'pause'
                    count_proc += 1
                    print(proc[0].name, 'pause', round(time.time() - start_tm, 3), 'sec')
                    self.send_data(conn)
            if len(self.processes) == 0:  # Проверка на выполнение всех задач
                return False

    def start(self, tasks, max_exec_time):
        if self.n is None:
            raise NoLimitError  # Если не задали ограничение процессов
        self.tasks = tasks
        self.max_exec_time = max_exec_time
        self.output_p, self.input_p = multiprocessing.Pipe()
        self.main_proc = multiprocessing.Process(target=self.worker, args=(self.input_p,))
        self.main_proc.start()

    def wait(self):
        self.main_proc.join()

    def wait_count(self):
        wait_tasks = self.output_p.recv()['wait_tasks']
        return wait_tasks

    def alive_count(self):
        alive_tasks = self.output_p.recv()['alive_tasks']
        return alive_tasks


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


if __name__ == "__main__":
    x, y = 10, 2
    tasks = [(f1, (x, y)), (f2, (x, y)), (f3, (x, y)), (f4, (x, y))]
    start_time = time.time()
    p = ProcessController()
    p.set_max_proc(2)
    p.start(tasks, 1)
    print(f'Ожидают запуска {p.wait_count()} задач')
    print(f'Запущено {p.alive_count()} задач')
    p.wait()
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 3)
    print(f'Выполнено за {elapsed_time} секунд')
