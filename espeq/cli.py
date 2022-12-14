"""Console script for espeq."""
import json
import sys

import click

from espeq.utils import import_app
from espeq.worker import Worker

from . import utils
from .scheduler import Scheduler


@click.command()
def main(args=None):
    """Console script for espeq."""
    click.echo("Replace this message by putting your code into " "espeq.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


@click.command()
@click.option("--app", required=True, help="Import path of the EspeQ instance.")
def worker(**options):
    """Run worker(s) to process tasks from queue(s) defined in your app."""
    espeq = import_app(options.pop("app"))
    worker = Worker(espeq=espeq)
    worker.start()


@click.command()
@click.option("--app", required=True, help="Import path of the EspeQ instance.")
def info(**options):
    """Inspect and print info about your queues."""
    espeq = import_app(options.pop("app"))
    _info = utils.inspect(espeq)
    json_formatted_str = json.dumps(_info, indent=2, sort_keys=True)
    click.echo(json_formatted_str)


@click.command()
@click.option("--app", required=True, help="Import path of the espeq instance.")
@click.option(
    "--foreground",
    is_flag=True,
    help="Run in foreground; Default is to run as daemon in background.",
)
def scheduler(**options):
    """Run a scheduler to enqueue periodic tasks based on a schedule defined in your app."""
    espeq = import_app(options.pop("app"))
    result = Scheduler(espeq=espeq, **options)
    if result:
        click.fail(result)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
