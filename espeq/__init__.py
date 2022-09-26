"""Top-level package for EspeQ."""

__author__ = """Yusuf Adel"""
__email__ = "yusufadell.dev@gmail.com"
__version__ = "0.1.0"

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


class WakaQ:
    queues = []
    queues_by_name = {}
    tasks = {}
    eta_task_key = "wakaq-eta"
    schedules = []
    wait_timeout = None
    broker = None

    def __init__(
        self,
        queues=[],
        schedules=[],
        host="localhost",
        port=6379,
        socket_timeout=15,
        socket_connect_timeout=15,
        health_check_interval=30,
        wait_timeout=10,
    ):
        self.queues = [Queue.create(x) for x in queues]
        self.queues.sort(key=lambda q: q.priority)
        self.queues_by_name = dict([(x.name, x) for x in self.queues])
        self.schedules = [CronTask.create(x) for x in schedules]
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

    def task(self, func, queue=None):
        t = Task(func=func, espeq=self, queue=queue)
        if t.name in self.tasks:
            raise Exception(f"Duplicate task name: {t.name}")
        self.tasks[t.name] = t
        return t.func
