# -*- coding: utf-8 -*-
"""
artron.worker
~~~~~~~~~~~~

artron task runner
"""
import logging
import traceback
import multiprocessing

# import local
from artron import utils
from artron._py6 import iteritems, range_type
from artron.task import Task, TaskDependenciesError

LOGGER = logging.getLogger(__name__)

class Worker(multiprocessing.Process):
    """This module provides a queue implementation.
    It provides a convenient way of moving Python objects between different
    subprocesses.

    Args:
        builder (obj): Builder object with the `func` to run.
        queue (multiprocessing.Manager.Queue): queue can be shared between
            subprocesses.
        name (str): Worker name.
        tasks (multiprocessing.managers.DictProxy): shared dict object and
            return a proxy for it.
        max_retry (str): Number of retry when task fail.

    Attributes:
        builder (obj): Builder object with the `func` to run.
        queue (multiprocessing.Manager.Queue): queue can be shared between
            subprocesses.
        name (str): Worker name.
        tasks (multiprocessing.managers.DictProxy): shared dict object and
            return a proxy for it.
        max_retry (str): Number of retry when task fail.
        lock (multiprocessing.Lock): Lock on ressource access.

    See Also:
        * http://effbot.org/librarybook/queue.htm
        * https://docs.python.org/3/library/multiprocessing.html
    """
    # pylint: disable=line-too-long,too-many-arguments
    def __init__(self, builder, queue, name, tasks, max_retry, lock):
        super(Worker, self).__init__()
        self.queue = queue
        self.name = name
        self.tasks = tasks
        self.builder = builder
        self.max_retry = max_retry
        self.lock = lock

    def stop(self):
        """Stop the worker"""
        if self.is_alive():
            # send sigterm
            self.terminate()

    def run(self):
        """Run infinite while receive a marker var or exec something"""
        while self.is_alive():
            task, = self.queue.get()
            if task is None:
                LOGGER.debug(
                    "%s> getting end-of-queue markers",
                    self.name
                )
                # Indicate that a formerly enqueued task is complete
                self.queue.task_done()
                # reached end of queue
                break

            LOGGER.debug("%s> begin(%s) task.tid=%s", self.name,\
                utils.strdate(), task)

            # run the task
            with self.lock:
                current_task = self.tasks[task]
                current_task.state = Task.STATE_RUNNING
                self.tasks[task] = current_task

            try:
                for retry in range_type(1, self.max_retry+1):
                    LOGGER.debug("running retry=%d task state %d", \
                        retry, self.tasks[task].state)

                    result = current_task.run(self.builder, retry=retry)

                    if current_task.state == Task.STATE_SUCCESS:
                        LOGGER.debug("%s> end(%s) task.tid=%s results=%s",\
                            self.name, utils.strdate(), task, result)
                        break

            except TaskDependenciesError as err:
                current_task.state = Task.STATE_WRONG
                LOGGER.error("%s> %s", self.name, err)

            except Exception as err: # pylint: disable=broad-except
                current_task.state = Task.STATE_ERROR
                trb = traceback.format_exc()
                LOGGER.error("%s> You will see this error in prod: %s",\
                    self.name, err)
                LOGGER.error(trb)

            finally:
                # write proxydict content
                with self.lock:
                    self.tasks[task] = current_task
                    LOGGER.debug("update childs of %s", task)
                    # Update tasks depends on this task
                    for updated in current_task.update_childs(self.tasks):
                        for tasku_id, tasku in iteritems(updated):
                            # LOGGER.debug("update task of %s", tasku)
                            self.tasks[tasku_id] = tasku

                self.queue.task_done()
        else:
            self.queue.task_done()
