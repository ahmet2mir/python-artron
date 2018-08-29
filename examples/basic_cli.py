# -*- coding: utf-8 -*-
import basic

import click

@click.group()
@click.version_option()
def cli():
    """Artron CLI"""

@cli.command()
def start():
    """Start all tasks."""
    basic.process()

@cli.command()
def list():
    """List tasks."""
    basic.process(False)

if __name__ == '__main__':
    cli()
