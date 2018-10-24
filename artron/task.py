# -*- coding: utf-8 -*-
"""
artron.task
~~~~~~~~~~~

artron task management
"""
# standard
import copy
import json
import time
import logging
import traceback

from artron import utils

LOGGER = logging.getLogger(__name__)


class TaskDependenciesError(Exception):
    """Occurs when dependency is missing"""
    pass


class Task(object): # pylint: disable=too-many-instance-attributes
    """
    A task could run on a `builder`.

    It's not the builder who manage tasks but a task will safely be runnable
    on each builder.

    To get a complete Graph course, code and more generate,
    go on http://www.python-course.eu/graphs_python.php

    Args:
        tasks (dict): dict with key as task id and value as task obj
        tid (str): task uniq identifier.
        inputs (dict): kwargs format to send to the `func`
        func (str): function name to use on the `builder`. The builder is not in
                    object but as arg in `run`. Because the task should be
                    runnable on different builders.
        require (Optional[list]): List of required task ids .Defaults to None.

    Attributes:
        tid (str): task uniq identifier.
        inputs (dict): kwargs format to send to the `func`
        func (str): function name to use on the `builder`. The builder is not in
                    object but as arg in `run`. Because the task should be
                    runnable on different builders.
        require (Optional[list]): List of required task ids .Defaults to None.
        state (int): Task state, one of TASK_* attribute.
        results (obj): Task's func results.
        date_created (str): date when task created.
        date_start (str): date when task started.
        date_end (str): date when task ended.
        time_duration (float): Task run duration.
        time_duration_str (str): Task run duration in form '00:00:00'.
        STATE_WRONG (int): status for wrong execution like task w requirements.
        STATE_DEPENDENCY (int): status for deps error ie. parent task failed.
        STATE_ERROR (int): status for failed task.
        STATE_INIT (int): status for fresh task.
        STATE_READY (int): status for ready to run ie. not deps.
        STATE_RUNNING (int): status for running task.
        STATE_SUCCESS (int): status for finished and success task.
    """

    STATE_WRONG = -3
    STATE_DEPENDENCY = -2
    STATE_ERROR = -1
    STATE_INIT = 0
    STATE_READY = 1
    STATE_RUNNING = 2
    STATE_SUCCESS = 3

    def __init__(self, tid, inputs, func, require=None):
        self.tid = tid
        self.inputs = inputs
        self.func = func
        self.require = require
        if not self.require:
            self.require = []
        self.state = 0
        self.results = None
        self.date_created = utils.strdate()
        self.date_start = None
        self.date_end = None
        self.time_duration_str = '00:00:00'
        self.time_duration = 0.0

    def __repr__(self):
        """Object representation into json

        Returns;
            str: json dump of the object.
        """
        return json.dumps(self.__dict__)

    def run(self, builder, retry):
        """Run task on specified `builder`.

        Args:
            builder (obj): Builder object with the `func` to run.
            retry (bool): number of retry.

        Raises:
            TaskDependenciesError: If the task has dependencies.
        """
        time_start = time.time()
        self.date_start = utils.strdate()

        if self.require:
            raise TaskDependenciesError("Task {} can't run. Requires {}"\
                .format(self.tid, ', '.join(self.require)))
        try:
            self.results = getattr(builder, self.func)(
                retry=retry,
                **self.inputs
            )
            self.state = self.STATE_SUCCESS

        except Exception as err: # pylint: disable=broad-except
            trb = traceback.format_exc()
            LOGGER.error(trb)
            LOGGER.error(err)
            self.results = str(err)
            self.state = self.STATE_ERROR

        duration = time.time() - time_start
        self.time_duration = duration
        self.time_duration_str = utils.strgmtime(time.gmtime(duration))
        self.date_end = utils.strdate()

    def add_require(self, task_id):
        """Add dependency

        Args:
            task_id (str): task id to add as dependency
        """
        self.require.append(task_id)

    def del_require(self, task_id):
        """Delete dependency

        Args:
            task_id (str): task id to remove as dependency
        """
        self.require.remove(task_id)

    def is_runnable(self):
        """Is the task runnable

        Returns:
            bool: true if state init and no dependencies
        """
        return self.state == self.STATE_INIT and not self.require

    def is_finished(self):
        """Check if a task is finnished

        Returns:
            bool: if a task is not in state init or ready
        """

        return self.state != self.STATE_INIT and self.state != self.STATE_READY

    def update_childs(self, _tasks):
        """Update task childs

        When a task state changes, update childs.
        If the task success, remove dependencies on childs otherwise mark childs
        states with STATE_DEPENDENCY

        Args:
            tasks (dict): dict with key as task id and value as task obj

        Yields:
            dict: updated {taskid: task} item.
        """
        tasks = copy.deepcopy(_tasks)
        for child in tasks.keys():

            # only process init state tasks
            if tasks[child].state != self.STATE_INIT:
                continue

            # if erased and none
            if not tasks[child].require:
                continue

            # process all childs
            for r_tid in tasks[child].require:

                # if child id is not me, ignore
                if r_tid != self.tid:
                    continue

                # success
                elif self.state == self.STATE_SUCCESS:
                    tasks[child].del_require(r_tid)
                    yield {tasks[child].tid: tasks[child]}

                # task running
                elif self.state == self.STATE_RUNNING:
                    continue

                # task error
                elif self.state < self.STATE_INIT:
                    tasks[child].state = self.STATE_DEPENDENCY
                    tasks[child].del_require(r_tid)

                    yield {tasks[child].tid: tasks[child]}

                    # recurse and mark child of child as dependency error
                    for item in tasks[child].update_childs(tasks):
                        yield item
