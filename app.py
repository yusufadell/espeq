import sys
from pathlib import Path

_ = Path(__name__).resolve().parent
sys.path.append(_)

from espeq import EspeQ

espeq = EspeQ(
    queues=[
        (0, "high-priority-queue"),
        (1, "medium-priority-queue"),
        (2, "low-priority-queue"),
    ],
)


@espeq.task(queue="medium-priority-queue")
def mytask(x, y):
    print(x + y)


if __name__ == "__main__":
    # add 1 plus 1 on a worker somewhere, overwriting the default queue from medium to high priority
    mytask.delay(1, 1, queue="hight-priority-queue")
