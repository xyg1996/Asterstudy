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

"""Data Model tests for
Pasting into the second stage when first stage is not empty"""


import unittest

from hamcrest import * # pragma pylint: disable=unused-import

from asterstudy.datamodel.history import History
from asterstudy.datamodel.general import Validity

#------------------------------------------------------------------------------
def test():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage = case.create_stage(':1:')

    stage.paste("a = 1")

    assert_that(stage, has_length(1))
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    stage = case.create_stage(':2:')

    stage.paste("b = a")

    assert_that(stage, has_length(1))
    assert_that(stage.check(), equal_to(Validity.Ok))

    assert_that(case, has_length(2))
    assert_that(case.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
