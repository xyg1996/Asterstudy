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

"""Data Model tests for 'Manage variables (CCTP 2.2.1.3)' functionality"""


import unittest

from hamcrest import * # pragma pylint: disable=unused-import
from testutils import attr

from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.command import Variable
from asterstudy.datamodel.general import Validity

from testutils.tools import check_export, check_import
from testutils.tools import check_persistence

#------------------------------------------------------------------------------
def test_from_text():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
vitesse = 1.e-5
t_0 = 5.e-2 / (8.0 * vitesse)
c1 = DEFI_CONSTANTE(VALE=t_0)
"""
    stage = case.create_stage(':1:')

    comm2study(text, stage)

    assert_that(stage, has_length(3))
    assert_that(stage.check(), equal_to(Validity.Ok))

    var = stage['vitesse']
    assert_that(var.name, equal_to('vitesse'))
    assert_that(var.expression, equal_to('1.e-5'))
    assert_that(var.evaluation, equal_to(1.e-5))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_via_api():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')
    assert_that(Variable.context(stage), Variable.initial_context())

    #--------------------------------------------------------------------------
    var = stage.add_variable('vitesse', '1.e-5')
    assert_that(var.current_context, Variable.initial_context())
    assert_that(Variable.context(stage).keys(), has_item('vitesse'))

    assert_that(var.name, equal_to('vitesse'))
    assert_that(var.expression, equal_to('1.e-5'))
    assert_that(var.evaluation, equal_to(1.e-5))

    #--------------------------------------------------------------------------
    var = stage.add_variable('t_0', '5.e-2 / (8.0 * vitesse)')
    assert_that(var.current_context.keys(), has_item('vitesse'))
    assert_that(Variable.context(stage).keys(), has_items('t_0', 'vitesse'))
    assert_that(stage['t_0'].depends_on(stage['vitesse']), equal_to(True))

    assert_that(var.name, equal_to('t_0'))
    assert_that(var.expression, equal_to('5.e-2 / (8.0 * vitesse)'))
    assert_that(var.evaluation, equal_to(625.0))

    #--------------------------------------------------------------------------
    cmd = stage.add_command('DEFI_CONSTANTE', 'c1')
    cmd['VALE'] = stage['t_0']

    assert_that(stage['c1'].depends_on(stage['t_0']), equal_to(True))
    assert_that(stage['c1'].depends_on(stage['vitesse']), equal_to(True))

    #--------------------------------------------------------------------------
    text = \
"""
vitesse = 1.e-5

t_0 = 5.e-2 / (8.0 * vitesse)

