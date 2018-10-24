# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import time
from pprint import pprint

from tqdm import tqdm

from artron.task import Task
from artron.manager import Manager


class Builder(object):
    
    def builder_func_1(self, msg, retry):
        time.sleep(2)
        return "builder_func_1 ==> " + msg

    def builder_func_2(self, msg, retry):
        time.sleep(3)
        return "builder_func_2 ==> " + msg

    def builder_func_3(self, msg, retry):
        time.sleep(1)
        raise Exception("ERROR builder_func_3")
        return "builder_func_3 ==> " + msg

    def builder_func_4(self, msg, retry):
        time.sleep(1)
        return "builder_func_4 ==> " + msg


def process():
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

    # set progress bar
    manager.progress = tqdm(total=len(manager.tasks))

    # start
    results = manager.start()
    pprint(results)
    sys.exit(results['exit_code'])


if __name__ == '__main__':
    process()
