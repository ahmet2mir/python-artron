# -*- coding: utf-8 -*-
import json

import pytest
from mock import patch, MagicMock

from artron import _py6
from artron.task import TaskDependenciesError, Task


task = Task("tid", {"for": "bar"}, "func")


def test_init():

    assert task.tid == "tid"
    assert task.inputs == {"for": "bar"}
    assert task.func == "func"
    assert task.require == []
    assert task.state == 0
    assert task.results == None
    assert isinstance(task.date_created, _py6.string_types)
    assert task.date_start == None
    assert task.date_end == None
    assert task.time_duration_str == '00:00:00'
    assert task.time_duration == 0.0

    assert task.STATE_DEPENDENCY == -2
    assert task.STATE_ERROR == -1
    assert task.STATE_INIT == 0
    assert task.STATE_READY == 1
    assert task.STATE_RUNNING == 2
    assert task.STATE_SUCCESS == 3

    task_x = Task("tid2", {"foo": "bar2"}, "func", require=["tid1"])
    assert task_x.require == ["tid1"]


def test_repr():
    assert json.loads(str(task))["tid"] == task.tid


def test_run():

    builder1 = MagicMock()
    builder1.func.return_value = "success"

    task.run(builder1, 1)
    assert task.date_start is not None
    assert task.date_start is not None
    assert task.date_start is not None
    assert task.date_end is not None
    assert task.time_duration is not None

    builder2 = MagicMock()
    builder2.func = MagicMock(side_effect=Exception)
    task.run(builder2, 1)

    task.require = ["foo"]
    builder3 = MagicMock()
    with pytest.raises(TaskDependenciesError):
        task.run(builder3, 1)
    task.require = []


def test_add_del():

    task.add_require("foo")
    assert task.require == ["foo"]

    task.del_require("foo")
    assert task.require == []


def test_is_runnable():

    task.state = Task.STATE_READY
    assert task.is_runnable() == False

    task.state = Task.STATE_INIT
    assert task.is_runnable() == True

    task.require = ["foo"]
    assert task.is_runnable() == False

    task.require = []
    task.state = Task.STATE_INIT


def test_is_finished():

    task.state = Task.STATE_READY
    assert task.is_finished() == False

    task.state = Task.STATE_INIT
    assert task.is_finished() == False

    task.state = Task.STATE_SUCCESS
    assert task.is_finished() == True

    task.require = []
    task.state = Task.STATE_INIT


def test_update_childs():

    task1 = Task("tid1", {"foo": "bar1"}, "func")
    task2 = Task("tid2", {"foo": "bar2"}, "func", require=["tid1", "tid3"])
    task3 = Task("tid3", {"foo": "bar3"}, "func", require=["tid1"])
    tasks = {
        task1.tid: task1,
        task2.tid: task2,
        task3.tid: task3,
    }

    task1.state = Task.STATE_SUCCESS

    items = list(task1.update_childs(tasks))
    # Update tasks depends on this task
    for updated in items:
        for task_id, task in _py6.iteritems(updated):
            tasks[task_id] = task
 
    assert tasks[task3.tid].require == []
    assert tasks[task2.tid].require == [task3.tid]
 
    task3.state = Task.STATE_SUCCESS
    tasks[task3.tid] = task3


def test_update_childs_running():

    task1 = Task("tid1", {"foo": "bar1"}, "func")
    task2 = Task("tid2", {"foo": "bar2"}, "func", require=["tid1"])
    tasks = {
        task1.tid: task1,
        task2.tid: task2,
    }
    task1.state = Task.STATE_RUNNING
    task2.state = Task.STATE_INIT
    assert list(task1.update_childs(tasks)) == []


def test_update_childs_error():

    task1 = Task("tid1", {"foo": "bar1"}, "func")
    task2 = Task("tid2", {"foo": "bar2"}, "func", require=["tid1"])
    tasks = {
        task1.tid: task1,
        task2.tid: task2,
    }
    task1.state = Task.STATE_ERROR

    updated = list(task1.update_childs(tasks))[0]
    assert task2.tid in updated
    assert updated[task2.tid].state == Task.STATE_DEPENDENCY


def test_update_childs_error_dependencies():

    task1 = Task("tid1", {"foo": "bar1"}, "func")
    task2 = Task("tid2", {"foo": "bar2"}, "func", require=["tid1"])
    task3 = Task("tid3", {"foo": "bar3"}, "func", require=["tid2"])
    tasks = {
        task1.tid: task1,
        task2.tid: task2,
        task3.tid: task3,
    }
    task1.state = Task.STATE_ERROR

    for updated in list(task1.update_childs(tasks)):
        assert updated[list(_py6.iterkeys(updated))[0]].state == Task.STATE_DEPENDENCY


def test_update_childs_none_require():
    task1 = Task("tid1", {"foo": "bar1"}, "func")
    task2 = Task("tid2", {"foo": "bar2"}, "func", require=["tid1"])

    task1.require = None
    task2.require = None
    task1.state = Task.STATE_SUCCESS

    tasks = {
        task1.tid: task1,
        task2.tid: task2,
    }

    list(task1.update_childs(tasks))

def test_update_childs_loop():
    task1 = Task("tid1", {"foo": "bar1"}, "func")
    task2 = Task("tid2", {"foo": "bar2"}, "func", require=["tid1"])

    task1.require = None
    task2.require = None
    task1.state = Task.STATE_SUCCESS

    tasks = {
        task1.tid: task1,
        task2.tid: task2,
    }

    list(task1.update_childs(tasks))
