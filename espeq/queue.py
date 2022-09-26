from dataclasses import dataclass


@dataclass
class Queue:
    name: str = "espeq"
    priority: int = 0
    prefix: str = ""

    @classmethod
    def create(cls):
        ...

    def broker_key(self):
        return f"{self.prefix}:{self.name}"
