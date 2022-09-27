import datetime
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Tuple

import daemon

from .serializer import serialize

# from croniter import croniter


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

    def __init__(self):
        if not croniter.is_valid(self.schedule):
            raise Exception(
                f"Invalid cron schedule (min hour dom month dow): {self.schedule}"
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


class Scheduler:
    __slots__ = [
        "wakaq",
        "schedules",
    ]

    def __init__(self, wakaq=None, foreground=False):
        self.wakaq = wakaq

        if len(self.wakaq.schedules) == 0:
            return "No scheduled tasks found."

        self.schedules = []
        for schedule in self.wakaq.schedules:
            self.schedules.append(
                CronTask.create(schedule, queues_by_name=self.wakaq.queues_by_name)
            )

        if foreground:
            self._run()
            return

        with daemon.DaemonContext():
            self._run()

    def _run(self):
        base = datetime.utcnow()
        upcoming_tasks = []

        while True:
            if len(upcoming_tasks) > 0:
                for cron_task in upcoming_tasks:
                    task = self.wakaq.tasks[cron_task.task_name]
                    if cron_task.queue_name:
                        queue = self.wakaq.queues_by_name[cron_task.queue_name]
                    elif task.queue:
                        queue = task.queue
                    else:
                        queue = self.wakaq.queues[-1]
                    self.wakaq.broker.lpush(queue.broker_key, cron_task.payload)

            upcoming_tasks = []
            crons = []
            # crons = [(croniter(x.schedule, base).get_next(datetime), x) for x in self.schedules]
            sleep_until = base + timedelta(days=1)

            for dt, cron_task in crons:
                if dt < sleep_until:
                    sleep_until = dt
                    upcoming_tasks = [cron_task]
                elif self._is_same_minute_precision(dt, sleep_until):
                    upcoming_tasks.append(cron_task)

            base = sleep_until

    def _is_same_minute_precision(self, a, b):
        return a.strftime("%Y%m%d%H%M") == b.strftime("%Y%m%d%H%M")
