from dataclasses import dataclass, field
from typing import Any, List

from .serializer import serialize


@dataclass
class CronTask:
    schedule: List = field(default_factory=list)
    task_name: str = None
    queue_name: str = None
    args: str = None
    kwargs: str = None
    payload: serialize = serialize(
        {
            "name": task_name,
            "args": args,
            "kwargs": kwargs,
        }
    )

    @classmethod
    def create(cls):
        ...


@dataclass
class Scheduler:
    espeq: Any = None
    schedules: List = field(default_factory=list)

    def _run(self):
        ...
