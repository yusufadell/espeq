import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, List

from espeq import EspeQ

from .queue import Queue
from .serializer import serialize


@dataclass
class Task:
    func: Any = None
    name: str = func.__name__
    espeq: EspeQ = None
    queue: List[Queue] = field(default_factory=list)

    def __init__(self, queue=None):

        if queue is not None:
            self.queue = self._create_queue(queue)

        @wraps(self.fn)
        def inner(*args, **kwargs):
            return self.fn(*args, **kwargs)

        inner.delay = self.delay
        self.fn = inner

    def delay(self, *args, **kwargs):
        queue = kwargs.pop("queue", None)
        eta = kwargs.pop("eta", None)
        if queue:
            queue = self._create_queue(queue)
        else:
            if self.queue:
                queue = self.queue
            else:
                queue = self.espeq.queues[-1]

        payload = {
            "name": self.name,
            "args": args,
            "kwargs": kwargs,
            "queue": queue.name if eta else None,
        }
        payload = serialize(payload)
        if eta:
            self.espeq.broker.zadd(
                self.espeq.eta_task_key, {payload: time.time()}, nx=True
            )

        self.espeq.broker.rpush(queue.broker_key, payload)

    def _create_queue(self, queue):
        return Queue.create(queue, queues_by_name=self.espeq.queues_by_name)
