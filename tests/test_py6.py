
from artron import _py6

def test_int_types():
    _py6.PY2 = True
    assert isinstance(1, _py6.int_types)
    assert isinstance(-1, _py6.int_types)
    assert isinstance(23, _py6.int_types)
    assert not isinstance(.1, _py6.int_types)

def test_string_types():
    _py6.PY2 = True

    assert isinstance("hi", _py6.string_types)

    assert issubclass(_py6.text_type, _py6.string_types)

def test_range():
    _py6.PY2 = True

    assert list(_py6.range_type(1,2)) == [1]


def test_dict():
    _py6.PY2 = True

    assert list(_py6.iterkeys({1: 2})) == [1]
    assert list(_py6.itervalues({1: 2})) == [2]
    assert list(_py6.iteritems({1: 2})) == [(1, 2)]

def test_timeout():
    _py6.PY2 = True

    assert issubclass(_py6.TimeoutError, Exception)


def test_int_types3():
    _py6.PY2 = False
    assert isinstance(1, _py6.int_types)
    assert isinstance(-1, _py6.int_types)
    assert isinstance(23, _py6.int_types)
    assert not isinstance(.1, _py6.int_types)

def test_string_types3():
    _py6.PY2 = False

    assert isinstance("hi", _py6.string_types)

    assert issubclass(_py6.text_type, _py6.string_types)

def test_range3():
    _py6.PY2 = False

    assert list(_py6.range_type(1,2)) == [1]


def test_dict3():
    _py6.PY2 = False

    assert list(_py6.iterkeys({1: 2})) == [1]
    assert list(_py6.itervalues({1: 2})) == [2]
    assert list(_py6.iteritems({1: 2})) == [(1, 2)]

def test_timeout3():
    _py6.PY2 = False

    assert issubclass(_py6.TimeoutError, Exception)
