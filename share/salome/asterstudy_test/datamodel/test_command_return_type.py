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

from asterstudy.datamodel.general import ConversionLevel
from asterstudy.datamodel.history import History


def test():
    history = History()
    case = history.current_case

    stage = case.create_stage(':0:')

    # command without result
    command = stage('DEBUT')
    assert_that(command.gettype(), none())

    # returns a DataStructure object
    command = stage('AFFE_MODELE')
    assert_that(command.gettype(), not_none())

    # command with type computes by a function
    command = stage('CALC_GP')
    assert_that(command.gettype(), not_none())

    # check impact of user keywords on the returned type
    command = stage('CALC_GP')
    fact = command['TRANCHE_2D']
    # without ZONE_MAIL the command is invalid
    assert_that(command.gettype(ConversionLevel.NoFail), not_none())

    fact['ZONE_MAIL'] = 'NON'
    assert_that(command.gettype(), not_none())


def test_var():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    var = stage('_CONVERT_VARIABLE', 'a')
    var['EXPR'] = '(1., 2., 3.)'
    var.update(expression='(1., 2., 3.)')

    assert_that(var.gettype(), equal_to('R'))


def test_var_list():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    var = stage('_CONVERT_VARIABLE', 'a')
    expr = '[i for i in range(5)]'
    var['EXPR'] = expr
    var.update(expression=expr)

    assert_that(var.evaluation, has_length(5))
    assert_that(var.gettype(), equal_to('R'))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
