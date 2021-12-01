# -*- coding: utf-8 -*-

# Copyright 2016-2018 EDF R&D
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

"""Automatic tests for variables support in DEFI_LIST command (issue 1852)."""


import unittest

from hamcrest import *
from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study

#------------------------------------------------------------------------------
def test():
    """Test for issue 1852"""
    history = History()
    cc = history.current_case
    stage = cc.create_stage(':1:')

    text = """
a = 1
b = 2
c = 3
d = 4
lst = DEFI_LIST_INST(DEFI_LIST=_F(VALE=(0, a, b, c, d, 6))) 
"""
    comm2study(text, stage)
    assert_that(stage, has_length(5))

    a = stage['a']
    b = stage['b']
    c = stage['c']
    d = stage['d']
    lst = stage['lst']
    vale = lst['DEFI_LIST']['VALE']
    assert_that(vale.value, has_length(6))
    assert_that(vale.value, equal_to((0, a, b, c, d, 6)))

    stage.use_text_mode()
    stage.use_graphical_mode()
    assert_that(stage, has_length(5))

    a = stage['a']
    b = stage['b']
    c = stage['c']
    d = stage['d']
    lst = stage['lst']
    vale = lst['DEFI_LIST']['VALE']
    assert_that(vale.value, has_length(6))
    assert_that(vale.value, equal_to((0, a, b, c, d, 6)))

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
