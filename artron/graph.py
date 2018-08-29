# -*- coding: utf-8 -*-
"""
artron.graph
~~~~~~~~~~~

artron graph management
"""
# local
from artron._py6 import iteritems, itervalues
from artron.task import Task

class Graph(dict):
    '''Graph extend dict'''
    def __init__(self, tasks):
        """Build oriented graph using edges.

        Parameters
        ----------
        tasks : dict
            Dict of Task object in form {task_id: task...}

        Example
        -------
        >>> from artron import Task, Graph
        >>>
        >>> task1 = Task('for_test-tid1', {'msg': 'hello1'}, 'for_test')
        >>> task2 = Task('for_test-tid2', {'msg': 'hello2'}, 'for_test')
        >>> task3 = Task('for_test-tid3', {'msg': 'hello3'}, 'for_test')
        >>> task4 = Task('for_test-tid4', {'msg': 'hello4'}, 'for_test')
        >>>
        >>> task1.add_require(task2.tid)
        >>> task1.add_require(task3.tid)
        >>> task1.add_require(task4.tid)
        >>> task2.add_require(task4.tid)
        >>>
        >>> tasks = {
        ...     task1.tid: task1,
        ...     task2.tid: task2,
        ...     task3.tid: task3,
        ...     task4.tid: task4
        ... }
        >>>
        >>> graph = Graph(tasks)
        >>> graph
        [
            ('for_test-tid1', 'for_test-tid2'),
            ('for_test-tid1', 'for_test-tid3'),
            ('for_test-tid1', 'for_test-tid4'),
            ('for_test-tid2', 'for_test-tid4'),
            ('for_test-tid3', 'for_test-tid3'),
            ('for_test-tid4', 'for_test-tid4')
        ]

        See also
        --------
        * http://www.python-course.eu/graphs_python.php
        """
        super(Graph, self).__init__()
        for edge in self.__generate_edges(tasks):

            if not edge[0] in self:
                self[edge[0]] = []

            if edge[1] and not edge[0] == edge[1]:
                self[edge[0]].append(edge[1])

    def __setitem__(self, key, value):
        if isinstance(value, list):
            super(Graph, self).__setitem__(key, value)
        else:
            raise ValueError("Value must be a list")

    def edges(self):
        """Generate oriented graph's edges

        Returns
        -------
        edges : generator
            Generator with a tuple of 2 vertices the edge ie. (A,B,)
            where A depends on B

        Example
        -------
        >>> list(graph.edges())
        [
            ('for_test-tid1', 'for_test-tid2'),
            ('for_test-tid1', 'for_test-tid3'),
            ('for_test-tid1', 'for_test-tid4'),
            ('for_test-tid2', 'for_test-tid4'),
            ('for_test-tid3', 'for_test-tid3'),
            ('for_test-tid4', 'for_test-tid4')
        ]
        """
        for vertex in self:
            if not self[vertex]:
                yield (vertex, vertex,)
            else:
                for neighbour in self[vertex]:
                    yield (vertex, neighbour,)

    def isolated_vertices(self):
        """Returns a list of isolated vertices (ie no dependency)

        Returns
        -------
        vertices : generator
            Generator with all isolated vertices.

        Example
        -------
        >>> graph
        [
            ('for_test-tid1', 'for_test-tid2'),
            ('for_test-tid1', 'for_test-tid3'),
            ('for_test-tid1', 'for_test-tid4'),
            ('for_test-tid2', 'for_test-tid4'),
            ('for_test-tid3', 'for_test-tid3'),
            ('for_test-tid4', 'for_test-tid4')
        ]
        >>> list(graph.isolated_vertices())
        ['for_test-tid4', 'for_test-tid3']
        """
        for key, value in iteritems(self):
            if not value:
                yield key

    def remove_vertex(self, vertex):
        """Remove vertex from graph and all childs."""
        del self[vertex]
        for value in itervalues(self):
            value.remove(vertex)

    @staticmethod
    def __generate_edges(tasks):
        """ The connecting line between two resource is called an edge.
        Edges are directed from one vertex to another, the graph is called
        a directed graph. This function is used to construct the graph.

        Parameters
        ----------
            tasks : dict
                tasks dict in form {task_id: task, ...}

        Returns
        -------
            edges : generator
                A generator with edges as tuple
        """
        for task in tasks.values():
            if task.state != Task.STATE_INIT:
                continue

            for neighbour in task.require:
                yield (task.tid, neighbour,)

            # isolated node
            if not task.require:
                yield (task.tid, task.tid,)
