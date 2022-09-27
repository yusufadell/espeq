import time
from functools import wraps

from .queue import Queue
from .serializer import serialize


class Task:
    __slots__ = [
        "name",
        "fn",
        "espeq",
        "queue",
    ]

    def __init__(self, fn=None, espeq=None, queue=None):
        self.name = fn.__name__
        self.espeq = espeq
        if queue:
            self.queue = self._create_queue(queue)
        else:
            self.queue = None

        @wraps(fn)
        def inner(*args, **kwargs):
            return fn(*args, **kwargs)

        self.fn = inner
        inner.delay = self._delay

    def _delay(self, *args, **kwargs):
        queue = kwargs.pop("queue", None) or self.queue
        eta = kwargs.pop("eta", None)
        self._enqueue_with_eta(args, kwargs, queue, eta)

    def _enqueue_with_eta(self, args, kwargs, queue, eta):
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