c1 = DEFI_CONSTANTE(VALE=t_0)
"""
    assert(check_export(stage, text))

    assert(check_import(text))

    #--------------------------------------------------------------------------
    stage = case.create_stage(':2:')
    var = stage.add_variable('t_2', 't_0 + 375')
    assert_that(var.current_context.keys(), has_items('vitesse', 't_0'))
    assert_that(Variable.context(stage).keys(), has_items('t_2', 't_0', 'vitesse'))

    assert_that(stage['t_2'].depends_on(case[':1:']['t_0']), equal_to(True))

    assert_that(var.name, equal_to('t_2'))
    assert_that(var.expression, equal_to('t_0 + 375'))
    assert_that(var.evaluation, equal_to(1000))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_update_variable():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    var = stage.add_variable('vitesse')

    assert_that(var.name, equal_to('vitesse'))
    assert_that(var.expression, equal_to(''))
    assert_that(var.evaluation, equal_to(None))

    var.update('1.e-5')
    assert_that(var.expression, equal_to('1.e-5'))
    assert_that(var.evaluation, equal_to(1.e-5))

    #--------------------------------------------------------------------------
    var = stage.add_variable('t_1')

    assert_that(var.name, equal_to('t_1'))
    assert_that(var.expression, equal_to(''))
    assert_that(var.evaluation, equal_to(None))

    var.update('5.e-2 / (8.0 * vitesse)', 't_0')

    assert_that(var.name, equal_to('t_0'))
    assert_that(var.expression, equal_to('5.e-2 / (8.0 * vitesse)'))
    assert_that(var.evaluation, equal_to(625.0))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_dependencies_update():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    stage.add_variable('vitesse', '1.e-5')
    stage.add_variable('t_0', '5.e-2 / (8.0 * vitesse)')

    assert_that(stage['t_0'].depends_on(stage['vitesse']), equal_to(True))
    assert_that(stage['vitesse'].depends_on(stage['t_0']), equal_to(False))

    #--------------------------------------------------------------------------
    stage['t_0'].update('625.0')

    assert_that(stage['t_0'].depends_on(stage['vitesse']), equal_to(False))
    assert_that(stage['vitesse'].depends_on(stage['t_0']), equal_to(False))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_dependencies_modification():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    stage.add_variable('vitesse', '1.e-5')
    stage.add_variable('t_0', '5.e-2 / (8.0 * vitesse)')

    assert_that(stage['t_0'].depends_on(stage['vitesse']), equal_to(True))
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    # Reseting 'vitesse' variable
    assert_that(stage['vitesse'].update(''), equal_to(None))
    assert_that(stage.check(), equal_to(Validity.Syntaxic))

    # Recalculating 't_0' variable (it can be properly evaluated - become None)
    assert_that(stage['t_0'].evaluation, equal_to(None))

    # Dependendcy is still in place
    assert_that(stage['t_0'].depends_on(stage['vitesse']), equal_to(True))

    #--------------------------------------------------------------------------
    # Restoring initial value
    assert_that(stage['vitesse'].update('1.e-5'), equal_to(1.e-5))
    assert_that(stage.check(), equal_to(Validity.Ok))

    # Recalculating 't_0' variable
    assert_that(stage['t_0'].evaluation, equal_to(625.0))

    # Dependendcy is still in place
    assert_that(stage['t_0'].depends_on(stage['vitesse']), equal_to(True))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_invalid_expression():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    stage.add_variable('vitesse', '@ % ^ &')
    assert_that(stage['vitesse'].evaluation, equal_to(None))
    assert_that(stage.check(), equal_to(Validity.Syntaxic))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_name_modification():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    assert_that(stage.add_variable('a', '1').evaluation, equal_to(1))

    assert_that(stage.add_variable('b', 'a + 1').evaluation, equal_to(2))
    assert_that(stage['b'].depends_on(stage['a']), equal_to(True))

    assert_that(stage.add_variable('c', '2 * a').evaluation, equal_to(2))
    assert_that(stage['c'].depends_on(stage['a']), equal_to(True))
    assert_that(stage['c'].depends_on(stage['b']), equal_to(False))

    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    stage['b'].rename('a')
    assert_that(stage['a'].evaluation, equal_to(2))
    assert_that(stage[1].depends_on(stage[0]), equal_to(True))

    assert_that(stage['c'].evaluation, equal_to(4))
    assert_that(stage[2].depends_on(stage[1]), equal_to(True))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_auto_update_on_renaming():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    assert_that(stage.add_variable('a', '1').evaluation, equal_to(1))

    assert_that(stage.add_variable('b', 'a + 1').evaluation, equal_to(2))
    assert_that(stage['b'].depends_on(stage['a']), equal_to(True))

    stage.add_variable('d', '3')

    assert_that(stage.add_variable('c', '2 * b').evaluation, equal_to(4))
    assert_that(stage['c'].depends_on(stage['a']), equal_to(True))
    assert_that(stage['c'].depends_on(stage['b']), equal_to(True))

    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    stage['b'].name = 'a'
    assert_that(stage['a'].evaluation, equal_to(2))
    assert_that(stage['a'].depends_on(stage[0]), equal_to(True))
    assert_that(stage.check(), equal_to(Validity.Syntaxic | Validity.Naming))

    stage['d'].name = 'b'
    assert_that(stage['b'].evaluation, equal_to(3))
    assert_that(stage.check(), equal_to(Validity.Naming))

    assert_that(stage['c'].evaluation, equal_to(6))
    assert_that(stage['c'].depends_on(stage[0]), equal_to(False))
    assert_that(stage['c'].depends_on(stage[1]), equal_to(False))
    assert_that(stage['c'].depends_on(stage[2]), equal_to(True))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
@attr('deprecated')
def test_auto_update_on_deletion():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    assert_that(stage.add_variable('a', '1').evaluation, equal_to(1))

    assert_that(stage.add_variable('a', '2').evaluation, equal_to(2))

    stage = case.create_stage(':2:')
    assert_that(stage.add_variable('b', 'a*2').evaluation, equal_to(4))
    assert_that(case[':2:']['b'].depends_on(case[':1:'][0]), equal_to(False))
    assert_that(case[':2:']['b'].depends_on(case[':1:'][1]), equal_to(True))

    del case[':1:'][1]

    assert_that(case[':2:']['b'].evaluation, equal_to(2))
    assert_that(case[':2:']['b'].depends_on(stage[0]), equal_to(True))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
