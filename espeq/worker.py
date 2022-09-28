import logging
import os
import signal
import time
from dataclasses import dataclass, field
from queue import Queue

import daemon

from .serializer import deserialize, serialize

logger = logging.Logger(__name__)

ZRANGEPOP = """
local results = redis.call('ZRANGEBYSCORE', KEYS[1], 0, ARGV[1])
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, ARGV[1])
return results
"""
from typing import List, TypeVar

_T = TypeVar("_T")


@dataclass
class Worker:
    __slots__ = [
        "espeq",
        "children",
    ]
    espeq: _T = None
    concurrency: int = 1
    exclude_queues: str = ""
    foreground: bool = False
    children: List = field(default_factory=list)

    def __init__(self, espeq=None):
        self.espeq = espeq

    def start(self, foreground=False):
        self.children = []

        if foreground:
            self._run()
            return

        with daemon.DaemonContext():
            self._run()

    def _run(self):
        pid = None
        for _ in range(self.espeq.concurrency):
            pid = self._fork()

        if pid != 0:  # parent
            self._parent()

    def _parent(self):
        signal.signal(signal.SIGCHLD, self._on_child_exit)
        self.wakaq.broker.close()
        pubsub = self.wakaq.broker.pubsub()
        pubsub.subscribe(self.wakaq.broadcast_key)
        while True:
            msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=10)
            if msg:
                queue_broker_key, payload = self._handle_pub_message(msg)
                self.wakaq.broker.lpush(queue_broker_key, payload)

    def _handle_pub_message(self, msg):
        payload = deserialize(msg["data"])
        queue = Queue.create(
            payload.pop("queue"), queues_by_name=self.wakaq.queues_by_name
        )
        payload = serialize(payload)
        return queue.broker_key, payload

    def _child(self):
        # ignore ctrl-c sent to process group from terminal
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # redis should eventually detect pid change and reset, but we force it
        self.espeq.broker.connection_pool.reset()

        while True:
            self._enqueue_ready_eta_tasks()
            self._execute_next_task_from_queue()

    def _fork(self) -> int:
        pid = os.fork()
        if pid == 0:
            self._child()
        else:
            self.children.append(pid)
        return pid

    def _on_child_exit(self, signum, frame):
        for child in self.children:
            try:
                pid, _ = os.waitpid(child, os.WNOHANG)
                if pid != 0:  # child exited
                    self.children.remove(child)
            except InterruptedError:  # child exited while calling os.waitpid
                self.children.remove(child)
            except ChildProcessError:  # child pid no longer valid
                self.children.remove(child)
        self._refork_missing_children()

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
