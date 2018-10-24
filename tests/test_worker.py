# -*- coding: utf-8 -*-
import json
import time
import multiprocessing

import pytest
from mock import patch, MagicMock
import mock

from artron import _py6
from artron.worker import Worker
from artron.task import TaskDependenciesError, Task

class Builder(object):
    
    def builder_func_1(self, msg, retry):
        time.sleep(0.3)
        return "builder_func_1 ==> " + msg

    def builder_func_2(self, msg, retry):
        time.sleep(0.5)
        return "builder_func_2 ==> " + msg

    def builder_func_3(self, msg, retry):
        raise Exception("ERROR builder_func_3")


def test_worker_start():

    task1 = Task('task-id-1', {'msg': 'task-1-msg'}, 'builder_func_1')
    task2 = Task('task-id-2', {'msg': 'task-2-msg'}, 'builder_func_2', require=[task1.tid])

    mng = multiprocessing.Manager()
    builder = Builder()
    queue = mng.Queue()
    name = "worker1"
    max_retry = 1

    task1.state = Task.STATE_READY

    tasks = mng.dict({task1.tid: task1, task2.tid: task2})

    worker = Worker(
        builder=builder,
        queue=queue,
        tasks=tasks,
        name=name,
        max_retry=max_retry,
        lock=mng.RLock()
    )

    assert worker.max_retry == max_retry
    assert worker.name == name

    # start worker
    worker.start()
    
    # send tasks
    queue.put((task1.tid,))
    queue.put((task2.tid,))
    queue.put((None,))
    queue.join()

    # stop worker
    worker.stop()
    worker.join()

    assert tasks[task1.tid].state == Task.STATE_SUCCESS
    assert tasks[task1.tid].results == 'builder_func_1 ==> task-1-msg'
    assert tasks[task2.tid].state == Task.STATE_SUCCESS


@patch('artron.worker.Worker.is_alive', return_value=True)
def test_worker_run(is_alive):

    task1 = Task('task-id-1', {'msg': 'task-1-msg'}, 'builder_func_1')
    task2 = Task('task-id-2', {'msg': 'task-2-msg'}, 'builder_func_2', require=[task1.tid])

    mng = multiprocessing.Manager()

    task1.state = Task.STATE_READY

    tasks = mng.dict({task1.tid: task1, task2.tid: task2})

    worker = Worker(
        builder=Builder(),
        queue=mng.Queue(),
        tasks=tasks,
        name="worker1",
        max_retry=1,
        lock=mng.RLock()
    )
    worker.queue.put((task1.tid,))
    worker.queue.put((task2.tid,))
    worker.queue.put((None,))

    assert worker.max_retry == 1
    assert worker.name == "worker1"
    
    worker.run()

    assert tasks[task1.tid].state == Task.STATE_SUCCESS
    assert tasks[task1.tid].results == 'builder_func_1 ==> task-1-msg'
    assert tasks[task2.tid].state == Task.STATE_SUCCESS


@patch('artron.worker.Worker.is_alive', return_value=True)
def test_worker_retry(is_alive):

    mng = multiprocessing.Manager()

    task = Task('task-id-3', {'msg': 'task-3-msg'}, 'builder_func_3')
    task.state = Task.STATE_READY
    task.run = MagicMock()
    task.run.return_value = 1

    worker = Worker(
        builder=Builder(),
        queue=mng.Queue(),
        tasks={task.tid: task},
        name="worker1",
        max_retry=3,
        lock=mng.RLock()
    )

    worker.builder.builder_func_1 = MagicMock()
    worker.builder.builder_func_1.side_effect = RuntimeError("retry!")

    worker.queue.put((task.tid,))
    worker.queue.put((None,))

    worker.run()

    assert task.run.call_count == 3

@patch('artron.worker.Worker.is_alive', return_value=True)
def test_worker_exception(is_alive):

    mng = multiprocessing.Manager()

    task = Task('task-id-3', {'msg': 'task-3-msg'}, 'builder_func_3')
    task.state = Task.STATE_READY
    task.run = MagicMock()
    task.run.side_effect = Exception("erro")

    worker = Worker(
        builder=Builder(),
        queue=mng.Queue(),
        tasks={task.tid: task},
        name="worker1",
        max_retry=3,
        lock=mng.RLock()
    )

    worker.builder.builder_func_1 = MagicMock()
    worker.builder.builder_func_1.side_effect = RuntimeError("retry!")

    worker.queue.put((task.tid,))
    worker.queue.put((None,))

    worker.run()

    assert task.run.call_count == 1


class MyTask(Task):
    def run(*args, **kwargs):
        raise TaskDependenciesError("foo")

@patch('artron.worker.Worker.is_alive', return_value=True)
def test_worker_dependency_exception(is_alive):
    mng = multiprocessing.Manager()

    task = MyTask('task-id-1', {'msg': 'task-1-msg'}, 'builder_func_1')
    task.state = Task.STATE_READY

    tasks = mng.dict({task.tid: task})

    worker = Worker(
        builder=Builder(),
        queue=mng.Queue(),
        tasks=tasks,
        name="worker1",
        max_retry=3,
        lock=mng.RLock()
    )

    worker.builder.builder_func_1 = MagicMock()
    worker.builder.builder_func_1.side_effect = RuntimeError("retry!")

    worker.queue.put((task.tid,))
    worker.queue.put((None,))

    worker.run()

    assert tasks[task.tid].state == Task.STATE_WRONG


@patch('artron.worker.Worker.is_alive', return_value=False)
def test_worker_alive_run(is_alive):
    worker = Worker(
        builder=None,
        queue=MagicMock(),
        tasks={},
        name="worker",
        max_retry=3,
        lock=multiprocessing.Manager().RLock()
    )

    worker.run()
    worker.queue.task_done.assert_called()


def test_worker_stop():
    worker = Worker(
        builder=None,
        queue=MagicMock(),
        tasks={},
        name="worker",
        max_retry=3,
        lock=multiprocessing.Manager().RLock()
    )
    # if is alive, don't call terminate
    worker.is_alive = MagicMock()
    worker.is_alive.return_value = True
    worker.terminate = MagicMock()
    worker.stop()
    worker.terminate.assert_called()

    # if is not alive, don't call terminate
    worker.is_alive = MagicMock()
    worker.is_alive.return_value = False
    worker.terminate = MagicMock()
    worker.stop()
    worker.terminate.assert_not_called()


# when running start, worker will not run `run` func
@patch('artron.worker.Worker.is_alive', return_value=False)
def test_worker_alive_start(is_alive):
    worker = Worker(
        builder=None,
        queue=MagicMock(),
        tasks={},
        name="worker",
        max_retry=3,
        lock=multiprocessing.Manager().RLock()
    )

    worker.start()
    worker.queue.task_done.assert_not_called()


@patch('artron.worker.Worker.is_alive', return_value=True)
def test_worker_loop(is_alive):
    worker = Worker(
        builder=None,
        queue=MagicMock(),
        tasks={},
        name="worker",
        max_retry=3,
        lock=multiprocessing.Manager().RLock()
    )
    worker.queue.get.return_value = (None,)

    worker.run()

    assert is_alive.call_count == 1

