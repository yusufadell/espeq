import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, List

from espeq import EspeQ

from .queue import Queue


@dataclass
class Task:
    func: Any = None
    name: str = func.__name__
    espeq: EspeQ = None
    queue: List[Queue] = field(default_factory=list)

    def _create_queue(self, queue):
        return Queue.create(queue, queues_by_name=self.espeq.queues_by_name)
