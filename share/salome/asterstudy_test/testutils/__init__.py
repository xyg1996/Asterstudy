# coding=utf-8

# Copyright 2016 EDF R&D
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License Version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, you may download a copy of license
# from https://www.gnu.org/licenses/gpl-3.0.

"""Auxiliary utilities for testing purposes."""


import os.path as osp
import shutil
import sys
import tempfile
import types
import unittest
from functools import wraps


def attr(*args, **kwargs):
    """
    Decorator that adds attributes to classes or functions
    for use with the Attribute (-a) plugin.

    Note:
        This function is copied from nose.plugins.attrib.py.
    """
    def wrap_ob(ob):
        for name in args:
            setattr(ob, name, True)
        for name, value in kwargs.items():
            setattr(ob, name, value)
        return ob
    return wrap_ob


def get_test_suite(module_name):
    """Create test cases for all test functions in the given module."""
    module = sys.modules[module_name]
    functions = [obj for name, obj in module.__dict__.items() \
                     if isinstance(obj, types.FunctionType) \
                     and name.startswith("test")]
    cases = [obj for name, obj in module.__dict__.items() if \
                 isinstance(obj, type) and issubclass(obj, unittest.TestCase)]
    loader = unittest.loader.defaultTestLoader
    cases = [loader.loadTestsFromTestCase(c) for c in cases]
    suite = unittest.TestSuite([unittest.FunctionTestCase(func)
                                for func in functions] + cases)
    return suite


def tempdir(func):
    """Execute the function in a temporary directory."""
    idx = getattr(tempdir, 'idx', 0) + 1
    tempdir.idx = idx

    @wraps(func)
    def wrapper(*args, **kwds):
        """wrapper"""
        retcode = None
        try:
            tmpdir = tempfile.mkdtemp(prefix='asterstudy-test{0:06d}-'
                                      .format(idx))
            retcode = func(tmpdir, *args, **kwds)
        except Exception:
            sys.stderr.write("temporary directory is: {0}\n".format(tmpdir))
            raise
        else:
            if osp.exists(tmpdir):
                shutil.rmtree(tmpdir)
        return retcode
    return wrapper

def dummy_render(func):
    """Deactivate the render when Salome is in text mode"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """wrapper."""
        try:
            import pvsimple as pvs
            import salome
            if not salome.hasDesktop():
                pvs.Render = lambda *args1, **kwargs1: None
        except ImportError:
            pass
        return func(*args, **kwargs)
    return wrapper
