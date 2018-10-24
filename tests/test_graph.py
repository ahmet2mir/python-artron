# -*- coding: utf-8 -*-
import six
import pytest

from artron.task import Task
from artron.graph import Graph


task1 = Task('for_test-tid1', {'msg': 'hello1'}, 'for_test')
task2 = Task('for_test-tid2', {'msg': 'hello2'}, 'for_test')
task3 = Task('for_test-tid3', {'msg': 'hello3'}, 'for_test')
task4 = Task('for_test-tid4', {'msg': 'hello4'}, 'for_test')

task1.add_require(task2.tid)
task1.add_require(task3.tid)
task1.add_require(task4.tid)
task2.add_require(task4.tid)

tasks = {
    task1.tid: task1,
    task2.tid: task2,
    task3.tid: task3,
    task4.tid: task4
}

graph = Graph(tasks)
output = {
    'for_test-tid4': [],
    'for_test-tid1': ['for_test-tid2', 'for_test-tid3', 'for_test-tid4'],
    'for_test-tid3': [],
    'for_test-tid2': ['for_test-tid4']
}


def test_init():
    assert sorted(graph) == sorted(output)


def test_set():
    graph["foo"] = ["bar"]
    assert graph["foo"] == ["bar"]
    with pytest.raises(ValueError):
        graph["foo"] = "bar"

def test_remove_vertex():
    graph.remove_vertex("foo")
    assert sorted(graph) == sorted(output)

    graph.remove_vertex("for_test-tid2")
    assert len(graph["for_test-tid1"]) == 2

    graph["for_test-tid2"] = ["for_test-tid4"]
    graph["for_test-tid1"].append("for_test-tid2")
    assert sorted(graph) == sorted(output)


def test_edges():
    edges = [
        ('for_test-tid1', 'for_test-tid2'),
        ('for_test-tid1', 'for_test-tid3'),
        ('for_test-tid1', 'for_test-tid4'),
        ('for_test-tid2', 'for_test-tid4'),
        ('for_test-tid3', 'for_test-tid3'),
        ('for_test-tid4', 'for_test-tid4')
    ]
    print(list(graph.edges()))
    assert sorted(edges) == sorted(list(graph.edges()))


def test_isolated_vertices():
    isolated_vertices = ['for_test-tid4', 'for_test-tid3']
    assert sorted(list(graph.isolated_vertices())) == sorted(isolated_vertices)


def test_generate_edges():
    task1.state = Task.STATE_READY

    graph = Graph(tasks)

    edges = [
        ('for_test-tid2', 'for_test-tid4'),
        ('for_test-tid3', 'for_test-tid3'),
        ('for_test-tid4', 'for_test-tid4')
    ]

    print(list(graph.edges()))
    assert sorted(edges) == sorted(list(graph.edges()))
