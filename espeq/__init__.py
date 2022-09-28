"""Top-level package for EspeQ."""

__author__ = """Yusuf Adel"""
__email__ = "yusufadell.dev@gmail.com"
__version__ = "0.1.0"

import multiprocessing

import redis

from .cli import worker
from .queue import Queue
from .scheduler import CronTask
from .task import Task

__all__ = [
    "EspeQ",
    "worker",
    "scheduler",
]


class EspeQ:
    queues = []
    schedules = []
    queues_by_name = {}
    tasks = {}
    eta_task_key = "espeq-eta"
    concurrency = 0
    exclude_queues = []

    def __init__(
        self,
        queues=[],
        schedules=[],
        host="localhost",
        port=6379,
        socket_timeout=15,
        concurrency=0,
        exclude_queues=[],
        socket_connect_timeout=15,
        health_check_interval=30,
        wait_timeout=10,
    ):
        self.queues = [Queue.create(queue) for queue in queues]
        self.priority_sort()
        self.queues_by_name = {queue.name: queue for queue in self.queues}
        self.schedules = [CronTask.create(schedule) for schedule in schedules]
        self.concurrency = abs(int(concurrency)) or multiprocessing.cpu_count()
        self.exclude_queues = self._validate_queue_names(exclude_queues)

        self.wait_timeout = wait_timeout
        self.broker = redis.Redis(
            host=host,
            port=port,
            charset="utf-8",
            decode_responses=True,
            health_check_interval=health_check_interval,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
        )

    def priority_sort(self):
        self.queues.sort(key=lambda q: q.priority)

    def task(self, fn=None, queue=None):
        def _task(f):
            t = Task(
                fn=f,
                espeq=self,
                queue=queue,
            )
            if t.name in self.tasks:
                raise Exception(f"Duplicate task name: {t.name}")
            self.tasks[t.name] = t
            return t.fn

        return _task(fn) if fn else _task

    def _validate_queue_names(self, queue_names: list) -> list:
        try:
            queue_names = [x for x in queue_names]
        except:
            return []
        for queue_name in queue_names:
            if queue_name not in self.queues_by_name:
                raise Exception(f"Invalid queue: {queue_name}")
        return queue_names
