import logging
import os
import time
from dataclasses import dataclass
from queue import Queue

import daemon

from .serializer import deserialize, serialize

logger = logging.Logger(__name__)

ZRANGEPOP = """
local results = redis.call('ZRANGEBYSCORE', KEYS[1], 0, ARGV[1])
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, ARGV[1])
return results
"""
from typing import Any


@dataclass
class Worker:
    espeq: Any = None
    concurrency: int = 1
    exclude_queues: str = ""
    foreground: bool = False

    def __init__(self):
        if self.foreground:
            self._run()

        with daemon.DaemonContext():
            self._run()

    def _run(self):
        is_parent = True
        for i in range(self.concurrency):
            pid = os.fork()
            if pid == 0:  # child
                is_parent = False
                while True:
                    self._enqueue_ready_eta_tasks()
                    self._execute_next_task_from_queue()

        if is_parent:
            while True:
                time.sleep(10)

    def _enqueue_ready_eta_tasks(self):
        script = self.espeq.broker.register_script(ZRANGEPOP)
        results = script(keys=[self.espeq.eta_task_key], args=[int(round(time.time()))])
        for payload in results:
            payload = deserialize(payload)
            queue = payload.pop("queue")
            queue = Queue.create(queue, queues_by_name=self.espeq.queues_by_name)
            payload = serialize(payload)
            self.espeq.broker.lpush(queue.broker_key, payload)

    def _execute_next_task_from_queue(self):
        queues = [x.broker_key for x in self.espeq.queues]
        print("Checking for tasks...")
        payload = self.espeq.broker.blpop(queues, self.espeq.wait_timeout)
        if payload is not None:
            queue, payload = payload
            payload = deserialize(payload)
            print(f"got task: {payload}")
            task = self.espeq.tasks[payload["name"]]
            task.fn(*payload["args"], **payload["kwargs"])
