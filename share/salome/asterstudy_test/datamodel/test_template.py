# -*- coding: utf-8 -*-

# Copyright 2016 - 2018 EDF R&D
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

"""Automatic tests for automatic naming of results."""


import os.path as osp
import unittest

from asterstudy.common import CFG
from asterstudy.common.template import BasicFormatter
from hamcrest import *
from testutils import attr


def test():
    engine = BasicFormatter()

    text = engine.format("key: {key} value: {value}",
                         key="x", value=1)
    assert_that(text, equal_to("key: x value: 1"))

    text = engine.format("key: {key} {value:repeat:value: {{item}} }",
                         key="x", value=[1, 2, 3])
    assert_that(text, equal_to("key: x value: 1 value: 2 value: 3 "))

    template = "there {sing:if:is}{pl:if:are} {nbv} item{pl:if:s}: {items}"
    values = list(range(1))
    nbv = len(values)
    text = engine.format(template,
                         items=values, nbv=nbv, sing=nbv <= 1, pl=nbv > 1)
    assert_that(text, equal_to("there is 1 item: [0]"))

    values = list(range(3))
    nbv = len(values)
    text = engine.format(template,
                         items=values, nbv=nbv, sing=nbv <= 1, pl=nbv > 1)
    assert_that(text, equal_to("there are 3 items: [0, 1, 2]"))


def test_yacs():
    with open(osp.join(CFG.rcdir, "yacs_schema.xml.template")) as tmpl:
        template = tmpl.read()

    engine = BasicFormatter()
    kwargs = {
        "schema": "Case Name",
        "code": "def _exec(a, b):\n    return a + b\n",
        "call": "res = _exec(a, b)",
        "invars": [("a", 0.), ("b", 1.)],
        "outvars": ["res"],
    }
    text = engine.format(template, **kwargs)
    assert_that(text, contains_string("return a + b"))
    assert_that(text.count("_exec(a, b)"), equal_to(2))
    assert_that(text, contains_string('<inport name="a" type="double"/>'))
    assert_that(text, contains_string('<inport name="b" type="double"/>'))
    assert_that(text, contains_string('<outport name="res" type="double"/>'))
    assert_that(text, contains_string('<tonode>Case Name</tonode><toport>a</toport>'))
    assert_that(text, contains_string('<tonode>Case Name</tonode><toport>b</toport>'))
    assert_that(text, contains_string('<value><double>0.0</double></value>'))
    assert_that(text, contains_string('<value><double>1.0</double></value>'))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
