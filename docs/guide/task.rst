====
Task
====

Tasks are simple objects wrapping builder functions with inputs and outputs 
management, dependency between tasks and run status.

.. code-block:: python

    from artron.task import Task

    task1 = Task(
        tid='task-id-1',
        inputs={'msg': 'task-msg'},
        func='func_1'
    )
    task2 = Task(
        tid='task-id-2',
        inputs={'arg1': 'value-1', 'arg2': 'value-2'},
        func='func_2',
        require=['func_1']
    )

    # or dependency could be added later
    
    task2.add_require(task1.tid)
