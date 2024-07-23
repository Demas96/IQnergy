import multiprocessing
import time


class NoLimitError(Exception):
    def __str__(self):
        return ('Не задано ограничение количества процессов. '
                'Используйте .set_max_proc(n)"')


class ProcessController:

    def __init__(self):
        self.wait_tasks = 0
        self.output_p = None
        self.input_p = None
        self.main_proc = None
        self.max_exec_time = None
        self.tasks = []
        self.processes = []
        self.n = None

    def set_max_proc(self, n):
        self.n = n

    def worker(self, inp, outp):
        num_proc = 0
        count_proc = self.n
        self.wait_tasks = len(self.tasks)
        start_tm = time.time()  # Время запуска очереди
        while True:
            for item in range(num_proc, len(self.tasks)):  # Первый запуск задач
                task = self.tasks[item]
                if num_proc < len(self.tasks) and count_proc > 0 and task[0] not in multiprocessing.active_children():
                    proc = multiprocessing.Process(target=task[0], args=(task[1][0], task[1][1]), name=task[0].__name__)
                    self.processes.append([proc, time.time()])
                    proc.start()
                    num_proc += 1
                    print(proc.name, 'start', round(time.time() - start_tm, 3), 'sec')
                    count_proc -= 1
                    self.wait_tasks -= 1

            for proc in self.processes:  # Обработка запущеных задач
                process, working_time = proc
                if process not in multiprocessing.active_children():  # Проверка на завершенность задачи
                    self.processes.remove(proc)
                    count_proc += 1
                    print(proc[0].name, 'done', round(time.time() - start_tm, 3), 'sec')
                elif time.time() - proc[1] > self.max_exec_time:  # Остановка процесса по таймауту
                    process.terminate()
                    self.processes.remove(proc)
                    count_proc += 1
                    print(proc[0].name, 'is terminated', round(time.time() - start_tm, 3), 'sec')

            if outp.poll():
                op = outp.recv()
                if op == 'wait_tasks':
                    print(f'Ожидают запуска {self.wait_tasks} задач')
                    inp.send(False)
                elif op == 'alive_tasks':
                    print(f'Запущено {len(self.processes)} задач')
                    inp.send(False)
                # не принимает список новых заданий
                elif isinstance(op, list):
                    self.tasks += op
                    self.wait_tasks += len(op)
                    inp.send(False)

            if len(self.processes) == 0 and num_proc == len(self.tasks):  # Проверка на выполнение всех задач
                return False

    def start(self, tasks, max_exec_time):
        if self.n is None:
            raise NoLimitError  # Если не задали ограничение процессов
        if len(multiprocessing.active_children()) == 0:
            self.max_exec_time = max_exec_time
            self.output_p, self.input_p = multiprocessing.Pipe()
            self.tasks = tasks
            self.main_proc = multiprocessing.Process(target=self.worker, args=(self.input_p, self.output_p))
            self.main_proc.start()
        else:
            self.input_p.send(tasks)

    def wait(self):
        self.main_proc.join()

    def wait_count(self):
        self.input_p.send('wait_tasks')

    def alive_count(self):
        self.input_p.send('alive_tasks')


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


if __name__ == "__main__":
    x, y = 10, 2
    tasks1 = [(f1, (x, y)), (f2, (x, y)), (f3, (x, y)), (f4, (x, y))]
    start_time = time.time()

    p = ProcessController()
    p.set_max_proc(2)
    p.start(tasks1, 4)

    p.wait_count()
    p.alive_count()

    time.sleep(3)
    tasks2 = [(f5, (x, y)), (f6, (x, y)), (f7, (x, y)), (f8, (x, y))]
    p.start(tasks2, 4)
    p.wait_count()
    p.alive_count()

    time.sleep(4)
    p.wait_count()
    p.alive_count()

    p.wait()
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 3)
    print(f'Выполнено за {elapsed_time} секунд')
