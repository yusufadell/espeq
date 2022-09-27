from importlib import import_module


def import_app(app):
    module_path, class_name = app.rsplit(
        sep=".", maxsplit=1
    )  # math.sin => ['math', 'sin']
    module = import_module(module_path)  # eq to import math
    espeq = getattr(module, class_name)
    return espeq  # callable from module, it could be a function like sin()


def inspect(app):
    queues = {}
    for queue in app.queues:
        queues[queue.name] = {
            "name": queue.name,
            "priority": queue.priority,
            "broker_key": queue.broker_key,
            "broker_eta_key": queue.broker_eta_key,
            "pending_tasks": num_pending_tasks_in_queue(app, queue),
            "pending_eta_tasks": num_pending_eta_tasks_in_queue(app, queue),
        }
    return {
        "queues": queues,
    }


def num_pending_tasks_in_queue(app, queue=None, queue_name: str = None) -> int:
    queue = _handle_queue(app, queue, queue_name)
    return app.broker.llen(queue.broker_key)


def num_pending_eta_tasks_in_queue(app, queue=None, queue_name: str = None) -> int:
    queue = _handle_queue(queue, queue_name)
    return app.broker.zcount(queue.broker_eta_key, "-inf", "+inf")


def _handle_queue(app, queue, queue_name):
    if not queue:
        if queue_name is None:
            return 0
        queue = app.queues_by_name.get(queue_name)
        if not queue:
            return 0
        return queue
