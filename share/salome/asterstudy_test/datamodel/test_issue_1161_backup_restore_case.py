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

"""Automatic tests for Feature #1161 -
History view: back-up/restore Current Case (CCTP 2.4.4)."""


import tempfile
import unittest

from asterstudy.common.utilities import enable_autocopy
from asterstudy.datamodel.history import History
from asterstudy.datamodel.result import RunOptions
from hamcrest import *
from testutils import tempdir
from testutils.tools import add_database, check_persistence

Skip = RunOptions.Skip
Reuse = RunOptions.Reuse
Execute = RunOptions.Execute

#------------------------------------------------------------------------------
def test_stage_modification():
    #--------------------------------------------------------------------------
    history = History()
    cc = history.current_case

    cc.create_stage('s1')
    cc.create_stage('s2')
    cc.create_stage('s3')

    #--------------------------------------------------------------------------
    backup = history.create_backup_case()
    assert_that(backup[0].uid, equal_to(cc[0].uid))
    assert_that(backup[1].uid, equal_to(cc[1].uid))
    assert_that(backup[2].uid, equal_to(cc[2].uid))

    with enable_autocopy(cc):
        cc[1].add_command('FIN')

    assert_that(backup[0].uid, equal_to(cc[0].uid))
    assert_that(backup[1].uid, is_not(equal_to(cc[1].uid)))
    assert_that(backup[2].uid, is_not(equal_to(cc[2].uid)))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_backup_naming():
    #--------------------------------------------------------------------------
    history = History()

    #--------------------------------------------------------------------------
    c0 = history.current_case
    c0.create_stage('s1')
    c0.create_stage('s2')

    rc1 = history.create_run_case().run()
    assert_that(rc1.name, 'RunCase_1')

    bc1 = history.create_backup_case()
    assert_that(bc1.name, 'BackupCase_1')

    bc2 = history.create_backup_case()
    assert_that(bc2.name, 'BackupCase_2')

    rc2 = history.create_run_case().run()
    assert_that(rc2.name, 'RunCase_2')

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
@tempdir
def test_backup(tmpdir):
    #--------------------------------------------------------------------------
    history = History()
    history.folder = tempfile.mkdtemp(dir=tmpdir, prefix='history-')
    c0 = history.current_case

    c0.name = 'c0'
    c0.create_stage('s1')
    c0.create_stage('s2')

    #--------------------------------------------------------------------------
    rc1 = history.create_run_case(name='rc1').run()
    add_database(rc1['s1'].folder)
    add_database(rc1['s2'].folder)
    assert_that(rc1[0].uid, equal_to(c0[0].uid))
    assert_that(rc1[1].uid, equal_to(c0[1].uid))

    #--------------------------------------------------------------------------
    c0 = history.current_case
    assert_that(rc1[0].uid, equal_to(c0[0].uid))
    assert_that(rc1[1].uid, equal_to(c0[1].uid))

    #--------------------------------------------------------------------------
    bc = history.create_backup_case('bc')
    assert_that(bc[0].uid, equal_to(c0[0].uid))
    assert_that(bc[1].uid, equal_to(c0[1].uid))

    assert_that(history.run_cases, has_length(1))
    assert_that(history.backup_cases, has_length(1))

    #--------------------------------------------------------------------------
    with enable_autocopy(c0):
        c0[0].add_command('FIN')

    assert_that(bc[0].uid, is_not(equal_to(c0[0].uid)))
    assert_that(bc[1].uid, is_not(equal_to(c0[1].uid)))

    assert_that(rc1[0].uid, is_not(equal_to(c0[0].uid)))
    assert_that(rc1[1].uid, is_not(equal_to(c0[1].uid)))

    assert_that(rc1[0].uid, equal_to(bc[0].uid))
    assert_that(rc1[1].uid, equal_to(bc[1].uid))

    #--------------------------------------------------------------------------
    c0.copy_from(bc)

    assert_that(c0.run_options(c0['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(c0.run_options(c0['s2']), equal_to(Skip | Reuse | Execute))

    assert_that(bc[0].uid, equal_to(c0[0].uid))
    assert_that(bc[1].uid, equal_to(c0[1].uid))

    assert_that(rc1[0].uid, equal_to(c0[0].uid))
    assert_that(rc1[1].uid, equal_to(c0[1].uid))

    assert_that(history.run_cases, has_length(1))
    assert_that(history.backup_cases, has_length(1))

    #--------------------------------------------------------------------------
    rc2 = history.create_run_case(exec_stages=[1], name='rc2').run()

    assert_that(rc2[0].uid, equal_to(c0[0].uid))
    assert_that(rc2[1].uid, equal_to(c0[1].uid))

    assert_that(rc1[0].uid, equal_to(c0[0].uid))

    assert_that(history.run_cases, has_length(2))
    assert_that(history.backup_cases, has_length(1))

    #--------------------------------------------------------------------------
    rc1.delete()

    assert_that(history.run_cases, has_length(0))
    assert_that(history.backup_cases, has_length(1))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_case_description():
    #--------------------------------------------------------------------------
    history = History()

    #--------------------------------------------------------------------------
    c0 = history.current_case
    assert_that(c0.description, equal_to(''))

    c0.description = 'xxx'
    assert_that(c0.description, equal_to('xxx'))

    c0.create_stage('s1')
    c0.create_stage('s2')

    #--------------------------------------------------------------------------
    rc1 = history.create_run_case()

    assert_that(rc1.description, equal_to(''))
    assert_that(c0.description, equal_to('xxx'))

    rc1.description = 'yyy'
    assert_that(rc1.description, equal_to('yyy'))

    #--------------------------------------------------------------------------
    bc1 = history.create_backup_case()
    assert_that(bc1.description, equal_to(''))
    assert_that(c0.description, equal_to('xxx'))
    assert_that(rc1.description, equal_to('yyy'))

    bc1.description = 'zzz'
    assert_that(bc1.description, equal_to('zzz'))

    #--------------------------------------------------------------------------
    c0.copy_from(bc1)
    assert_that(c0.description, equal_to('xxx'))

    #--------------------------------------------------------------------------
    c0.copy_from(rc1)
    assert_that(c0.description, equal_to('xxx'))

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
