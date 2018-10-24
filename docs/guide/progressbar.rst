======================
Use Progress Bar
======================

Use TQDM
--------

Artron supports the awesome tqdm_.

.. _tqdm: https://github.com/tqdm/tqdm

.. code-block:: python

    # create manager
    manager = Manager(builder, max_retry=2)
    
    manager.progress = tqdm(total=len(manager.tasks))

See full example under `examples/basic_progress_tqdm.py <https://github.com/ahmet2mir/python-artron/tree/master/examples/basic_progress_tqdm.py>`_.


Use custom
----------

You could also use custom progress bar, but your object should have attributes **total** and **n**
where total is the progress bar size and n the counter.

And the object should implements methods **update** and **close**
where update draw with the size in parameters and close flush.

.. code-block:: python

    class ProgressBar(object):
        """Simple progress bar"""
        def __init__(self, total=100):
            self.total = total
            self.n = 0

        def update(self, count=1):
            if self.n == 0:
                sys.stdout.write("[%s]" % (" " * self.total))
                sys.stdout.flush()
                sys.stdout.write("\b" * (self.total+1))
            for _ in range(0, min(count, self.total-self.n)):
                sys.stdout.write("-")
                sys.stdout.flush()
            self.n += count

        def close(self):
            self.update(self.total - self.n)
            sys.stdout.write("\n")

See full example under `examples/basic_progress_custom.py <https://github.com/ahmet2mir/python-artron/tree/master/examples/basic_progress_custom.py>`_.


