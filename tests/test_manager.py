# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import time
import multiprocessing

import pytest
from mock import patch, MagicMock

from artron.task import Task
from artron.manager import Manager

class Builder(object):
    
    def builder_func_1(self, msg, retry):
        time.sleep(0.2)
        return "builder_func_1 ==> " + msg

    def builder_func_2(self, msg, retry):
        time.sleep(0.3)
        return "builder_func_2 ==> " + msg

    def builder_func_3(self, msg, retry):
        time.sleep(0.1)
        raise Exception("ERROR builder_func_3")

    def builder_func_4(self, msg, retry):
        time.sleep(0.1)
        return "builder_func_4 ==> " + msg


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


def test_start():
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

    # start
    manager.start()


def test_progress():
    # builder to pass to Artron
    builder = Builder()

    # declare manager
    manager = Manager(builder, max_retry=2)

    # declare tasks
    task1 = Task('task-id-1', {'msg': 'task-1-msg'}, 'builder_func_1')
    task2 = Task('task-id-2', {'msg': 'task-2-msg'}, 'builder_func_2')
    
    # add task
    manager.add(task1)
    manager.add(task2)

    ProgressBar = MagicMock()
    ProgressBar.update.return_value = True
    ProgressBar.close.return_value = True

    manager.progress = ProgressBar()

    # start
    results = manager.start()

    ProgressBar.update.call_count = 3


def test_timeout():

    # builder to pass to Artron
    builder = Builder()

    # declare manager
    manager = Manager(builder, max_retry=2)

    # declare tasks
    task1 = Task('task-id-1', {'msg': 'task-1-msg'}, 'builder_func_1')
    task2 = Task('task-id-2', {'msg': 'task-2-msg'}, 'builder_func_2')
    
    # add task
    manager.add(task1)
    manager.add(task2)

    manager.timeout = 0

    # start
    results = manager.start()

def test_default():

    manager = Manager(
        builder=Builder(),
    )

    assert manager.nb_workers == multiprocessing.cpu_count()
    assert len(manager.workers) == multiprocessing.cpu_count()
    assert manager.queue is not None
    assert manager.timeout > 3600
    assert manager.sleep == 1
    assert manager.tasks is not None

    manager2 = Manager(
        builder=Builder(),
        nb_workers=2,
        workers=[1,2,3,4],
        queue=1,
        run_timeout=1800,
        sleep=2,
        tasks={1:2},
        max_retry=3,
        progress=None,
    )

    assert manager2.nb_workers == 2
    assert len(manager2.workers) == 4
    assert manager2.queue == 1
    assert manager2.timeout > 1800
    assert manager2.sleep == 2
    assert manager2.tasks == {1:2}

if __name__ == '__main__':
    test_default()
