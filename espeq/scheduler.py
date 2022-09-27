import logging
from dataclasses import dataclass, field
from typing import List, Tuple

from .serializer import serialize

log = logging.getLogger("espeq")


@dataclass
class CronTask:
    schedule: List | Tuple = field(default_factory=(list, tuple))
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
    def create(cls, obj, queues_by_name=None):
        if isinstance(obj, cls):
            if (
                queues_by_name is not None
                and obj.queue
                and obj.queue not in queues_by_name
            ):
                log.error(f"Unknown queue: {obj.queue}")
                raise Exception(f"Unknown queue: {obj.queue}")
            return obj
        elif isinstance(obj, (list, tuple)) and len(obj) == 2:
            return cls(schedule=obj[0], task_name=obj[1])
        elif isinstance(obj, (list, tuple)) and len(obj) == 4:
            return cls(schedule=obj[0], task_name=obj[1], args=obj[2], kwargs=obj[3])
        else:
            log.error(f"Invalid schedule: {obj}")
            raise Exception(f"Invalid schedule: {obj}")

    @property
    def payload(self):
        return serialize(
            {
                "name": self.task_name,
                "args": self.args if self.args is not None else [],
                "kwargs": self.kwargs if self.kwargs is not None else {},
            }
        )
