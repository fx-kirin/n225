#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import datetime
import logging
import os

import kanilog
import pytest
import stdlogging
from add_parent_path import add_parent_path

with add_parent_path():
    import n225


logger = kanilog.get_module_logger(__file__, 0)


def setup_module(module):
    pass


def teardown_module(module):
    pass


def setup_function(function):
    pass


def teardown_function(function):
    pass


def test_func():
    today = datetime.date(2020, 11, 10)
    n225.get_compositions(today)
    n225.get_all_stock_codes()


if __name__ == "__main__":
    kanilog.setup_logger(logfile='/tmp/%s.log' % (os.path.basename(__file__)), level=logging.INFO)

    pytest.main([__file__, '-k test_', '-s'])
