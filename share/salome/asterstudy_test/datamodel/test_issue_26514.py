# -*- coding: utf-8 -*-

# Copyright 2018 EDF R&D
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

"""Automatic tests for command dependences within a stage."""


import unittest

from asterstudy.common import enable_autocopy
from asterstudy.datamodel.history import History
from hamcrest import *

def _define_commands(stage, order):
    "Utilitary function to define commands in some order"

    # commands are created in reversed order on purpose
    for i in range(3):
        if order[i] == 0:
            cmd1 = stage('LIRE_MAILLAGE', 'mesh')
            cmd1['UNITE'] = 20

        if order[i] == 1:
            cmd2 = stage('DEFI_MATERIAU', 'mat')
            fact2 = cmd2['ELAS']
            fact2['E'] = 30000.0
            fact2['NU'] = 0.2

        if order[i] == 2:
            cmd3 = stage('AFFE_MATERIAU', 'fieldmat')
            fact3 = cmd3['AFFE']
            fact3['TOUT'] = 'OUI'

    # Now that everything is created
    #     define links between commands
    cmd3['MAILLAGE'] = cmd1
    fact3['MATER'] = cmd2

    return

def _test_dependences(stage_a, stage_b):
    "Utilitary function to test the dependence of the commands on two stages"

    cmd1_a = stage_a['mesh']
    cmd2_a = stage_a['mat']
    cmd3_a = stage_a['fieldmat']

    cmd1_b = stage_b['mesh']
    cmd2_b = stage_b['mat']
    cmd3_b = stage_b['fieldmat']

    assert_that(cmd2_a, is_in(cmd3_a.parent_nodes))
    assert_that(cmd1_a, is_in(cmd3_a.parent_nodes))
    assert_that(cmd3_a, is_in(cmd2_a.child_nodes))
    assert_that(cmd3_a, is_in(cmd1_a.child_nodes))

    assert_that(cmd3_a['MAILLAGE']     , is_(cmd1_a))
    assert_that(cmd3_a['AFFE']['MATER'], is_(cmd2_a))

    assert_that(cmd1_b, is_in(cmd3_b.parent_nodes))
    assert_that(cmd2_b, is_in(cmd3_b.parent_nodes))
    assert_that(cmd3_b, is_in(cmd1_b.child_nodes))
    assert_that(cmd3_b, is_in(cmd2_b.child_nodes))

    assert_that(cmd3_b['MAILLAGE']     , is_(cmd1_b))
    assert_that(cmd3_b['AFFE']['MATER'], is_(cmd2_b))

    # No relation whatsoever between commands in different stages
    assert_that(cmd2_a, is_not(is_in(cmd3_b.parent_nodes)))
    assert_that(cmd1_a, is_not(is_in(cmd3_b.parent_nodes)))
    assert_that(cmd3_a, is_not(is_in(cmd2_b.child_nodes)))
    assert_that(cmd3_a, is_not(is_in(cmd1_b.child_nodes)))

    assert_that(cmd3_a['MAILLAGE']     , is_not(same_instance(cmd1_b)))
    assert_that(cmd3_a['AFFE']['MATER'], is_not(same_instance(cmd2_b)))

    assert_that(cmd2_b, is_not(is_in(cmd3_a.parent_nodes)))
    assert_that(cmd1_b, is_not(is_in(cmd3_a.parent_nodes)))
    assert_that(cmd3_b, is_not(is_in(cmd2_a.child_nodes)))
    assert_that(cmd3_b, is_not(is_in(cmd1_a.child_nodes)))

    assert_that(cmd3_b['MAILLAGE']     , is_not(same_instance(cmd1_a)))
    assert_that(cmd3_b['AFFE']['MATER'], is_not(same_instance(cmd2_a)))


def test_26514_1():
    """Test command dependence with child command copied first"""
    history = History()
    cc = history.current_case
    stage = cc.create_stage(':a:')

    # create commands in reversed order on purpose
    _define_commands(stage, (2, 1, 0))

    # create a first run case and pretend to execute it
    rc1 = history.create_run_case(exec_stages=[0]).run()

    # pretend to modify something in the current
    with enable_autocopy(cc):
        cc[':a:']['mat']['ELAS']['NU'] = 0.3

    # check commands still have the right relations
    _test_dependences(cc[':a:'], rc1[':a:'])

    # once again
    rc2 = history.create_run_case(exec_stages=[0]).run()
    with enable_autocopy(cc):
        cc[':a:']['mat']['ELAS']['NU'] = 0.25

    #
    _test_dependences(cc[':a:'] , rc1[':a:'])
    _test_dependences(cc[':a:'] , rc2[':a:'])
    _test_dependences(rc1[':a:'], rc2[':a:'])

def test_26514_2():
    """Test command dependence with parent commands copied first"""
    history = History()
    cc = history.current_case
    stage = cc.create_stage(':a:')

    # create commands in standard order
    _define_commands(stage, (0, 1, 2))

    # create a first run case and pretend to execute it
    rc1 = history.create_run_case(exec_stages=[0]).run()

    # pretend to modify something in the current
    with enable_autocopy(cc):
        cc[':a:']['mat']['ELAS']['NU'] = 0.3

    # check commands still have the right relations
    _test_dependences(cc[':a:'], rc1[':a:'])

    # once again
    rc2 = history.create_run_case(exec_stages=[0]).run()
    with enable_autocopy(cc):
        cc[':a:']['mat']['ELAS']['NU'] = 0.25

    #
    _test_dependences(cc[':a:'] , rc1[':a:'])
    _test_dependences(cc[':a:'] , rc2[':a:'])
    _test_dependences(rc1[':a:'], rc2[':a:'])

def test_26514_3():
    """Test command dependence with some parents copied first and others last"""
    history = History()
    cc = history.current_case
    stage = cc.create_stage(':a:')

    # create commands in standard order
    _define_commands(stage, (0, 2, 1))

    # create a first run case and pretend to execute it
    rc1 = history.create_run_case(exec_stages=[0]).run()

    # pretend to modify something in the current
    with enable_autocopy(cc):
        cc[':a:']['mat']['ELAS']['NU'] = 0.3

    # check commands still have the right relations
    _test_dependences(cc[':a:'], rc1[':a:'])

    # once again
    rc2 = history.create_run_case(exec_stages=[0]).run()
    with enable_autocopy(cc):
        cc[':a:']['mat']['ELAS']['NU'] = 0.25

    #
    _test_dependences(cc[':a:'] , rc1[':a:'])
    _test_dependences(cc[':a:'] , rc2[':a:'])
    _test_dependences(rc1[':a:'], rc2[':a:'])

if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
