# -*- coding: utf-8 -*-
import time
from datetime import datetime

import pytest

from artron import _py6
from artron import utils

def test_strgmtime():
     assert utils.strgmtime(time.gmtime(1.8)) == '00:00:01'
     assert utils.strgmtime(1.8) == '00:00:01'

     with pytest.raises(ValueError):
        utils.strgmtime("raise")


def test_strdate():
     assert isinstance(utils.strdate(datetime.utcnow()), _py6.string_types)
     assert isinstance(utils.strdate(), _py6.string_types)
     with pytest.raises(ValueError):
        utils.strdate("raise")
