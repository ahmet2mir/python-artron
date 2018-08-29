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
    """Based on http://effbot.org/librarybook/queue.htm"""
    # pylint: disable=line-too-long
    def __init__(self, builder, queue, name, tasks, max_retry):
        """Init the worker:

        Parameters
        ----------
            builder: Builder
                Builder to use
            queue: queue.Queue
                queue to process
            name: str
                worker name
            tasks: ProxyDict
                dict with tasks shared between processes

        See also
        --------
        * https://docs.python.org/2/library/multiprocessing.html#multiprocessing-managers
        """
        super(Worker, self).__init__()
        self.queue = queue
        self.name = name
        self.tasks = tasks
        self.builder = builder
        self.max_retry = max_retry

    def stop(self):
        """Stop the worker"""
        if self.is_alive():
            self.terminate()

    def run(self):
        """Run infinite while receive a marker var or exec something"""
        while 1:
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
            parent_task = self.tasks[task]
            parent_task.state = Task.STATE_RUNNING
            self.tasks[task] = parent_task

            try:
                for retry in range_type(1, self.max_retry+1):
                    LOGGER.debug("running retry=%d task state %d", \
                        retry, self.tasks[task].state)

                    result = parent_task.run(self.builder, retry=retry)

                    # write proxydict content
                    self.tasks[task] = parent_task

                    if parent_task.state == Task.STATE_SUCCESS:
                        LOGGER.debug("%s> end(%s) task.tid=%s results=%s",\
                            self.name, utils.strdate(), task, result)
                        break
                    # continue with the same copy of the task

            except TaskDependenciesError as err:
                LOGGER.error("%s> %s", self.name, err)

            except Exception as err: # pylint: disable=broad-except
                trb = traceback.format_exc()
                LOGGER.error("%s> You will see this error in prod: %s",\
                    self.name, err)
                LOGGER.error(trb)

            finally:
                # write proxydict content
                self.tasks[task] = parent_task
                LOGGER.debug("update chidls of %s", task)
                # Update tasks depends on this task
                for updated in parent_task.update_childs(self.tasks):
                    for task_id, task in iteritems(updated):
                        self.tasks[task_id] = task

                self.queue.task_done()
