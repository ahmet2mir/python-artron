======================
Use with CLI
======================

Use click
---------

Artron could be combined with the awesome click_.

.. _click: https://github.com/pallets/click

.. code-block:: python

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

.. code-block:: console

    $ python examples/basic_cli.py list
    - task-id-1
    - task-id-3
    - task-id-2
    - task-id-5
    - task-id-4
    - task-id-6

See full example under `examples/basic_cli.py <https://github.com/ahmet2mir/python-artron/tree/master/examples/basic_cli.py>`_.


Use docopt
----------

docopt seems to be a dead project so I don't use it anymore.
