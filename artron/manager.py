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
from artron.task import Task
from artron.graph import Graph
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


class Manager(object): # pylint: disable=too-many-instance-attributes
    """Manager class is the central piece of Artron.
    It takes care of creating, start and queueing jobs.

    Attributes:
        builder (obj): Builder object with the `func` to run.
        lock (multiprocessing.Lock): Lock on ressource access.
        max_retry (int): Number of retry when task fail.
        progress (obj): Progress bar.
        queue (multiprocessing.Manager.Queue): queue can be shared between
            subprocesses.
        sleep (int): sleep value in seconds when iterating edges.
        tasks (multiprocessing.managers.DictProxy): shared dict object and
            return a proxy for it.
        timeout (int): timestamp when timeout will be triggered.
        workers (list):  list of `artron.worker.Worker`

    Args:
        builder (obj): Builder object with the `func` to run.
        nb_workers (int): number of worker
        workers (list):  list of `artron.worker.Worker`
        queue (multiprocessing.Manager.Queue): queue can be shared between
            subprocesses.
        run_timeout (int): number of seconds for timeout. Will be added to
            attribute timeout with current timestamp.
        sleep (int): sleep value itasks (multiprocessing.managers.DictProxy):
            shared dict object and return a proxy for it.tasks=None
        max_retry (int): Number of retry when task fail.
        progress (obj): Progress bar.


    Examples:
        >>> manager = Manager(builder, max_retry=2)
    """
    # pylint: disable=too-many-arguments
    def __init__(self, builder, nb_workers=None, workers=None, queue=None, \
                 run_timeout=3600, sleep=1, tasks=None, max_retry=3, \
                 progress=None):
        self.builder = builder
        self.nb_workers = nb_workers
        self.queue = queue
        self.tasks = tasks
        self.workers = workers
        self.timeout = time.time() + run_timeout
        self.sleep = sleep
        self.max_retry = max_retry
        self.progress = progress

        if self.nb_workers is None:
            self.nb_workers = multiprocessing.cpu_count()

        mng = multiprocessing.Manager()

        if self.queue is None:
            self.queue = mng.Queue()

        if self.tasks is None:
            self.tasks = mng.dict()

        # set lock on tasks access
        self.lock = mng.RLock()

        if self.workers is None:
            self.workers = [
                Worker(
                    self.builder,
                    self.queue,
                    "worker-%d" % wid,
                    self.tasks,
                    max_retry,
                    self.lock,
                )
                for wid in range_type(self.nb_workers)
            ]

    def add(self, task):
        """Add task to manager

        Args:
            task (artron.task.Task): task object o add
            retry (bool): retry count
        """
        with self.lock:
            self.tasks[task.tid] = task

    # pylint: disable=too-many-branches,too-many-statements
    def start(self):
        """Start manager

        Returns:
            dict: run result in form.
                >>> {
                    'date_end': '2018-08-29T20:02:54.640Z',
                    'date_start': '2018-08-29T20:02:39.606Z',
                    'elapsed': '00:00:15',
                    'exit_code': 1,
                    'results': {
                        'aborted': 0,
                        'deps': 2,
                        'failures': 1,
                        'nrun': 0,
                        'ready': 0,
                        'success': 3
                    },
                    'tasks': [
                        {
                            'date_created': '2018-08-29T20:02:39.605Z',
                            'date_end': None,
                            'date_start': None,
                            'func': 'builder_func_1',
                            'inputs': {'msg': 'task-1-msg'},
                            'require': ['task-id-2', 'task-id-4'],
                            'results': None,
                            'state': -2,
                            'tid': 'task-id-1',
                            'time_duration': 0.0,
                            'time_duration_str': '00:00:00'
                        },{
                            'date_created': '2018-08-29T20:02:39.605Z',
                            'date_end': '2018-08-29T20:02:41.617Z',
                            'date_start': '2018-08-29T20:02:40.615Z',
                            'func': 'builder_func_3',
                            'inputs': {'msg': 'task-3-msg'},
                            'require': [],
                            'results': 'ERROR builder_func_3',
                            'state': -1,
                            'tid': 'task-id-3',
                            'time_duration': 1.0019969940185547,
                            'time_duration_str': '00:00:01'
                        }
                    ]
                }
        """
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
            LOGGER.debug("init %d workers", self.nb_workers)
            for worker in self.workers:
                worker.start()

            LOGGER.debug("send resources to queues")

            # generate exec graph
            graph = Graph(self.tasks)
            edges = list(graph.edges())
            LOGGER.debug("Edges %s", edges)

            # while we have non empty graph and don't reach timeout
            while edges and time.time() < self.timeout:
                # isolated vertice is task without deps
                for task_id in graph.isolated_vertices():

                    LOGGER.debug("isolated vertex task(%s) with state(%d)", \
                        task_id, self.tasks[task_id].state)

                    if self.tasks[task_id].is_runnable():
                        LOGGER.debug("send task(%s)", task_id)

                        # update task status because put in queue != is running
                        # so to avoid multiple queue send, mark it as running
                        with self.lock:
                            task_new = self.tasks[task_id]
                            task_new.state = Task.STATE_READY
                            self.tasks[task_id] = task_new

                        self.queue.put((task_id,))

                graph = Graph(self.tasks)
                edges = list(graph.edges())

                # LOGGER.debug("Task %s", self.tasks)
                LOGGER.debug("Edges %s", edges)

                if self.progress:
                    count = max(0, len([1 for task in self.tasks.values() \
                        if task.is_finished()]) - self.progress.n)
                    if count > 0:
                        self.progress.update(count)

                time.sleep(self.sleep)

            if self.progress:
                count = max(0, len([1 for task in self.tasks.values() \
                    if task.is_finished()]) - self.progress.n)
                if count > 0:
                    self.progress.update(count)

            if time.time() > self.timeout:
                raise TimeoutError('timeout error')

            LOGGER.debug("add end-of-queue markers")
            for _ in self.workers:
                # True add the end to mark the end of queue
                self.queue.put((None,))

            LOGGER.debug("blocks until all items in the queue have been "\
                  "gotten and processed.")
            self.queue.join()

            if self.progress:
                self.progress.close()

        # catch all errors
        # pylint: disable=broad-except
        except Exception as err:
            LOGGER.error("%s. Exiting...", err)

        # stop workers
        finally:
            LOGGER.debug("stop all workers")
            for worker in self.workers:
                # send sigterm
                worker.stop()
                # wait end
                worker.join()
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
