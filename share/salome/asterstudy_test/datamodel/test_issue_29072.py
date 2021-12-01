# -*- coding: utf-8 -*-

# Copyright 2016 - 2019 EDF R&D
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

"""Automatic tests for issue29072."""


import unittest

from asterstudy.datamodel import History, Validity
from hamcrest import *
from testutils import tempdir


@tempdir
def test_var_cmd(tmpdir):
    history = History()
    history.folder = tmpdir
    case = history.current_case
    stg1 = case.create_stage('st1')
    cmd1 = stg1.add_variable('cmd1', '1.0')

    stg2 = case.create_stage('st2')
    cmd2 = stg2('FORMULE', 'cmd2')
    cmd2.init({'NOM_PARA': 'INST', 'VALE': 'cmd1'})

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    rc1 = history.create_run_case(name='rc1')
    rc1.make_run_dir()
    rc1.run()

    # ensure to check objects from current case
    case = history.current_case
    cmd1 = case[0]['cmd1']
    cmd2 = case[1]['cmd2']

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    rc2 = history.create_run_case(name='rc2')
    rc2.make_run_dir()
    rc2.run()

    # ensure to check objects from current case
    case = history.current_case
    cmd1 = case[0]['cmd1']
    cmd2 = case[1]['cmd2']

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    rc1.delete()

    # ensure to check objects from current case
    case = history.current_case
    cmd1 = case[0]['cmd1']
    cmd2 = case[1]['cmd2']

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))


@tempdir
def test_cmd_cmd(tmpdir):
    history = History()
    history.folder = tmpdir
    case = history.current_case
    stg1 = case.create_stage('st1')
    cmd1 = stg1('DEFI_FONCTION', 'cmd1')
    cmd1.init({'NOM_PARA': 'X', 'VALE': (0., 1.)})

    stg2 = case.create_stage('st2')
    cmd2 = stg2('CALC_FONCTION', 'cmd2')
    cmd2.init({'ABS': {'FONCTION': cmd1}})

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    rc1 = history.create_run_case(name='rc1')
    rc1.make_run_dir()
    rc1.run()

    # ensure to check objects from current case
    case = history.current_case
    cmd1 = case[0]['cmd1']
    cmd2 = case[1]['cmd2']

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    rc2 = history.create_run_case(name='rc2')
    rc2.make_run_dir()
    rc2.run()

    # ensure to check objects from current case
    case = history.current_case
    cmd1 = case[0]['cmd1']
    cmd2 = case[1]['cmd2']

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    rc1.delete()

    # ensure to check objects from current case
    case = history.current_case
    cmd1 = case[0]['cmd1']
    cmd2 = case[1]['cmd2']

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))


@tempdir
def test_var_var(tmpdir):
    history = History()
    history.folder = tmpdir
    case = history.current_case
    stg1 = case.create_stage('st1')
    cmd1 = stg1.add_variable('cmd1', '1.0')

    stg2 = case.create_stage('st2')
    cmd2 = stg2.add_variable('cmd2', '1.0 * cmd1')

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    rc1 = history.create_run_case(name='rc1')
    rc1.make_run_dir()
    rc1.run()

    # ensure to check objects from current case
    case = history.current_case
    cmd1 = case[0]['cmd1']
    cmd2 = case[1]['cmd2']

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    rc2 = history.create_run_case(name='rc2')
    rc2.make_run_dir()
    rc2.run()

    # ensure to check objects from current case
    case = history.current_case
    cmd1 = case[0]['cmd1']
    cmd2 = case[1]['cmd2']

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    rc1.delete()

    # ensure to check objects from current case
    case = history.current_case
    cmd1 = case[0]['cmd1']
    cmd2 = case[1]['cmd2']

    assert_that(cmd2.depends_on(cmd1), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
