# Artron - multiprocess execution helper

![GitHub](https://img.shields.io/github/license/ahmet2mir/python-artron.svg)
[![image](https://img.shields.io/pypi/pyversions/artron.svg)](https://python.org/pypi/artron)
[![Build Status](https://travis-ci.org/ahmet2mir/python-artron.svg?branch=master)](https://travis-ci.org/ahmet2mir/python-artron)

`Artron` is a simple `python` module to use `multiprocessing` with dependency graph and queue management allowing easy tool creation.

[Read the full documentation](https://artron.readthedocs.io/en/latest/) to see everything you can do.

## Installation

pip

    pip install artron

## Simple example

> see examples/basic.py to get the full file

First create an class with all actions needed inside (you could also use a module). `Artron` will use `getattr` on the object or module to run the task.

```python
import time

class Builder(object):
    
    def builder_func_1(self, msg, retry):
        time.sleep(6)
        return "builder_func_1 ==> " + msg

    def builder_func_2(self, msg, retry):
        time.sleep(3)
        return "builder_func_2 ==> " + msg

    def builder_func_3(self, msg, retry):
        time.sleep(1)
        raise Exception("ERROR builder_func_3")
        return "builder_func_3 ==> " + msg

    def builder_func_4(self, msg, retry):
        time.sleep(4)
        return "builder_func_4 ==> " + msg
```

Now use with Artron

```python
import sys
from pprint import pprint
from artron.task import Task
from artron.manager import Manager

def process(run=True):
    # builder to pass to Artron
    builder = Builder()

    # declare manager
    manager = Manager(builder, max_retry=2)

    # declare tasks
    task1 = Task('task-id-1', {'msg': 'task-1-msg'}, 'builder_func_1')
    task2 = Task('task-id-2', {'msg': 'task-2-msg'}, 'builder_func_2')
    task3 = Task('task-id-3', {'msg': 'task-3-msg'}, 'builder_func_3')
    task4 = Task('task-id-4', {'msg': 'task-4-msg'}, 'builder_func_4')
    task5 = Task('task-id-5', {'msg': 'task-5-msg'}, 'builder_func_2')
    task6 = Task('task-id-6', {'msg': 'task-6-msg'}, 'builder_func_4')
    
    # generate dependencies
    task1.add_require(task2.tid)
    task1.add_require(task3.tid)
    task1.add_require(task4.tid)
    task2.add_require(task4.tid)
    task6.add_require(task2.tid)
    task5.add_require(task1.tid)
    
    # add task
    manager.add(task1)
    manager.add(task2)
    manager.add(task3)
    manager.add(task4)
    manager.add(task5)
    manager.add(task6)

    # if we should run
    if run:
        # start
        results = manager.start()
        pprint(results)
        sys.exit(results['exit_code'])
    # otherwise print tasks ids
    else:
        for task in manager.tasks.keys():
            print("-", task)

if __name__ == '__main__':
    process()
```

That's it!

**Result**

```shell
artron: [ERROR] Traceback (most recent call last):
  File "/home/ahmet/workspaces/devs/python-artron/artron/task.py", line 89, in run
    **self.inputs
  File "examples/basic.py", line 19, in builder_func_3
    raise Exception("ERROR builder_func_3")
Exception: ERROR builder_func_3

artron: [ERROR] ERROR builder_func_3
artron: [ERROR] Traceback (most recent call last):
  File "/home/ahmet/workspaces/devs/python-artron/artron/task.py", line 89, in run
    **self.inputs
  File "examples/basic.py", line 19, in builder_func_3
    raise Exception("ERROR builder_func_3")
Exception: ERROR builder_func_3

artron: [ERROR] ERROR builder_func_3
{'date_end': '2018-08-29T20:02:54.640Z',
 'date_start': '2018-08-29T20:02:39.606Z',
 'elapsed': '00:00:15',
 'exit_code': 1,
 'results': {'aborted': 0,
             'deps': 2,
             'failures': 1,
             'nrun': 0,
             'ready': 0,
             'success': 3},
 'tasks': [{'date_created': '2018-08-29T20:02:39.605Z',
            'date_end': None,
            'date_start': None,
            'func': 'builder_func_1',
            'inputs': {'msg': 'task-1-msg'},
            'require': ['task-id-2', 'task-id-4'],
            'results': None,
            'state': -2,
            'tid': 'task-id-1',
            'time_duration': 0.0,
            'time_duration_str': '00:00:00'},
           {'date_created': '2018-08-29T20:02:39.605Z',
            'date_end': '2018-08-29T20:02:41.617Z',
            'date_start': '2018-08-29T20:02:40.615Z',
            'func': 'builder_func_3',
            'inputs': {'msg': 'task-3-msg'},
            'require': [],
            'results': 'ERROR builder_func_3',
            'state': -1,
            'tid': 'task-id-3',
            'time_duration': 1.0019969940185547,
            'time_duration_str': '00:00:01'},
           {'date_created': '2018-08-29T20:02:39.605Z',
            'date_end': '2018-08-29T20:02:48.625Z',
            'date_start': '2018-08-29T20:02:45.621Z',
            'func': 'builder_func_2',
            'inputs': {'msg': 'task-2-msg'},
            'require': [],
            'results': 'builder_func_2 ==> task-2-msg',
            'state': 3,
            'tid': 'task-id-2',
            'time_duration': 3.0032620429992676,
            'time_duration_str': '00:00:03'},
           {'date_created': '2018-08-29T20:02:39.605Z',
            'date_end': None,
            'date_start': None,
            'func': 'builder_func_2',
            'inputs': {'msg': 'task-5-msg'},
            'require': [],
            'results': None,
            'state': -2,
            'tid': 'task-id-5',
            'time_duration': 0.0,
            'time_duration_str': '00:00:00'},
           {'date_created': '2018-08-29T20:02:39.605Z',
            'date_end': '2018-08-29T20:02:43.616Z',
            'date_start': '2018-08-29T20:02:39.613Z',
            'func': 'builder_func_4',
            'inputs': {'msg': 'task-4-msg'},
            'require': [],
            'results': 'builder_func_4 ==> task-4-msg',
            'state': 3,
            'tid': 'task-id-4',
            'time_duration': 4.003551006317139,
            'time_duration_str': '00:00:04'},
           {'date_created': '2018-08-29T20:02:39.605Z',
            'date_end': '2018-08-29T20:02:54.636Z',
            'date_start': '2018-08-29T20:02:50.631Z',
            'func': 'builder_func_4',
            'inputs': {'msg': 'task-6-msg'},
            'require': [],
            'results': 'builder_func_4 ==> task-6-msg',
            'state': 3,
            'tid': 'task-id-6',
            'time_duration': 4.00443696975708,
            'time_duration_str': '00:00:04'}]}
```

## Details

### Tasks

`Task` is an object with `function` to run on `builder`, `inputs` to send and `state` also with time informations.

**States values:**

* -2: dependency error, means that parent task failed.
* -1: task failed to run
* 0: initial state (when creating them)
* 1: task is ready and in queue, there is no more dependencies, waiting to be process by workers
* 2: task is running
* 3: task run successfully

### Worker

`Worker` is just a `process`. 
By default, `multiprocessing.cpu_count()` is used as number of workers.

## Integrations

You could use [click](http://click.pocoo.org/5/) to create simple cli.

```shell
pip install click
```

```python
# -*- coding: utf-8 -*-
import basic # import examples/basic.py

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
```

List tasks

```shell
$ python examples/basic_cli.py list
- task-id-1
- task-id-3
- task-id-2
- task-id-5
- task-id-4
- task-id-6
```

# Licence

Copyright 2018 - Ahmet Demir

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.


class ProgressBar(object):
    """Simple progress bar"""
    def __init__(self, total=100):
        self.total = total
        self.n = 0

    def update(self, count=1):
        if self.n == 0:
            sys.stdout.write("[%s]" % (" " * self.total))
            sys.stdout.flush()
            sys.stdout.write("\b" * (self.total+1))
        for _ in range(0, min(count, self.total-self.n)):
            sys.stdout.write("-")
            sys.stdout.flush()
        self.n += count

    def close(self):
        self.update(self.total - self.n)
        sys.stdout.write("\n")
