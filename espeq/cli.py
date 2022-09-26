"""Console script for espeq."""
import sys

import click

from .utils import import_app
from .worker import Worker


@click.command()
def main(args=None):
    """Console script for espeq."""
    click.echo("Replace this message by putting your code into " "espeq.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


@click.command()
@click.option("--app", required=True, help="Import path of the EspeQ instance.")
@click.option(
    "--concurrency", type=click.INT, default=1, help="Number of worker processes."
)
@click.option(
    "--exclude-queues",
    default="",
    help="Comma separated list of queue names to not process.",
)
@click.option(
    "--foreground",
    is_flag=True,
    help="Run in foreground; Default is to run as daemon in background.",
)
def worker(**options):
    """Run worker(s) to process tasks from queue(s) defined in your app."""
    try:
        options["exclude_queues"] = [
            x.strip().lower() for x in options["exclude_queues"].split(",")
        ]
    except:
        click.fail(
            f'Invalid value for exclude_queues. Must be a list of queue names separated by periods: {options["exclude_queues"]}'
        )

    espeq = import_app(options.pop("app"))
    Worker(espeq=espeq, **options)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
