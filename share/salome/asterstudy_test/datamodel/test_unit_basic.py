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

"""Automatic tests for export feature."""


import unittest
from hamcrest import *
from testutils import attr

from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History

from testutils.tools import check_export, check_import

#------------------------------------------------------------------------------
def test_unit_value_check():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':0:')

    text = \
"""
table = LIRE_TABLE(UNITE=1)
"""
    comm2study(text, stage, strict=True)

    #--------------------------------------------------------------------------
    command = stage['table']
    assert_that(command['UNITE'], equal_to(1))

    # check syntax is valid
    assert_that(command.check(), equal_to(Validity.Nothing))

    #--------------------------------------------------------------------------
    value = {1: 'dummy.txt'}
    command['UNITE'] = value
    assert_that(command['UNITE'], equal_to(value))

    # check syntax is valid
    assert_that(command.check(), equal_to(Validity.Nothing))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_unit_value_pass():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':0:')

    #--------------------------------------------------------------------------
    unit = 1
    filename = 'dummy.txt'
    assert_that(stage.handle2info.get(unit), equal_to(None))

    #--------------------------------------------------------------------------
    command = stage('LIRE_TABLE', "tabl")
    command.init({'UNITE': {unit: filename}})
    assert_that(stage.handle2file(unit), equal_to(filename))

    keyword = command['UNITE']
    assert_that(keyword.value, equal_to(unit))
    assert_that(keyword.filename, equal_to(filename))
    assert_that(command.check(), equal_to(Validity.Nothing))

    #--------------------------------------------------------------------------
    command.init({'UNITE': {}})
    assert_that('UNITE', is_not(is_in(command.keys())))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
