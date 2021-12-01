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
from testutils import attr

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study

#------------------------------------------------------------------------------
def test_command_validity():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    stage('LIRE_MAILLAGE', 'Mesh')
    assert_that(stage['Mesh'].check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    #--------------------------------------------------------------------------
    stage('MODI_MAILLAGE', 'Mod')
    assert_that(stage['Mod'].check(), equal_to(Validity.Syntaxic))
    assert_that(stage['Mesh'].check(), equal_to(Validity.Nothing))
    assert_that(stage.check(), equal_to(Validity.Syntaxic))
    assert_that(case.check(), equal_to(Validity.Syntaxic))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
