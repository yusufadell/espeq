from dataclasses import dataclass

from espeq import EspeQ


@dataclass
class Worker:
    espeq: EspeQ = None
    concurrency: int = 1
    exclude_queues: str = ""
    foreground: bool = False

    def _run(self):
        ...
