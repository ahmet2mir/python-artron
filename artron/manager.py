# -*- coding: utf-8 -*-
"""
atron.manager
~~~~~~~~~~~~~
"""
# standard
import os
import time
import multiprocessing

import logging
import logging.config
import logging.handlers

# local
from artron import utils
from artron.graph import Graph
from artron.task import Task
from artron.worker import Worker
from artron._py6 import range_type, TimeoutError


logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            '()': 'logging.Formatter',
            'format': 'artron: [%(levelname)s] %(message)s'
        }
    },
    'handlers': {
        'console':{
            'level': os.environ.get('ARTRON_LEVEL', 'ERROR').upper(),
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'artron': {
            'level': os.environ.get('ARTRON_LEVEL', 'ERROR').upper(),
            'handlers': ['console']
        }
    }
})
LOGGER = logging.getLogger(__name__)

TASK_TIMEOUT = 1200

class Manager(object):
    """Manager"""
    def __init__(self, builder, nb_workers=None, workers=None, queue=None, \
                 run_timeout=3600, sleep=1, tasks=None, max_retry=3):
        """Init manager, if vars are None use default"""
        self.builder = builder
        self.nb_workers = nb_workers
        self.queue = queue
        self.tasks = tasks
        self.workers = workers
        self.timeout = time.time() + run_timeout
        self.sleep = sleep
        self.max_retry = max_retry

        if tasks is None:
            tasks = {}

        if self.nb_workers is None:
            self.nb_workers = multiprocessing.cpu_count()

        if self.queue is None or self.tasks is None:
            mng = multiprocessing.Manager()
            if self.queue is None:
                self.queue = mng.Queue()
            if self.tasks is None:
                self.tasks = mng.dict(tasks)

        if self.workers is None:
            self.workers = [
                Worker(self.builder, self.queue, "worker-%d" % wid, self.tasks, max_retry)
                for wid in range_type(self.nb_workers)
            ]

    def add(self, task):
        self.tasks[task.tid] = task

    def start(self):
        """Start manager"""
        time_start = time.time()

        out = {
            'elapsed': 0.0,
            'date_end': None,
            'date_start': utils.strdate(),
            'results': {
                'success': 0,
                'failures': 0,
                'deps': 0,
                'nrun': 0,
                'aborted': 0,
                'ready': 0
            },
            'exit_code': 1,
            'tasks': []
        }

        try:
            # start all workers
            LOGGER.debug("init %d workers" % self.nb_workers)
            for worker in self.workers:
                worker.start()

            LOGGER.debug("send resources to queues")

            # generate exec graph
            graph = Graph(self.tasks)

            # while we have non empty graph and don't reach timeout
            while list(graph.edges()) and time.time() < self.timeout:
                # isolated vertice is task without deps
                for task_id in graph.isolated_vertices():

                    LOGGER.debug("isolated vertex task(%s) with state(%d)", \
                        task_id, self.tasks[task_id].state)

                    if self.tasks[task_id].is_runnable():
                        LOGGER.debug("send task(%s)", task_id)

                        # update task status because put in queue != is running
                        # so to avoid multiple queue send, mark it as running
                        task_new = self.tasks[task_id]
                        task_new.state = Task.STATE_READY
                        self.tasks[task_id] = task_new

                        self.queue.put((task_id,))

                graph = Graph(self.tasks)
                time.sleep(self.sleep)

            if time.time() > self.timeout:
                raise TimeoutError('timeout error')

            LOGGER.debug("add end-of-queue markers")
            for _ in self.workers:
                # True add the end to mark the end of queue
                self.queue.put((None,))

            LOGGER.debug("blocks until all items in the queue have been "\
                  "gotten and processed.")
            self.queue.join()

        # catch all errors
        # pylint: disable=broad-except
        except Exception as err:
            LOGGER.error("%s. Exiting...", err)

        # stop workers
        finally:
            LOGGER.debug("stop all workers")
            for worker in self.workers:
                worker.stop()
                LOGGER.debug("stop workers %s", worker.name)

        out['date_end'] = utils.strdate()

        # final message
        for task in self.tasks.values():
            out['tasks'].append(task.__dict__)
            if task.state == Task.STATE_SUCCESS:
                out['results']['success'] += 1

            elif task.state == Task.STATE_ERROR:
                out['results']['failures'] += 1

            elif task.state == Task.STATE_DEPENDENCY:
                out['results']['deps'] += 1

            elif task.state == Task.STATE_INIT:
                out['results']['nrun'] += 1

            elif task.state == Task.STATE_RUNNING:
                out['results']['aborted'] += 1

            elif task.state == Task.STATE_READY:
                out['results']['ready'] += 1

        if len(out['tasks']) == out['results']['success']:
            out['exit_code'] = 0

        out['elapsed'] = utils.strgmtime(time.gmtime(time.time() - time_start))

        return out
