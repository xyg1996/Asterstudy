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


import unittest

from hamcrest import * # pragma pylint: disable=unused-import
from testutils import attr

from asterstudy.common import CyclicDependencyError
from asterstudy.datamodel.history import History
from asterstudy.datamodel.command import Variable

#------------------------------------------------------------------------------
def test_same_named_variables():
    #--------------------------------------------------------------------------
    history = History()
    cc = history.current_case
    stage = cc.create_stage(':1:')

    #--------------------------------------------------------------------------
    assert_that(stage, has_length(0))

    #--------------------------------------------------------------------------
    stage.add_variable('a')
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to('a'))

    #--------------------------------------------------------------------------
    assert_that(calling(stage.add_variable).with_args('a'), raises(NameError))

    #--------------------------------------------------------------------------
    stage[0].name = 'b'
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to('b'))

    #--------------------------------------------------------------------------
    stage.add_variable('a')
    assert_that(stage, has_length(2))
    assert_that(stage[0].name, equal_to('b'))
    assert_that(stage[1].name, equal_to('a'))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_variables_reorder():
    #--------------------------------------------------------------------------
    history = History()
    cc = history.current_case
    stage = cc.create_stage(':1:')

    #--------------------------------------------------------------------------
    stage.add_variable('a')
    stage.add_variable('b')

    assert_that(stage, has_length(2))
    assert_that(stage[0].name, equal_to('a'))
    assert_that(stage[1].name, equal_to('b'))

    assert_that(stage[0].evaluation, none())
    assert_that(stage[1].evaluation, none())

    sorted_commands = stage.sorted_commands
    assert_that(sorted_commands[0].name, equal_to('a'))
    assert_that(sorted_commands[1].name, equal_to('b'))

    #--------------------------------------------------------------------------
    assert_that(stage['b'].update('10'), equal_to(10))
    assert_that(stage[0].evaluation, none())
    assert_that(stage[1].evaluation, equal_to(10))

    sorted_commands = stage.sorted_commands
    assert_that(sorted_commands[0].name, equal_to('a'))
    assert_that(sorted_commands[1].name, equal_to('b'))

    #--------------------------------------------------------------------------
    assert_that(stage['a'].update('b * 2'), equal_to(20))
    assert_that(stage[0].evaluation, equal_to(20))
    assert_that(stage[1].evaluation, equal_to(10))

    sorted_commands = stage.sorted_commands
    assert_that(sorted_commands[0].name, equal_to('a'))
    assert_that(sorted_commands[1].name, equal_to('b'))

    #--------------------------------------------------------------------------
    stage.reorder()
    assert_that(stage[0].evaluation, equal_to(20))
    assert_that(stage[1].evaluation, equal_to(10))

    sorted_commands = stage.sorted_commands
    assert_that(sorted_commands[0].name, equal_to('b'))
    assert_that(sorted_commands[1].name, equal_to('a'))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_variables_cyclic_dependencies():
    #--------------------------------------------------------------------------
    history = History()
    cc = history.current_case
    stage = cc.create_stage(':1:')

    #--------------------------------------------------------------------------
    stage.add_variable('a', '10')
    stage.add_variable('b', 'a * 2')
    stage.add_variable('c', 'b + 4')

    assert_that(stage, has_length(3))

    assert_that(stage['a'].evaluation, 10)
    assert_that(stage['b'].evaluation, 20)
    assert_that(stage['c'].evaluation, 24)

    #--------------------------------------------------------------------------
    assert_that(calling(stage['a'].update).with_args('c / 2'), raises(CyclicDependencyError))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_variable_context():
    #--------------------------------------------------------------------------
    history = History()
    cc = history.current_case
    stage1 = cc.create_stage(':1:')
    stage2 = cc.create_stage(':1:')

    #--------------------------------------------------------------------------
    assert_that('a', is_not(is_in(Variable.context(stage1))))

    #--------------------------------------------------------------------------
    stage1.add_variable('a', '10')

    assert_that('a', is_in(Variable.context(stage1)))
    assert_that('a', is_not(is_in(stage1['a'].current_context)))

    #--------------------------------------------------------------------------
    stage1.add_variable('b', '20')

    assert_that('a', is_in(Variable.context(stage1)))
    assert_that('b', is_in(Variable.context(stage1)))

    assert_that('a', is_not(is_in(stage1['a'].current_context)))
    assert_that('b', is_not(is_in(stage1['b'].current_context)))

    assert_that('a', is_in(stage1['b'].current_context))
    assert_that('b', is_in(stage1['a'].current_context))

    #--------------------------------------------------------------------------

    assert_that('a', is_in(Variable.context(stage2)))
    assert_that('b', is_in(Variable.context(stage2)))

    #--------------------------------------------------------------------------

    stage2.add_variable('c', '30')

    assert_that('a', is_in(Variable.context(stage2)))
    assert_that('b', is_in(Variable.context(stage2)))
    assert_that('c', is_in(Variable.context(stage2)))

    assert_that('c', is_not(is_in(stage1['a'].current_context)))
    assert_that('c', is_not(is_in(stage1['b'].current_context)))

    assert_that('a', is_in(stage2['c'].current_context))
    assert_that('b', is_in(stage2['c'].current_context))
    assert_that('c', is_not(is_in(stage2['c'].current_context)))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
