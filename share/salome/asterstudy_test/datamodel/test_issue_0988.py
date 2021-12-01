# -*- coding: utf-8 -*-

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

"""Miscellaneous test cases"""


import unittest
from hamcrest import *

from asterstudy.datamodel.history import History

#------------------------------------------------------------------------------
def test():
    #--------------------------------------------------------------------------
    history = History()
    assert_that(history.nodes, has_length(1))

    case = history.current_case
    assert_that(history.nodes, has_length(1))

    stage = case.create_stage(':memory:')
    assert_that(history.nodes, has_length(3))
    assert_that(stage.children, has_length(1))

    #--------------------------------------------------------------------------
    for i in range(3):
        stage.use_text_mode()
        assert_that(history.nodes, has_length(3))
        assert_that(stage.children, has_length(1))

        stage.use_graphical_mode()
        assert_that(history.nodes, has_length(3))
        assert_that(stage.children, has_length(1))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
