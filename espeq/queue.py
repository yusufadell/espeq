# -*- coding: utf-8 -*-


class Queue:
    __slots__ = [
        "name",
        "priority",
        "prefix",
    ]

    def __init__(self, name=None, priority=0, prefix="EspeQ"):
        self.name = name
        self.prefix = prefix

        try:
            self.priority = int(priority)
        except:
            raise Exception(f"Invalid queue priority: {priority}")

    @classmethod
    def create(cls, obj, queues_by_name=None):
        if queues_by_name is not None:
            if isinstance(obj, cls):
                cls._handle_class_obj(obj, queues_by_name)

            elif cls.valid_sequence_type(obj):
                cls._handle_sequence_type_obj(obj, queues_by_name)

            # elif obj not in queues_by_name:
            #     raise Exception(f"Unknown queue: {obj}")

        return cls(name=obj)

    @classmethod
    def _handle_class_obj(cls, obj, queues_by_name):
        if obj.name not in queues_by_name:
            raise Exception(f"Unknown queue: {obj.name}")
        return obj

    @classmethod
    def valid_sequence_type(cls, obj):
        return isinstance(obj, (list, tuple)) and len(obj) == 2

    @classmethod
    def _handle_sequence_type_obj(cls, obj, queues_by_name):
        _priority, _name = obj[1], obj[0]
        if isinstance(obj[0], int):
            _priority, _name = obj[0], obj[1]
        if _name not in queues_by_name:
            raise Exception(f"Unknown queue: {_name}")
        return cls(priority=_priority, name=_name)

    @property
    def broker_key(self):
        return f"{self.prefix}:{self.name}"

    @property
    def broker_eta_key(self):
        return f"{self.prefix}:eta:{self.name}"
