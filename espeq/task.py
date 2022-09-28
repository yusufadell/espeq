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
        inner.broadcast = self.broadcast

    def _delay(self, *args, **kwargs):
        """Run task in the background."""

        queue = kwargs.pop("queue", self.queue)
        eta = kwargs.pop("eta", None)
        self._enqueue_with_eta(args, kwargs, queue, eta)

    def _enqueue_with_eta(self, args, kwargs, queue, eta):
        queue_name, queue_broker_key = self._validate_queue(queue)

        payload = {
            "name": self.name,
            "queue": queue_name,
            "args": args,
            "kwargs": kwargs,
        }
        payload = serialize(payload)
        if eta:
            self.espeq.broker.zadd(
                self.espeq.eta_task_key, {payload: time.time()}, nx=True
            )

        self.espeq.broker.rpush(queue_broker_key, payload)

    def broadcast(self, *args, **kwargs) -> int:
        """Run task in the background on all workers.

        Only runs the task once per worker parent daemon, no matter the worker's concurrency.

        Returns the number of workers the task was sent to.
        """

        queue = kwargs.pop("queue", None)

        payload = {
            "name": self.name,
            "queue": queue.name,
            "args": args,
            "kwargs": kwargs,
        }
        payload = serialize(payload)
        return self.wakaq.broker.publish(self.wakaq.broadcast_key, payload)

    def _create_queue(self, queue):
        return Queue.create(queue, queues_by_name=self.espeq.queues_by_name)

    def _validate_queue(self, queue):
        if queue:
            queue = self._create_queue(queue)
        else:
            if self.queue:
                queue = self.queue
            else:
                queue = self.espeq.queues[-1]
        return queue.name, queue.broker_key
