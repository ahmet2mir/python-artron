# -*- coding: utf-8 -*-
"""
artron.task
~~~~~~~~~~~

artron task management
"""
# standard
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
    A task is an object defined by as state and an executor
    """
    # States names
    # https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Process_states.svg/2000px-Process_states.svg.png

    STATE_DEPENDENCY = -2
    STATE_ERROR = -1
    STATE_INIT = 0
    STATE_READY = 1
    STATE_RUNNING = 2
    STATE_SUCCESS = 3

    def __init__(self, tid, inputs, func, require=None):
        """Task object

        Parameters
        ----------
        tid : str
            Task id used
        inputs : dict
            Inputs passed to func
        func : str
            method name to run on builder object
        require : list
            list of task ids required by this task
        """
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
        """object representation into json"""
        return json.dumps(self.__dict__)

    def run(self, builder, retry):
        """Run task

        Parameters
        ----------
        builder : Builder
            Builder object
        retry : bool
            retry count
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

        Parameters
        ----------
        task_id : str
            task id to add as dependency
        """
        self.require.append(task_id)

    def del_require(self, task_id):
        """Delete dependency

        Parameters
        ----------
        task_id : str
            task id to remove as dependency
        """
        self.require.remove(task_id)

    def is_runnable(self):
        """Is the task runnable

        Returns
        ----------
        runnable : bool
            true if state init and no dependencies
        """
        return self.state == self.STATE_INIT and not self.require

    def update_childs(self, tasks):
        """Update task childs

        When a task state changes, update childs.
        If the task success, remove dependencies on childs otherwise mark childs
        states with STATE_DEPENDENCY

        Parameters
        ----------
        tasks : dict(Task)
            dict of tasks
        """
        child_ids = tasks.keys()

        for child_id in child_ids:
            # manage deps
            child_task = tasks[child_id]

            if child_task.state != self.STATE_INIT:
                continue

            for r_tid in child_task.require:
                if r_tid != self.tid:
                    continue
                # task running
                elif self.state == self.STATE_RUNNING:
                    continue
                # task error
                elif self.state < self.STATE_INIT:
                    child_task.state = self.STATE_DEPENDENCY
                    child_task.del_require(r_tid)
                    LOGGER.debug("Remove require %s of %s", \
                        r_tid, child_task.tid)
                    yield {child_task.tid: child_task}
                    for item in child_task.update_childs(tasks):
                        yield item
                # success
                elif self.state == self.STATE_SUCCESS:
                    child_task.del_require(r_tid)
                    yield {child_task.tid: child_task}
                    LOGGER.debug("Remove require %s of %s", \
                        r_tid, child_task.tid)
                    for item in child_task.update_childs(tasks):
                        yield item
                # else:
                #    LOGGER.error("Unknown task(%s).state (%d)", \
                #        self.tid, self.state)
