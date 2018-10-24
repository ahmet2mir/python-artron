=======
Builder
=======

To work well Artron needs a class with all functions to run tasks.

Functions could be reusable and for that reason Artron doesn't mix the Task and the Builder.

Each functions should have multiple args but at least a ``retry`` because some functions could disallow retry and other not.

.. code-block:: python

    class MyAwesomeBuilder(object):
        
        def func_1(self, msg, retry):
            return "func_1: retry=%d msg=%s" % (retry, msg)

        def func_2(self, arg1, arg2, retry):
            if retry > 1:
                raise RuntimeError("func_2 shoudn't retry => retry %d!" % retry)
            return "func_2: retry=%d arg1=%s arg2=%s" % (retry, arg1, arg2)


In this example ``func_2`` doesn't support retry but func_1 supports.
