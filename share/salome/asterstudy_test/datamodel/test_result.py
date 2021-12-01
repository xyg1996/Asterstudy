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

"""Automatic tests for general services."""


import os
import os.path as osp
import shutil
import tempfile
import unittest

from asterstudy.common import CFG, enable_autocopy
from asterstudy.datamodel.history import History
from asterstudy.datamodel.result import RunOptions, StateOptions
from hamcrest import *
from testutils import attr, tempdir
from testutils.tools import add_database, add_file

Skip = RunOptions.Skip
Reuse = RunOptions.Reuse
Execute = RunOptions.Execute

Waiting = StateOptions.Waiting
Success = StateOptions.Success
Error = StateOptions.Error
Intermediate = StateOptions.Intermediate


#------------------------------------------------------------------------------
@tempdir
def test_result_state(tmpdir):
    """Test for result state"""
    #--------------------------------------------------------------------------
    history = History()
    history.folder = tempfile.mkdtemp(dir=tmpdir, prefix='history-')
    cc = history.current_case

    cc.create_stage('s1')
    cc.create_stage('s2')
    cc.create_stage('s3')

    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Execute))
    assert_that(cc.run_options(0), equal_to(Skip | Execute))
    assert_that(cc.run_options(1), equal_to(Skip | Execute))
    assert_that(cc.run_options(2), equal_to(Skip | Execute))

    #--------------------------------------------------------------------------
    rc1 = history.create_run_case(reusable_stages=range(3))
    assert_that(rc1['s1'].state, equal_to(Waiting))
    assert_that(rc1['s2'].state, equal_to(Waiting))
    assert_that(rc1['s3'].state, equal_to(Waiting))
    assert_that(rc1['s1'].parent_case, equal_to(rc1))
    assert_that(rc1['s2'].parent_case, equal_to(rc1))
    assert_that(rc1['s3'].parent_case, equal_to(rc1))

    #--------------------------------------------------------------------------
    rc1.rename('Test_RunCase')
    assert_that(rc1.name, equal_to('Test_RunCase'))

    #--------------------------------------------------------------------------
    rc1.run()
    add_database(rc1['s1'].folder)
    add_database(rc1['s2'].folder)
    add_database(rc1['s3'].folder)
    assert_that(rc1['s1'].state, equal_to(Success))
    assert_that(rc1['s2'].state, equal_to(Success))
    assert_that(rc1['s3'].state, equal_to(Success))

    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Execute | Reuse))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Execute | Reuse))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Execute | Reuse))

    # test representation
    result = rc1['s1'].result
    assert_that(repr(result), equal_to('Result-s1 <Success>'))
    result.state = Success | StateOptions.Warn
    assert_that(repr(result), equal_to('Result-s1 <Success+Warn>'))
    result.state = StateOptions.Error | StateOptions.Nook
    assert_that(repr(result), equal_to('Result-s1 <Error+Nook>'))
    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_file_descriptors():
    """Test for file descriptors keeping in run case"""
    #--------------------------------------------------------------------------
    history = History()
    cc = history.current_case

    cc.create_stage('s1')
    assert_that(cc['s1'].is_graphical_mode(), equal_to(True))

    cc['s1']('PRE_GMSH').init({'UNITE_GMSH': {1: 'gmsh.file'}})
    assert_that(1, is_in(cc['s1'].handle2info))
    assert_that(cc['s1'].handle2file(1), equal_to('gmsh.file'))

    assert_that(2, is_not(is_in(cc['s1'].handle2info)))
    assert_that(cc['s1'].handle2file(2), none())

    cc.create_stage('s2')
    cc['s2']('PRE_GMSH').init({'UNITE_GMSH': {1: 'gmsh.file'}})
    assert_that(1, is_in(cc['s2'].handle2info))
    assert_that(cc['s2'].handle2file(1), equal_to('gmsh.file'))

    cc['s2'].use_text_mode()
    assert_that(1, is_in(cc['s2'].handle2info))
    assert_that(cc['s2'].handle2file(1), equal_to('gmsh.file'))

    #--------------------------------------------------------------------------
    rc1 = history.create_run_case(name='rc1').run()

    assert_that(1, is_in(rc1['s1'].handle2info))
    assert_that(rc1['s1'].handle2file(1), equal_to('gmsh.file'))

    assert_that(1, is_in(rc1['s2'].handle2info))
    assert_that(rc1['s2'].handle2file(1), equal_to('gmsh.file'))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
@tempdir
def test_history_compare(tmpdir):
    """Test for histories comparison"""
    #--------------------------------------------------------------------------
    history = History()
    assert_that(history.folder, equal_to(None))

    #--------------------------------------------------------------------------
    history2 = History()
    assert_that(history * history2, none())

    #--------------------------------------------------------------------------
    history.folder = tmpdir
    assert_that(history.folder, equal_to(tmpdir))
    assert_that(calling(history.__mul__).with_args(history2), raises(AssertionError))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_result_compare():
    """Test for results comparison"""
    #--------------------------------------------------------------------------
    history = History()
    cc = history.current_case
    cc.create_stage('stage')

    #--------------------------------------------------------------------------
    rc1 = history.create_run_case(name="rc")
    rc2 = history.create_run_case(name="rc")

    s1 = rc1['stage']
    s2 = rc2['stage']
    assert_that(s1 * s2, none())

    r1 = s1.result
    r2 = s2.result
    assert_that(r1 * r2, none())

    assert_that(rc1 * rc2, none())
    assert_that(rc1, is_not(equal_to(rc2)))

    #--------------------------------------------------------------------------
    rc1['stage'].state = Success
    assert_that(calling(r1.__mul__).with_args(r2), raises(AssertionError))
    assert_that(calling(s1.__mul__).with_args(s2), raises(AssertionError))
    assert_that(calling(rc1.__mul__).with_args(rc2), raises(AssertionError))

    #--------------------------------------------------------------------------
    rc3 = history.create_run_case(name="rc")
    assert_that(rc2 * rc3, none())

    rc3.run()
    assert_that(calling(rc2.__mul__).with_args(rc3), raises(AssertionError))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
@tempdir
def test_use_case(tmpdir):
    """Test for real use case"""
    #--------------------------------------------------------------------------
    # Step 1: fill in Current Case (CC)
    #
    # CC=RC1
    #
    #  X
    #  |
    #  X
    #  |
    #  X

    history = History()
    history.folder = tempfile.mkdtemp(dir=tmpdir, prefix='history-')
    cc = history.current_case
    cc.name = 'c1'

    cc.create_stage('s1')
    cc.create_stage('s2')
    cc.create_stage('s3')

    # check

    #: History: nb of run cases = 0
    def _check_history(_run_cases):
        assert_that(history.run_cases, equal_to(_run_cases))
        assert_that(history.cases, equal_to(_run_cases + [cc]))
        assert_that(history.current_case, equal_to(cc))
        for _run_case in _run_cases:
            assert_that(history.current_case, is_not(equal_to(_run_case)))
    _check_history([])

    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can NOT reuse result for s1, s2, s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(False))
    assert_that(cc.can_reuse(cc['s2']), equal_to(False))
    assert_that(cc.can_reuse(cc['s3']), equal_to(False))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Execute))

    #--------------------------------------------------------------------------
    # Step 2: create run case RC1: execute s1, s2, s3
    #
    # RC1      CC=RC1
    #
    #  0         0
    #  |         |
    #  0         0
    #  |         |
    #  0         0

    rc1 = history.create_run_case(name='rc1', reusable_stages=[0, 1, 2]).run()
    add_database(rc1['s1'].folder)
    add_database(rc1['s2'].folder)
    add_database(rc1['s3'].folder)

    # check

    #: History: nb of run cases = 1
    _check_history([rc1])

    def _check_step1():
        #: RC1: nb of stages = 3
        assert_that(rc1.nb_stages, equal_to(3))
        #: RC1: results of s1, s2, s3 are OK
        assert_that(rc1['s1'].state, equal_to(Success))
        assert_that(rc1['s2'].state, equal_to(Success))
        assert_that(rc1['s3'].state, equal_to(Success))
        #: RC1: ref case of results for s1, s2, s3 is RC1
        assert_that(rc1['s1'].parent_case, equal_to(rc1))
        assert_that(rc1['s2'].parent_case, equal_to(rc1))
        assert_that(rc1['s3'].parent_case, equal_to(rc1))
        #: RC1: result's parent stage comes from RC1
        assert_that(rc1['s1'].result.stage, equal_to(rc1['s1']))
        assert_that(rc1['s2'].result.stage, equal_to(rc1['s2']))
        assert_that(rc1['s3'].result.stage, equal_to(rc1['s3']))
    _check_step1()

    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1, s2, s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Reuse | Execute))
    #: CC shares s1, s2, s3 from RC1
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, equal_to(Success))
    assert_that(cc['s1'], equal_to(rc1['s1']))
    assert_that(cc['s2'], equal_to(rc1['s2']))
    assert_that(cc['s3'], equal_to(rc1['s3']))
    assert_that(cc['s1'].result.stage, equal_to(rc1['s1']))
    assert_that(cc['s2'].result.stage, equal_to(rc1['s2']))
    assert_that(cc['s3'].result.stage, equal_to(rc1['s3']))
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s3'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc1, cc]))
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc1, cc]))
    assert_that(cc['s3'].result.used_in_cases, equal_to([rc1, cc]))

    #--------------------------------------------------------------------------
    # Step 3: create run case RC2: reuse s1, s2; execute s3
    #
    # RC1  RC2    CC=RC2
    #
    #  0            0
    #  |            |
    #  0---         0
    #  |   \        |
    #  O    0       0

    rc2 = history.create_run_case(2, reusable_stages=2, name='rc2').run()
    add_database(rc2['s3'].folder)

    # check

    #: History: nb of run cases = 2
    _check_history([rc1, rc2])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    def _check_step2():
        #: RC2: nb of stages = 3
        assert_that(rc2.nb_stages, equal_to(3))
        #: RC2: results of s1, s2, s3 are OK
        assert_that(rc2['s1'].state, equal_to(Success))
        assert_that(rc2['s2'].state, equal_to(Success))
        assert_that(rc2['s3'].state, equal_to(Success))
        #: RC2: ref case of results for s1, s2 is RC1; for s3 is RC2
        assert_that(rc2['s1'].parent_case, equal_to(rc1))
        assert_that(rc2['s2'].parent_case, equal_to(rc1))
        assert_that(rc2['s3'].parent_case, equal_to(rc2))
        #: RC2: stages s1, s2 are re-used from RC1, but not s3
        assert_that(rc2['s1'], equal_to(rc1['s1']))
        assert_that(rc2['s2'], equal_to(rc1['s2']))
        assert_that(rc2['s3'], is_not(equal_to(rc1['s3'])))
        #: RC2: result's parent stage comes from RC1 for s1, s2 and from RC2 for s3
        assert_that(rc2['s1'].result.stage, equal_to(rc2['s1']))
        assert_that(rc2['s1'].result.stage, equal_to(rc1['s1']))
        assert_that(rc2['s2'].result.stage, equal_to(rc2['s2']))
        assert_that(rc2['s2'].result.stage, equal_to(rc1['s2']))
        assert_that(rc2['s3'].result.stage, equal_to(rc2['s3']))
        assert_that(rc2['s3'].result.stage, is_not(equal_to(rc1['s3'])))
    _check_step2()

    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1, s2, s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Reuse | Execute))
    #: CC shares s1, s2, s3 from RC2
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, equal_to(Success))
    assert_that(cc['s1'], equal_to(rc2['s1']))
    assert_that(cc['s2'], equal_to(rc2['s2']))
    assert_that(cc['s3'], equal_to(rc2['s3']))
    assert_that(cc['s1'].result.stage, equal_to(rc2['s1']))
    assert_that(cc['s2'].result.stage, equal_to(rc2['s2']))
    assert_that(cc['s3'].result.stage, equal_to(rc2['s3']))
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s3'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc1, rc2, cc]))
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc1, rc2, cc]))
    assert_that(cc['s3'].result.used_in_cases, equal_to([rc2, cc]))

    #--------------------------------------------------------------------------
    # Step 4: create run case RC3: reuse s1; execute s2, s3
    #
    # RC1  RC2  RC3    CC=RC3
    #
    #  0--------         0
    #  |        \        |
    #  O---      0       0
    #  |   \     |       |
    #  O    O    0       0

    rc3 = history.create_run_case((1, 2), reusable_stages=(1, 2),
                                  name='rc3').run()
    add_database(rc3['s2'].folder)
    add_database(rc3['s3'].folder)

    # check

    #: History: nb of run cases = 3
    _check_history([rc1, rc2, rc3])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    def _check_step3():
        #: RC3: nb of stages = 3
        assert_that(rc3.nb_stages, equal_to(3))
        #: RC3: results of s1, s2, s3 are OK
        assert_that(rc3['s1'].state, equal_to(Success))
        assert_that(rc3['s2'].state, equal_to(Success))
        assert_that(rc3['s3'].state, equal_to(Success))
        #: RC3: ref case of results for s1 is RC1; for s2, s3 is RC2
        assert_that(rc3['s1'].parent_case, equal_to(rc1))
        assert_that(rc3['s2'].parent_case, equal_to(rc3))
        assert_that(rc3['s3'].parent_case, equal_to(rc3))
        #: RC3: stage s1 is re-used from RC1 (and RC2), but not s2, s3
        assert_that(rc3['s1'], equal_to(rc1['s1']))
        assert_that(rc3['s1'], equal_to(rc2['s1']))
        assert_that(rc3['s2'], is_not(equal_to(rc1['s2'])))
        assert_that(rc3['s2'], is_not(equal_to(rc2['s2'])))
        assert_that(rc3['s3'], is_not(equal_to(rc1['s3'])))
        assert_that(rc3['s3'], is_not(equal_to(rc2['s3'])))
        #: RC3: result's parent stage comes from RC1 for s1 and from RC2 for s2, s3
        assert_that(rc3['s1'].result.stage, equal_to(rc3['s1']))
        assert_that(rc3['s1'].result.stage, equal_to(rc2['s1']))
        assert_that(rc3['s1'].result.stage, equal_to(rc1['s1']))
        assert_that(rc3['s2'].result.stage, equal_to(rc3['s2']))
        assert_that(rc3['s2'].result.stage, is_not(equal_to(rc2['s2'])))
        assert_that(rc3['s2'].result.stage, is_not(equal_to(rc1['s2'])))
        assert_that(rc3['s3'].result.stage, equal_to(rc3['s3']))
        assert_that(rc3['s3'].result.stage, is_not(equal_to(rc2['s3'])))
        assert_that(rc3['s3'].result.stage, is_not(equal_to(rc1['s3'])))
    _check_step3()

    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1, s2, s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Reuse | Execute))
    #: CC shares s1, s2, s3 from RC3
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, equal_to(Success))
    assert_that(cc['s1'], equal_to(rc3['s1']))
    assert_that(cc['s2'], equal_to(rc3['s2']))
    assert_that(cc['s3'], equal_to(rc3['s3']))
    assert_that(cc['s1'].result.stage, equal_to(rc3['s1']))
    assert_that(cc['s2'].result.stage, equal_to(rc3['s2']))
    assert_that(cc['s3'].result.stage, equal_to(rc3['s3']))
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s3'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc1, rc2, rc3, cc]))
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc3, cc]))
    assert_that(cc['s3'].result.used_in_cases, equal_to([rc3, cc]))

    #--------------------------------------------------------------------------
    # Step 5: create run case RC4: reuse s1, s2; execute s3
    #
    # RC1  RC2  RC3  RC4    CC=RC4
    #
    #  0--------              0
    #  |        \             |
    #  O---      0---         0
    #  |   \     |   \        |
    #  O    O    O    0       0

    rc4 = history.create_run_case(2, reusable_stages=2, name='rc4').run()
    add_database(rc4['s3'].folder)

    # check

    #: History: nb of run cases = 4
    _check_history([rc1, rc2, rc3, rc4])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    def _check_step4():
        #: RC4: nb of stages = 3
        assert_that(rc4.nb_stages, equal_to(3))
        #: RC4: results of s1, s2, s3 are OK
        assert_that(rc4['s1'].state, equal_to(Success))
        assert_that(rc4['s2'].state, equal_to(Success))
        assert_that(rc4['s3'].state, equal_to(Success))
        #: RC4: ref case of results for s1 is RC1; for s2 is RC3, for s3 is RC4
        assert_that(rc4['s1'].parent_case, equal_to(rc1))
        assert_that(rc4['s2'].parent_case, equal_to(rc3))
        assert_that(rc4['s3'].parent_case, equal_to(rc4))
        #: RC4: stage s1 is re-used from RC1 (and RC2, RC3), s2 is reused from RC3, but not s3
        assert_that(rc4['s1'], equal_to(rc1['s1']))
        assert_that(rc4['s1'], equal_to(rc2['s1']))
        assert_that(rc4['s1'], equal_to(rc3['s1']))
        assert_that(rc4['s2'], is_not(equal_to(rc1['s2'])))
        assert_that(rc4['s2'], is_not(equal_to(rc2['s2'])))
        assert_that(rc4['s2'], equal_to(rc3['s2']))
        assert_that(rc4['s3'], is_not(equal_to(rc1['s3'])))
        assert_that(rc4['s3'], is_not(equal_to(rc2['s3'])))
        assert_that(rc4['s3'], is_not(equal_to(rc3['s3'])))
        #: RC4: result's parent stage comes from RC1 for s1, from RC3 for s2 and from RC4 for s3
        assert_that(rc4['s1'].result.stage, equal_to(rc4['s1']))
        assert_that(rc4['s1'].result.stage, equal_to(rc3['s1']))
        assert_that(rc4['s1'].result.stage, equal_to(rc2['s1']))
        assert_that(rc4['s1'].result.stage, equal_to(rc1['s1']))
        assert_that(rc4['s2'].result.stage, equal_to(rc4['s2']))
        assert_that(rc4['s2'].result.stage, equal_to(rc3['s2']))
        assert_that(rc4['s2'].result.stage, is_not(equal_to(rc2['s2'])))
        assert_that(rc4['s2'].result.stage, is_not(equal_to(rc1['s2'])))
        assert_that(rc4['s3'].result.stage, equal_to(rc4['s3']))
        assert_that(rc4['s3'].result.stage, is_not(equal_to(rc3['s3'])))
        assert_that(rc4['s3'].result.stage, is_not(equal_to(rc2['s3'])))
        assert_that(rc4['s3'].result.stage, is_not(equal_to(rc1['s3'])))
    _check_step4()

    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1, s2, s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Reuse | Execute))
    #: CC shares s1, s2, s3 from RC4
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, equal_to(Success))
    assert_that(cc['s1'], equal_to(rc4['s1']))
    assert_that(cc['s2'], equal_to(rc4['s2']))
    assert_that(cc['s3'], equal_to(rc4['s3']))
    assert_that(cc['s1'].result.stage, equal_to(rc4['s1']))
    assert_that(cc['s2'].result.stage, equal_to(rc4['s2']))
    assert_that(cc['s3'].result.stage, equal_to(rc4['s3']))
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s3'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc1, rc2, rc3, rc4, cc]))
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc3, rc4, cc]))
    assert_that(cc['s3'].result.used_in_cases, equal_to([rc4, cc]))

    #--------------------------------------------------------------------------
    # Step 6: create run case RC5: execute s1, s2, omit s3
    #
    # RC1  RC2  RC3  RC4  RC5    CC=RC5
    #
    #  O--------           0       0
    #  |        \          |       |
    #  O---      O---      0       0
    #  |   \     |   \             |
    #  O    O    O    O            X

    rc5 = history.create_run_case((0, 1), reusable_stages=(0, 1),
                                  name='rc5').run()
    add_database(rc5['s1'].folder)
    add_database(rc5['s2'].folder)

    # check

    #: History: nb of run cases = 5
    _check_history([rc1, rc2, rc3, rc4, rc5])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    def _check_step5():
        #: RC5: nb of stages = 2
        assert_that(rc5.nb_stages, equal_to(2))
        #: RC5: results of s1, s2 are OK
        assert_that(rc5['s1'].state, equal_to(Success))
        assert_that(rc5['s2'].state, equal_to(Success))
        #: RC5: ref case of results for s1, s2 is RC5
        assert_that(rc5['s1'].parent_case, equal_to(rc5))
        assert_that(rc5['s2'].parent_case, equal_to(rc5))
        #: RC5: stages s1, s2 are not re-used from previous run cases
        assert_that(rc5['s1'], is_not(equal_to(rc1['s1'])))
        assert_that(rc5['s1'], is_not(equal_to(rc2['s1'])))
        assert_that(rc5['s1'], is_not(equal_to(rc3['s1'])))
        assert_that(rc5['s1'], is_not(equal_to(rc4['s1'])))
        assert_that(rc5['s2'], is_not(equal_to(rc1['s2'])))
        assert_that(rc5['s2'], is_not(equal_to(rc2['s2'])))
        assert_that(rc5['s2'], is_not(equal_to(rc3['s2'])))
        assert_that(rc5['s2'], is_not(equal_to(rc4['s2'])))
        #: RC5: result's parent stage comes from RC5
        assert_that(rc5['s1'].result.stage, equal_to(rc5['s1']))
        assert_that(rc5['s1'].result.stage, is_not(equal_to(rc4['s1'])))
        assert_that(rc5['s1'].result.stage, is_not(equal_to(rc3['s1'])))
        assert_that(rc5['s1'].result.stage, is_not(equal_to(rc2['s1'])))
        assert_that(rc5['s1'].result.stage, is_not(equal_to(rc1['s1'])))
        assert_that(rc5['s2'].result.stage, equal_to(rc5['s2']))
        assert_that(rc5['s2'].result.stage, is_not(equal_to(rc4['s2'])))
        assert_that(rc5['s2'].result.stage, is_not(equal_to(rc3['s2'])))
        assert_that(rc5['s2'].result.stage, is_not(equal_to(rc2['s2'])))
        assert_that(rc5['s2'].result.stage, is_not(equal_to(rc1['s2'])))
    _check_step5()

    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1, s2; can NOT reuse result for s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(False))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Execute))
    #: CC shares s1, s2 from RC5, but not s3
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, is_not(equal_to(Success)))
    assert_that(cc['s1'], equal_to(rc5['s1']))
    assert_that(cc['s2'], equal_to(rc5['s2']))
    assert_that(cc['s3'], is_not(is_in([rc1['s3'], rc2['s3'], rc3['s3'], rc4['s3']]))) # !!!
    assert_that(cc['s1'].result.stage, equal_to(rc5['s1']))
    assert_that(cc['s2'].result.stage, equal_to(rc5['s2']))
    assert_that(cc['s3'].result.stage, equal_to(cc['s3'])) # !!!
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s3'].parent_case, equal_to(cc)) # !!!
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc5, cc]))
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc5, cc]))
    assert_that(cc['s3'].result.used_in_cases, equal_to([cc])) # !!!

    #--------------------------------------------------------------------------
    # Step 7: copy run case RC1 as Current Case
    #
    # RC1  RC2  RC3  RC4  RC5    CC=RC1
    #
    #  0--------           O       0
    #  |        \          |       |
    #  0---      O---      O       0
    #  |   \     |   \             |
    #  0    O    O    O            0

    cc.copy_from(rc1)

    # check

    #: History: nb of run cases = 5 (same as before)
    _check_history([rc1, rc2, rc3, rc4, rc5])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: RC5: all results are the same as after Step 6
    _check_step5()

    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1, s2, s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Reuse | Execute))
    #: CC shares s1, s2, s3 from RC1
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, equal_to(Success))
    assert_that(cc['s1'], equal_to(rc1['s1']))
    assert_that(cc['s2'], equal_to(rc1['s2']))
    assert_that(cc['s3'], equal_to(rc1['s3']))
    assert_that(cc['s1'].result.stage, equal_to(rc1['s1']))
    assert_that(cc['s2'].result.stage, equal_to(rc1['s2']))
    assert_that(cc['s3'].result.stage, equal_to(rc1['s3']))
    assert_that(cc['s1'].parent_case, equal_to(rc1))
    assert_that(cc['s2'].parent_case, equal_to(rc1))
    assert_that(cc['s3'].parent_case, equal_to(rc1))
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s3'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc1, rc2, rc3, rc4, cc]))
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc1, rc2, cc]))
    assert_that(cc['s3'].result.used_in_cases, equal_to([rc1, cc]))

    #--------------------------------------------------------------------------
    # Step 8: create run case RC6: reuse s1, s2; execute s3
    #
    # RC1  RC2  RC3  RC4  RC5  RC6    CC=RC6
    #
    #  0--------           O            0
    #  |        \          |            |
    #  0-----(1) O---      O (1)        0
    #  |   \     |   \         \        |
    #  O    O    O    O         0       0

    rc6 = history.create_run_case(2, reusable_stages=2, name='rc6').run()
    add_database(rc6['s3'].folder)

    # check

    #: History: nb of run cases = 6
    _check_history([rc1, rc2, rc3, rc4, rc5, rc6])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: RC5: all results are the same as after Step 6
    _check_step5()

    def _check_step6():
        #: RC6: nb of stages = 3
        assert_that(rc6.nb_stages, equal_to(3))
        #: RC6: results of s1, s2, s3 are OK
        assert_that(rc6['s1'].state, equal_to(Success))
        assert_that(rc6['s2'].state, equal_to(Success))
        assert_that(rc6['s3'].state, equal_to(Success))
        #: RC6: ref case of results for s1, s2 is RC1; for s3 is RC6
        assert_that(rc6['s1'].parent_case, equal_to(rc1))
        assert_that(rc6['s2'].parent_case, equal_to(rc1))
        assert_that(rc6['s3'].parent_case, equal_to(rc6))
        #: RC6: stages s1 ose re-used from RC1 (and RC2, RC3, RC4), s2 is reused from RC1 (and RC2), but not s3
        assert_that(rc6['s1'], equal_to(rc1['s1']))
        assert_that(rc6['s1'], equal_to(rc2['s1']))
        assert_that(rc6['s1'], equal_to(rc3['s1']))
        assert_that(rc6['s1'], equal_to(rc4['s1']))
        assert_that(rc6['s1'], is_not(equal_to(rc5['s1'])))
        assert_that(rc6['s2'], equal_to(rc1['s2']))
        assert_that(rc6['s2'], equal_to(rc2['s2']))
        assert_that(rc6['s2'], is_not(equal_to(rc3['s2'])))
        assert_that(rc6['s2'], is_not(equal_to(rc4['s2'])))
        assert_that(rc6['s2'], is_not(equal_to(rc5['s2'])))
        assert_that(rc6['s3'], is_not(equal_to(rc1['s3'])))
        assert_that(rc6['s3'], is_not(equal_to(rc2['s3'])))
        assert_that(rc6['s3'], is_not(equal_to(rc3['s3'])))
        assert_that(rc6['s3'], is_not(equal_to(rc4['s3'])))
        #: RC6: result's parent stage comes from RC1 for s1, s2 and from RC6 for s3
        assert_that(rc6['s1'].result.stage, equal_to(rc6['s1']))
        assert_that(rc6['s1'].result.stage, is_not(equal_to(rc5['s1'])))
        assert_that(rc6['s1'].result.stage, equal_to(rc4['s1']))
        assert_that(rc6['s1'].result.stage, equal_to(rc3['s1']))
        assert_that(rc6['s1'].result.stage, equal_to(rc2['s1']))
        assert_that(rc6['s1'].result.stage, equal_to(rc1['s1']))
        assert_that(rc6['s2'].result.stage, equal_to(rc6['s2']))
        assert_that(rc6['s2'].result.stage, is_not(equal_to(rc5['s2'])))
        assert_that(rc6['s2'].result.stage, is_not(equal_to(rc4['s2'])))
        assert_that(rc6['s2'].result.stage, is_not(equal_to(rc3['s2'])))
        assert_that(rc6['s2'].result.stage, equal_to(rc2['s2']))
        assert_that(rc6['s2'].result.stage, equal_to(rc1['s2']))
        assert_that(rc6['s3'].result.stage, equal_to(rc6['s3']))
        assert_that(rc6['s3'].result.stage, is_not(equal_to(rc4['s3'])))
        assert_that(rc6['s3'].result.stage, is_not(equal_to(rc3['s3'])))
        assert_that(rc6['s3'].result.stage, is_not(equal_to(rc2['s3'])))
        assert_that(rc6['s3'].result.stage, is_not(equal_to(rc1['s3'])))
    _check_step6()

    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1, s2, s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Reuse | Execute))
    #: CC shares s1, s2, s3 from RC6
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, equal_to(Success))
    assert_that(cc['s1'], equal_to(rc6['s1']))
    assert_that(cc['s2'], equal_to(rc6['s2']))
    assert_that(cc['s3'], equal_to(rc6['s3']))
    assert_that(cc['s1'].result.stage, equal_to(rc6['s1']))
    assert_that(cc['s2'].result.stage, equal_to(rc6['s2']))
    assert_that(cc['s3'].result.stage, equal_to(rc6['s3']))
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s3'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc1, rc2, rc3, rc4, rc6, cc]))
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc1, rc2, rc6, cc]))
    assert_that(cc['s3'].result.used_in_cases, equal_to([rc6, cc]))

    #--------------------------------------------------------------------------
    # Step 9: remove run case RC6
    #
    # RC1  RC2  RC3  RC4  RC5    CC=?
    #
    #  O---------          O       0
    #  |         \         |       |
    #  O---      O---      O       0
    #  |   \     |   \             |
    #  O    O    O   O             X

    assert_that(rc6.is_used_by_others(), equal_to(False))
    rc6.delete()

    # check

    #: History: nb of run cases = 5
    _check_history([rc1, rc2, rc3, rc4, rc5])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: RC5: all results are the same as aft1er Step 6
    _check_step5()

    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1, s2; can NOT reuse result for s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(False))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Execute))
    #: CC shares s1, s2 somehow from other Run Cases (RC1!), but not s3 !!!
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, is_not(equal_to(Success)))
    assert_that(cc['s1'], equal_to(rc1['s1']))
    assert_that(cc['s2'], equal_to(rc1['s2']))
    assert_that(cc['s3'], is_not(is_in([rc1['s3'], rc2['s3'], rc3['s3'], rc4['s3']]))) # !!!
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s3'].parent_case, equal_to(cc)) # !!!
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc1, rc2, rc3, rc4, cc])) # !!!
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc1, rc2, cc])) # !!!
    assert_that(cc['s3'].result.used_in_cases, equal_to([cc])) # !!!

    #--------------------------------------------------------------------------
    # Step 10: copy run case RC1 as Current Case
    #
    # RC1  RC2  RC3  RC4  RC5    CC=RC1
    #
    #  0---------          O       0
    #  |         \         |       |
    #  0---      O---      O       0
    #  |   \     |   \             |
    #  0    O    O   O             0

    cc.copy_from(rc1)

    # check

    #: History: nb of run cases = 5 (same as before)
    _check_history([rc1, rc2, rc3, rc4, rc5])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: RC5: all results are the same as after Step 6
    _check_step5()

    #: CC: result is the same as after Step 7
    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1, s2, s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Reuse | Execute))
    #: CC shares s1, s2, s3 from RC1
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, equal_to(Success))
    assert_that(cc['s1'], equal_to(rc1['s1']))
    assert_that(cc['s2'], equal_to(rc1['s2']))
    assert_that(cc['s3'], equal_to(rc1['s3']))
    assert_that(cc['s1'].result.stage, equal_to(rc1['s1']))
    assert_that(cc['s2'].result.stage, equal_to(rc1['s2']))
    assert_that(cc['s3'].result.stage, equal_to(rc1['s3']))
    assert_that(cc['s1'].parent_case, equal_to(rc1))
    assert_that(cc['s2'].parent_case, equal_to(rc1))
    assert_that(cc['s3'].parent_case, equal_to(rc1))
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s3'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc1, rc2, rc3, rc4, cc]))
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc1, rc2, cc]))
    assert_that(cc['s3'].result.used_in_cases, equal_to([rc1, cc]))

    #--------------------------------------------------------------------------
    # Step 11: modify s2 of Current Case (simulate edition operation)
    #
    # RC1  RC2  RC3  RC4  RC5    CC=?
    #
    #  0--------           O       0
    #  |        \          |       |
    #  O---      O---      O       X
    #  |   \     |   \             |
    #  O    O    O    O            X

    # The following simulates an edition to stage 2
    with enable_autocopy(cc):
        cc['s2'].rename('s2')
    #cc.modify(cc['s2'])

    # check

    #: History: nb of run cases = 5 (same as before)
    _check_history([rc1, rc2, rc3, rc4, rc5])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: RC5: all results are the same as after Step 6
    _check_step5()

    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1; can NOT reuse result for s2, s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(False))
    assert_that(cc.can_reuse(cc['s3']), equal_to(False))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Execute))
    #: CC shares s1 somehow from other Run Cases, but not s2, s3 !!!
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, is_not(equal_to(Success)))
    assert_that(cc['s3'].state, is_not(equal_to(Success)))
    assert_that(cc['s1'], equal_to(rc1['s1']))
    assert_that(cc['s2'], is_not(is_in([rc1['s2'], rc2['s2'], rc3['s2'], rc4['s2'], rc5['s2']]))) # !!!
    assert_that(cc['s3'], is_not(is_in([rc1['s3'], rc2['s3'], rc3['s3'], rc4['s3']]))) # !!!
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, equal_to(cc)) # !!!
    assert_that(cc['s3'].parent_case, equal_to(cc)) # !!!
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc1, rc2, rc3, rc4, cc])) # !!!
    assert_that(cc['s2'].result.used_in_cases, equal_to([cc])) # !!!
    assert_that(cc['s3'].result.used_in_cases, equal_to([cc])) # !!!

    #--------------------------------------------------------------------------
    # Step 12: copy run case RC5 as Current Case
    #
    # RC1  RC2  RC3  RC4  RC5    CC=RC5
    #
    #  O--------           0       0
    #  |        \          |       |
    #  O---      O---      0       0
    #  |   \     |   \
    #  O    O    O    O

    cc.copy_from(rc5)

    # check

    #: History: nb of run cases = 5 (same as before)
    _check_history([rc1, rc2, rc3, rc4, rc5])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: RC5: all results are the same as after Step 6
    _check_step5()

    #: CC: nb of stages = 2 !!!
    assert_that(cc.nb_stages, equal_to(2))
    #: CC: can reuse result for s1, s2
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    #: CC shares s1, s2 from RC5
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s1'], equal_to(rc5['s1']))
    assert_that(cc['s2'], equal_to(rc5['s2']))
    assert_that(cc['s1'].result.stage, equal_to(rc5['s1']))
    assert_that(cc['s2'].result.stage, equal_to(rc5['s2']))
    assert_that(cc['s1'].parent_case, equal_to(rc5))
    assert_that(cc['s2'].parent_case, equal_to(rc5))
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc5, cc]))
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc5, cc]))

    #--------------------------------------------------------------------------
    # Step 13: remove run case RC5
    #
    # RC1  RC2  RC3  RC4    CC=?
    #
    #  O--------              X
    #  |        \             |
    #  O---      O---         X
    #  |   \     |   \
    #  O    O    O    O

    assert_that(rc5.is_used_by_others(), equal_to(False))
    rc5.delete()

    # check

    #: History: nb of run cases = 4
    _check_history([rc1, rc2, rc3, rc4])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: CC: nb of stages = 2
    assert_that(cc.nb_stages, equal_to(2))
    #: CC: can NOT reuse result for s1, s2
    assert_that(cc.can_reuse(cc['s1']), equal_to(False))
    assert_that(cc.can_reuse(cc['s2']), equal_to(False))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Execute))
    #: CC does not reuse result from any Run Case !!!
    assert_that(cc['s1'].state, is_not(equal_to(Success)))
    assert_that(cc['s2'].state, is_not(equal_to(Success)))
    assert_that(cc['s1'], is_not(is_in([rc1['s1'], rc2['s1'], rc3['s1'], rc4['s1']]))) # !!!
    assert_that(cc['s2'], is_not(is_in([rc1['s2'], rc2['s2'], rc3['s2'], rc4['s2']]))) # !!!
    assert_that(cc['s1'].parent_case, equal_to(cc)) # !!!
    assert_that(cc['s2'].parent_case, equal_to(cc)) # !!!
    assert_that(cc['s1'].result.used_in_cases, equal_to([cc])) # !!!
    assert_that(cc['s2'].result.used_in_cases, equal_to([cc])) # !!!

    #--------------------------------------------------------------------------
    # Step 14: create case C2 as Current Case: keep previous Current Case
    # (note: C1 is previous CC)
    #
    # RC1  RC2  RC3  RC4  C1    CC=?
    #
    #  O--------           O
    #  |        \          |
    #  O---      O---      O
    #  |   \     |   \
    #  O    O    O    O

    c1 = history.current_case
    cc = history.create_case('c2')

    # check

    #: History: nb of run cases = 5
    _check_history([rc1, rc2, rc3, rc4, c1])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: C1 (previous Current Case)
    def _check_step14():
        #: C1: nb of stages = 2
        assert_that(c1.nb_stages, equal_to(2))
        #: C1: results of s1, s2 are KO
        assert_that(c1['s1'].state, is_not(equal_to(Success)))
        assert_that(c1['s2'].state, is_not(equal_to(Success)))
        #: C1: ref case of results for s1, s2 is RC1; for s3 is RC6
        assert_that(c1['s1'].parent_case, equal_to(c1))
        assert_that(c1['s2'].parent_case, equal_to(c1))
        #: C1: stages s1, s2 are not re-used from any Run Case
        assert_that(c1['s1'], is_not(is_in([rc1['s1'], rc2['s1'], rc3['s1'], rc4['s1']])))
        assert_that(c1['s2'], is_not(is_in([rc1['s2'], rc2['s2'], rc3['s2'], rc4['s2']])))
        #: C1: result's parent stage comes from C1 for s1, s2
        assert_that(c1['s1'].result.stage, equal_to(c1['s1']))
        assert_that(c1['s2'].result.stage, equal_to(c1['s2']))
    _check_step14()

    #: CC: nb of stages = 0
    assert_that(cc.nb_stages, equal_to(0))

    #--------------------------------------------------------------------------
    # Step 15: create case C2 as Current Case: replace previous Current Case
    #
    # RC1  RC2  RC3  RC4  C1    CC=?
    #
    #  O--------           O
    #  |        \          |
    #  O---      O---      O
    #  |   \     |   \
    #  O    O    O    O

    c2 = history.current_case
    cc = history.create_case('c3', replace=True)

    # check

    #: History: nb of run cases = 5
    _check_history([rc1, rc2, rc3, rc4, c1])
    assert_that(history.current_case, is_not(equal_to(c2)))

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: C1: all results are the same as after Step 14
    _check_step14()

    #: CC: nb of stages = 0
    assert_that(cc.nb_stages, equal_to(0))

    #--------------------------------------------------------------------------
    # Step 16: Modify Current Case: add stage
    #
    # RC1  RC2  RC3  RC4  C1    CC=?
    #
    #  O--------           O     X
    #  |        \          |
    #  O---      O---      O
    #  |   \     |   \
    #  O    O    O    O

    cc.create_stage('s1')

    # check

    #: History: nb of run cases = 5 (same as before)
    _check_history([rc1, rc2, rc3, rc4, c1])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: C1: all results are the same as after Step 14
    _check_step14()

    #: CC: nb of stages = 1
    assert_that(cc.nb_stages, equal_to(1))
    #: CC: can reuse result for s1, s2
    assert_that(cc.can_reuse(cc['s1']), equal_to(False))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Execute))
    assert_that(cc['s1'], is_not(is_in([rc1['s1'], rc2['s1'], rc3['s1'], rc4['s1'], c1['s1']])))

    #--------------------------------------------------------------------------
    # Step 17: copy run case RC1 as Current Case
    #
    # RC1  RC2  RC3  RC4  C1    CC=RC1
    #
    #  0---------          O       0
    #  |         \         |       |
    #  0---      O---      O       0
    #  |   \     |   \             |
    #  0    O    O   O             0

    cc.copy_from(rc1)

    # check

    #: History: nb of run cases = 5
    _check_history([rc1, rc2, rc3, rc4, c1])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: C1: all results are the same as after Step 14
    _check_step14()

    #: CC: result is the same as after Step 7
    #: CC: nb of stages = 3
    assert_that(cc.nb_stages, equal_to(3))
    #: CC: can reuse result for s1, s2, s3
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Reuse | Execute))
    #: CC shares s1, s2, s3 from RC1
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, equal_to(Success))
    assert_that(cc['s1'], equal_to(rc1['s1']))
    assert_that(cc['s2'], equal_to(rc1['s2']))
    assert_that(cc['s3'], equal_to(rc1['s3']))
    assert_that(cc['s1'].result.stage, equal_to(rc1['s1']))
    assert_that(cc['s2'].result.stage, equal_to(rc1['s2']))
    assert_that(cc['s3'].result.stage, equal_to(rc1['s3']))
    assert_that(cc['s1'].parent_case, equal_to(rc1))
    assert_that(cc['s2'].parent_case, equal_to(rc1))
    assert_that(cc['s3'].parent_case, equal_to(rc1))
    assert_that(cc['s1'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s2'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s3'].parent_case, is_not(equal_to(cc)))
    assert_that(cc['s1'].result.used_in_cases, equal_to([rc1, rc2, rc3, rc4, cc]))
    assert_that(cc['s2'].result.used_in_cases, equal_to([rc1, rc2, cc]))
    assert_that(cc['s3'].result.used_in_cases, equal_to([rc1, cc]))

    #--------------------------------------------------------------------------
    # Step 18: Modify Current Case: add stage
    #
    # RC1  RC2  RC3  RC4  C1    CC=RC1
    #
    #  0---------          O       0
    #  |         \         |       |
    #  0---      O---      O       0
    #  |   \     |   \             |
    #  0    O    O   O             0
    #                              |
    #                              X

    cc.create_stage('s4')

    # check

    #: History: nb of run cases = 5
    _check_history([rc1, rc2, rc3, rc4, c1])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: C1: all results are the same as after Step 14
    _check_step14()

    #: CC: nb of stages = 4
    assert_that(cc.nb_stages, equal_to(4))
    #: CC: can reuse result for s1, s2, s3; can NOT reuse result for s4
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.can_reuse(cc['s3']), equal_to(True))
    assert_that(cc.can_reuse(cc['s4']), equal_to(False))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s3']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s4']), equal_to(Skip | Execute))
    #: CC shares s1, s2, s3 from RC1
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, equal_to(Success))
    assert_that(cc['s4'].state, is_not(equal_to(Success)))

    #--------------------------------------------------------------------------
    # Step 19: Modify Current Case: remove stage
    #
    # RC1  RC2  RC3  RC4  C1    CC=?
    #
    #  0---------          O       0
    #  |         \         |       |
    #  0---      O---      O       0
    #  |   \     |   \
    #  O    O    O   O

    cc.detach(cc['s3'])

    # check

    #: History: nb of run cases = 5
    _check_history([rc1, rc2, rc3, rc4, c1])

    #: RC1: all results are the same as after Step 2
    _check_step1()

    #: RC2: all results are the same as after Step 3
    _check_step2()

    #: RC3: all results are the same as after Step 4
    _check_step3()

    #: RC4: all results are the same as after Step 5
    _check_step4()

    #: C1: all results are the same as after Step 14
    _check_step14()

    #: CC: nb of stages = 2
    assert_that(cc.nb_stages, equal_to(2))
    #: CC: can reuse result for s1, s2
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.can_reuse(cc['s2']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc['s2']), equal_to(Skip | Reuse | Execute))
    #: CC shares s1, s2, s3 from RC1
    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(cc['s2'].state, equal_to(Success))

    #--------------------------------------------------------------------------
    # Other checks

    #: can_reuse: invalid stage index
    assert_that(cc.can_reuse(0), equal_to(True))
    assert_that(cc.can_reuse(1), equal_to(True))
    assert_that(calling(cc.can_reuse).with_args(2), raises(IndexError))
    assert_that(calling(cc.can_reuse).with_args(rc4['s3']), raises(IndexError))

    #: run_options: invalid stage index
    assert_that(calling(cc.run_options).with_args(rc4['s3']), raises(IndexError))

    #: create_run_case: invalid stage index
    assert_that(calling(history.create_run_case).with_args((0, 2)), raises(IndexError))
    #: check that new run case was not added
    _check_history([rc1, rc2, rc3, rc4, c1])

    #: create_run_case: reuse stage without result
    cc.create_stage('s3')
    cc.create_stage('s4')
    assert_that(calling(history.create_run_case).with_args(3), raises(RuntimeError))
    #: check that new run case was not added
    _check_history([rc1, rc2, rc3, rc4, c1])

    #: delete: can't delete current case
    assert_that(calling(cc.delete), raises(RuntimeError))

    #: used_by_others: cases referenced by others
    assert_that(rc1.is_used_by_others(), equal_to(True))
    assert_that(rc2, is_in(rc1.used_by_others()))
    assert_that(rc3, is_in(rc1.used_by_others()))
    assert_that(rc4, is_in(rc1.used_by_others()))
    assert_that(rc2.is_used_by_others(), equal_to(False))
    assert_that(rc3.is_used_by_others(), equal_to(True))
    assert_that(rc4, is_in(rc3.used_by_others()))
    assert_that(c1.is_used_by_others(), equal_to(False))
    assert_that(cc.is_used_by_others(), equal_to(False))

    #: result attributes
    assert_that(cc['s1'].result.stage, equal_to(cc['s1']))
    assert_that(str(cc['s1'].result), equal_to('Result-s1'))
    assert_that(repr(cc['s1'].result), equal_to('Result-s1 <Success>'))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
@tempdir
def test_result_folder(tmpdir):
    """Test for folder attribute of Stage"""
    history = History()
    history.folder = tempfile.mkdtemp(dir=tmpdir, prefix='history-')
    try:
        cc = history.current_case
        cc.create_stage('s1')
        rc = history.create_run_case()
        assert_that(rc.name, equal_to('RunCase_1'))

        ref = osp.join(history.folder, 'RunCase_1', 'Result-s1')
        assert_that(rc[0].folder, equal_to(ref))

        # must not change after renaming
        rc[0].rename('news1')
        assert_that(rc[0].folder, equal_to(ref))

        # simulate execution by creating the results directory
        os.makedirs(rc[0].folder)
        # rc2 is created, "executed" and deleted
        rc2 = history.create_run_case()
        ref2 = osp.join(history.folder, 'RunCase_2', 'Result-news1')
        assert_that(rc2[0].folder, equal_to(ref2))
        os.makedirs(rc2[0].folder)
        rc2.delete()

        # create a fake directory 'RunCase_2'
        os.makedirs(osp.join(history.folder, 'RunCase_2'))

        # RunCase_2 doesn't exist but the directory does, so it is named '_3'
        rc3 = history.create_run_case()
        assert_that(rc3.name, equal_to('RunCase_3'))
    finally:
        shutil.rmtree(history.folder)

#------------------------------------------------------------------------------
def test_create_run_case():
    """Test for RunCase creation"""
    history = History()
    cc = history.current_case
    cc.name = 'c1'
    cc.create_stage('s1')
    cc.create_stage('s2')
    rc = history.create_run_case(name='rc')
    assert_that(rc['s1'].parent_case, same_instance(rc))
    assert_that(rc['s2'].parent_case, same_instance(rc))

#------------------------------------------------------------------------------
def test_create_run_case_all_exec_stages():
    """Test for RunCase creation by executing all stages"""
    history = History()
    cc = history.current_case
    cc.name = 'c1'
    cc.create_stage('s1')
    cc.create_stage('s2')
    rc = history.create_run_case(exec_stages=(0, 1), name='rc')
    assert_that(rc['s1'].parent_case, same_instance(rc))
    assert_that(rc['s2'].parent_case, same_instance(rc))

#------------------------------------------------------------------------------
def test_create_run_case_exec_stages():
    """Test for RunCase creation by executing some stages"""
    history = History()
    cc = history.current_case
    cc.name = 'c1'
    cc.create_stage('s1')
    cc.create_stage('s2')
    rc = history.create_run_case(exec_stages=0, name='rc')
    assert_that(rc, has_length(1))
    assert_that(cc, has_length(2))
    assert_that(rc['s1'].parent_case, same_instance(rc))
    assert_that(cc['s2'].parent_case, same_instance(cc))

#------------------------------------------------------------------------------
@tempdir
def test_keep_results(tmpdir):
    """Test for 'keep results' feature"""
    history = History()
    history.folder = tempfile.mkdtemp(dir=tmpdir, prefix='history-')
    cc = history.current_case

    #--------------------------------------------------------------------------
    # create three stages
    s1 = cc.create_stage('s1')
    s2 = cc.create_stage('s2')
    s3 = cc.create_stage('s3')

    assert_that(not cc['s1'].is_intermediate())
    assert_that(cc['s1'].state & Waiting)
    assert_that(cc['s2'].state & Waiting)
    assert_that(cc['s3'].state & Waiting)

    #--------------------------------------------------------------------------
    # create run case, exec all 3 stages 's1', 's2' and 's3', but keep results only for for stages 's1' and 's2'
    rc1 = history.create_run_case(name='rc1', reusable_stages=[1,2])
    # here, the state 's1' has 'Intermediate' state
    assert_that(cc['s1'].is_intermediate())
    assert_that(cc['s1'].state & Intermediate)
    assert_that(cc['s1'].state & Waiting)
    assert_that(cc['s2'].state & Waiting)
    assert_that(cc['s3'].state & Waiting)

    #--------------------------------------------------------------------------
    rc1.run()
    assert_that(cc['s1'].is_intermediate())
    assert_that(cc['s1'].state & Intermediate)
    assert_that(cc['s1'].state & Success)
    assert_that(cc['s2'].state & Success)
    assert_that(cc['s3'].state & Success)
    # no database for intermediate stages
    add_database(rc1['s2'].folder)
    add_database(rc1['s3'].folder)

    assert_that(not cc.can_reuse(cc['s1']))
    assert_that(cc.can_reuse(cc['s2']))
    assert_that(cc.can_reuse(cc['s3']))

    #--------------------------------------------------------------------------
    # now create another run case and reuse results from stages 's1' (as joined to 's2') and 's2'
    # so, exec only stage 's3'
    rc2 = history.create_run_case(name='rc2', exec_stages=2).run()

    assert_that(cc['s1'].is_intermediate())
    assert_that(cc['s1'].state & Intermediate)
    assert_that(cc['s1'].state & Success)
    assert_that(cc['s2'].state & Success)
    assert_that(cc['s3'].state & Success)

#------------------------------------------------------------------------------
@tempdir
def test_keep_results_and_use_as_current(tmpdir):
    """Test for 'keep results' feature and 'use as current' feature"""
    history = History()
    history.folder = tempfile.mkdtemp(dir=tmpdir, prefix='history-')
    cc = history.current_case

    #--------------------------------------------------------------------------
    s1 = cc.create_stage('s1')
    s2 = cc.create_stage('s2')
    s3 = cc.create_stage('s3')

    #--------------------------------------------------------------------------
    rc1 = history.create_run_case(name='rc1').run()
    assert_that(cc['s1'].state, equal_to(Intermediate | Success))
    assert_that(cc['s2'].state, equal_to(Intermediate | Success))
    assert_that(cc['s3'].state, equal_to(Success))
    # no database for intermediate stages
    add_database(rc1['s3'].folder)

    assert_that(not cc.can_reuse(cc['s1']))
    assert_that(not cc.can_reuse(cc['s2']))
    assert_that(cc.can_reuse(cc['s3']))

    #--------------------------------------------------------------------------
    rc2 = history.create_run_case(name='rc2').run(Error)
    assert_that(cc['s1'].state, equal_to(Intermediate | Error))
    assert_that(cc['s2'].state, equal_to(Intermediate | Error))
    assert_that(cc['s3'].state, equal_to(Error))

    assert_that(not cc.can_reuse(cc['s1']))
    assert_that(not cc.can_reuse(cc['s2']))
    assert_that(not cc.can_reuse(cc['s3']))

    #--------------------------------------------------------------------------
    cc.copy_from(rc1)
    assert_that(not cc.can_reuse(cc['s1']))
    assert_that(not cc.can_reuse(cc['s2']))
    assert_that(cc.can_reuse(cc['s3']))

    #--------------------------------------------------------------------------
    rc3 = history.create_run_case(name='rc3').run()
    assert_that(cc['s1'].state, equal_to(Intermediate | Success))
    assert_that(cc['s2'].state, equal_to(Intermediate | Success))
    add_database(rc3['s3'].folder)

    assert_that(not cc.can_reuse(cc['s1']))
    assert_that(not cc.can_reuse(cc['s2']))
    assert_that(cc.can_reuse(cc['s3']))

#------------------------------------------------------------------------------
@tempdir
def test_keep_results_can_reuse(tmpdir):
    """Test for can_reuse function when 'keep results' feature is used"""
    history = History()
    history.folder = tempfile.mkdtemp(dir=tmpdir, prefix='history-')
    cc = history.current_case

    #--------------------------------------------------------------------------
    # create three stages
    s1 = cc.create_stage('s1')
    s2 = cc.create_stage('s2')
    s3 = cc.create_stage('s3')

    assert_that(s1.result.folder, s1.folder)
    assert_that(s2.result.folder, s2.folder)
    assert_that(s3.result.folder, s3.folder)

    #--------------------------------------------------------------------------
    # create run case, exec all 3 stages 's1', 's2' and 's3', but keep results only for for stage 's3' (default behavior)
    rc1 = history.create_run_case(name='rc1').run()
    # simulate execution by creating the results directory
    add_database(rc1['s3'].folder)

    assert_that(cc['s1'].state, equal_to(Intermediate | Success))
    assert_that(cc['s2'].state, equal_to(Intermediate | Success))
    assert_that(cc['s3'].state, equal_to(Success))

    assert_that(not cc.can_reuse(cc['s1']))
    assert_that(not cc.can_reuse(cc['s2']))
    assert_that(cc.can_reuse(cc['s3']))

    assert_that(s1.result.folder, s3.folder)
    assert_that(s2.result.folder, s3.folder)
    assert_that(s3.result.folder, s3.folder)

#------------------------------------------------------------------------------
def test_run_with_options():
    """Test for run() method with options"""
    history = History()
    cc = history.current_case

    #--------------------------------------------------------------------------
    cc.create_stage('s1')
    cc.create_stage('s2')
    cc.create_stage('s3')

    #--------------------------------------------------------------------------
    rc1 = history.create_run_case(name='rc1')
    rc1.run()
    assert_that(cc['s1'].state, equal_to(Intermediate | Success))
    assert_that(cc['s2'].state, equal_to(Intermediate | Success))
    assert_that(cc['s3'].state, equal_to(Success))

    #--------------------------------------------------------------------------
    rc2 = history.create_run_case(name='rc2')
    rc2.run(Error)
    assert_that(cc['s1'].state, equal_to(Intermediate | Error))
    assert_that(cc['s2'].state, equal_to(Intermediate | Error))
    assert_that(cc['s3'].state, equal_to(Error))

    #--------------------------------------------------------------------------
    rc3 = history.create_run_case(name='rc3',reusable_stages=[1,2])
    rc3.run()
    assert_that(cc['s1'].state, equal_to(Intermediate | Success))
    assert_that(cc['s2'].state, equal_to(Success))
    assert_that(cc['s3'].state, equal_to(Success))

    #--------------------------------------------------------------------------
    rc4 = history.create_run_case(name='rc4',reusable_stages=[1,2])
    rc4.run(Error)
    assert_that(cc['s1'].state, equal_to(Intermediate | Error))
    assert_that(cc['s2'].state, equal_to(Error))
    assert_that(cc['s3'].state, equal_to(Waiting))

#------------------------------------------------------------------------------
def test_issue_26298_uc0():
    """Test automatic copy: use case 0."""

    history = History()
    cc = history.current_case
    s1 = cc.create_stage('s1')

    rc1 = history.create_run_case(name='rc1').run()

    s2 = cc.create_stage('s2')
    rc2 = history.create_run_case(name='rc2', exec_stages=1).run()

    # now rename the first stage with autocopy_enabled on
    from asterstudy.common.utilities import enable_autocopy
    with enable_autocopy(cc):
        s1.rename('s1p')

    # check the new structure of case/ stages
    assert_that(cc[0], same_instance(s1))
    assert_that(cc[1], same_instance(s2))

    assert_that(rc2[0], is_not(same_instance(s1)))
    assert_that(rc2[0], same_instance(rc1[0]))

    assert_that(rc2[1], is_not(same_instance(s2)))
    assert_that(rc2[1], is_not(same_instance(rc2[0])))

#------------------------------------------------------------------------------
def test_issue_26298_uc1():
    history = History()
    cc = history.current_case

    s1 = cc.create_stage('s1')
    s2 = cc.create_stage('s2')
    s3 = cc.create_stage('s3')

    rc1 = history.create_run_case(name='rc1', exec_stages=0).run()
    rc2 = history.create_run_case(name='rc2', exec_stages=1).run()

    from asterstudy.common.utilities import enable_autocopy
    with enable_autocopy(cc):
        cc['s2'].rename('s2p')

    assert_that(cc[0], same_instance(rc1[0]))
    assert_that(cc[0], same_instance(rc2[0]))

    assert_that(cc[1], is_not(same_instance(rc2[1])))

    assert_that(len(rc1), equal_to(1))
    assert_that(len(rc2), equal_to(2))
    assert_that(len(cc), equal_to(3))

#------------------------------------------------------------------------------
def test_issue_26298_uc2():
    history = History()
    cc = history.current_case

    cc.create_stage('s1')
    cc.create_stage('s2')
    cc.create_stage('s3')

    rc1 = history.create_run_case(name='rc1', exec_stages=0).run()
    rc2 = history.create_run_case(name='rc2', exec_stages=(1, 2), reusable_stages=[1, 2]).run()
    cc.detach('s3')

    # Here is where we are:
    #
    #    cc   rc2   rc1
    #    X     X     X
    #    |     |     |
    # s1 ------.---->o
    #    |     |
    # s2 ----->o
    #          |
    # s3       o
    assert_that(rc2.nb_stages, equal_to(3))
    assert_that(rc1.nb_stages, equal_to(1))
    assert_that(cc.nb_stages, equal_to(2))

    from asterstudy.common.utilities import enable_autocopy
    with enable_autocopy(cc):
        cc['s2'].rename('s2p')

    # Here is where we are:
    #
    #    cc   rc2   rc1
    #    X     X     X
    #    |     |     |
    # s1 ------.---->o
    #    |     |
    # s2 o     o
    #          |
    # s3       o
    assert_that(cc[0], same_instance(rc1[0]))
    assert_that(cc[0], same_instance(rc2[0]))

    assert_that(cc[1], is_not(same_instance(rc2[1])))

    assert_that(len(rc1), equal_to(1))
    assert_that(len(rc2), equal_to(3))
    assert_that(len(cc), equal_to(2))

    cc.detach('s2p')
    assert_that(len(cc), equal_to(1))
    assert_that(len(rc2), equal_to(3))

#------------------------------------------------------------------------------
def test_issue_26298_uc3():
    history = History()
    cc = history.current_case

    s1 = cc.create_stage('s1')
    rc1 = history.create_run_case(name='rc1').run()

    s2 = cc.create_stage('s2')
    rc2 = history.create_run_case(name='rc2', exec_stages=1).run()

    s3 = cc.create_stage('s3')
    rc3 = history.create_run_case(name='rc2', exec_stages=2).run()

    # now rename the first stage with autocopy_enabled on
    from asterstudy.common.utilities import enable_autocopy
    with enable_autocopy(cc):
        s1.rename('s1p')

    assert_that(cc[0], same_instance(s1))
    assert_that(cc[1], same_instance(s2))
    assert_that(cc[2], same_instance(s3))

    assert_that(rc3[0], is_not(same_instance(s1)))
    assert_that(rc3[0], same_instance(rc1[0]))
    assert_that(rc3[0], same_instance(rc2[0]))

    assert_that(rc3[1], is_not(same_instance(s2)))
    assert_that(rc3[1], same_instance(rc2[1]))
    assert_that(rc3[1], is_not(same_instance(rc3[0])))

    assert_that(rc3[2], is_not(same_instance(s3)))
    assert_that(rc3[2], is_not(same_instance(rc3[1])))
    assert_that(rc3[2], is_not(same_instance(rc3[0])))

#------------------------------------------------------------------------------
def test_issue_26298_uc4():
    history = History()
    cc = history.current_case

    cc.create_stage('s1')
    cc.create_stage('s2')
    cc.create_stage('s3')
    cc.create_stage('s4')

    rc1 = history.create_run_case(name='rc1', reusable_stages=range(4)).run()

    cc.detach('s4')
    rc2 = history.create_run_case(name='rc2', exec_stages=2).run()

    cc.detach('s3')
    rc3 = history.create_run_case(name='rc3', exec_stages=1).run()

    s1, s2 = rc3[0], rc3[1]
    # now rename the first stage with autocopy_enabled on
    from asterstudy.common.utilities import enable_autocopy
    with enable_autocopy(cc):
        s1.rename('s1p')

    assert_that(cc.nb_stages, equal_to(2))

    assert_that(rc1.nb_stages, equal_to(4))
    assert_that(rc2.nb_stages, equal_to(3))
    assert_that(rc3.nb_stages, equal_to(2))

    # check the new structure of case/ stages
    assert_that(cc[0], same_instance(s1))
    assert_that(cc[1], same_instance(s2))

    assert_that(rc3[0], is_not(same_instance(s1)))
    assert_that(rc3[0], same_instance(rc1[0]))
    assert_that(rc3[0], same_instance(rc2[0]))

    assert_that(rc3[1], is_not(same_instance(s2)))
    assert_that(rc3[1], is_not(same_instance(rc1[1])))
    assert_that(rc1[1], same_instance(rc2[1]))

    assert_that(rc2[2], is_not(same_instance(rc1[2])))

#------------------------------------------------------------------------------
def test_issue_26298_uc5():
    history = History()
    cc = history.current_case

    s1 = cc.create_stage('s1')
    s2 = cc.create_stage('s2')
    s3 = cc.create_stage('s3')
    s4 = cc.create_stage('s4')

    rc1 = history.create_run_case(name='rc1', reusable_stages=range(4)).run()
    rc2 = history.create_run_case(name='rc2', exec_stages=(2, 3), reusable_stages=[2, 3]).run()
    rc3 = history.create_run_case(name='rc3', exec_stages=3, reusable_stages=3).run()

    from asterstudy.common.utilities import enable_autocopy
    with enable_autocopy(cc):
        s2.rename('s2p')

    assert_that(cc[0], same_instance(rc1[0]))
    assert_that(cc[0], same_instance(rc2[0]))
    assert_that(cc[0], same_instance(rc3[0]))

    assert_that(cc[1], is_not(same_instance(rc1[1])))
    assert_that(rc2[1], same_instance(rc1[1]))
    assert_that(rc3[1], same_instance(rc1[1]))

    assert_that(cc[2], is_not(same_instance(rc1[2])))
    assert_that(rc2[2], is_not(same_instance(rc1[2])))
    assert_that(rc3[2], same_instance(rc2[2]))

    assert_that(cc[3], is_not(same_instance(rc1[3])))
    assert_that(rc2[3], is_not(same_instance(rc1[3])))
    assert_that(rc3[3], is_not(same_instance(rc2[3])))

#------------------------------------------------------------------------------
def test_issue_26298_uc6():
    """Second use case reported by issue26298."""
    history = History()
    cc = history.current_case

    cc.create_stage('s1')
    rc1 = history.create_run_case(name='rc1').run()

    cc.create_stage('s2')
    rc2 = history.create_run_case(name='rc2', exec_stages=(0, 1), reusable_stages=[0, 1]).run()

    assert_that(rc1[0], is_not(is_in(rc2[1].parent_nodes)))
    assert_that(rc2[1], is_not(is_in(rc1[0].child_nodes)))

#------------------------------------------------------------------------------
def test_issue_26546():
    """Test use case reported by issue26546"""
    history = History()
    cc = history.current_case

    st1 = cc.create_stage('s1')
    st2 = cc.create_stage('s2')
    rc1 = history.create_run_case(name='rc1', exec_stages=0, reusable_stages=0).run()
    rc2 = history.create_run_case(name='rc2', exec_stages=0, reusable_stages=0).run()

    assert_that(rc1[0], same_instance(st1))
    assert_that(rc2[0], is_not(same_instance(st1)))
    assert_that(cc[0], same_instance(rc2[0]))
    assert_that(cc[1], same_instance(st2))

    assert_that(rc2[0].parent_case, same_instance(rc2))
    assert_that(st1.parent_case, same_instance(rc1))
    assert_that(st2.parent_case, same_instance(cc))

#------------------------------------------------------------------------------
def test_validity_for_run():
    """Test for case validity for running"""
    #--------------------------------------------------------------------------
    history = History()
    cc = history.current_case

    assert_that(cc.can_be_ran(), equal_to(False))

    cc.create_stage('s1')
    assert_that(cc.can_be_ran(), equal_to(True))

    command = cc['s1']('LIRE_TABLE')
    command.init({'UNITE': {}})
    assert_that(cc.can_be_ran(), equal_to(False))

    command['UNITE'] = {77:'file.dat'}
    assert_that(cc.can_be_ran(), equal_to(True))

#------------------------------------------------------------------------------
@tempdir
def test_delete_results(tmpdir):
    """Test for case results delete"""
    history = History()
    history.folder = tempfile.mkdtemp(dir=tmpdir, prefix='history-')

    cc = history.current_case
    cc.create_stage('s1')

    rc1 = history.create_run_case(name='rc1')
    rc1.run()
    # Create a fake results tree
    # rc1/Result-s1
    # ├── base-stage2
    # │   ├── glob.1.gz
    # │   └── pick.1.gz
    # ├── export
    # ├── launcher_script
    # ├── logs
    # │   ├── error.log.runCommand_launcher_script_xxx
    # │   ├── output.log.runCommand_launcher_script_xxx
    # │   └── stderr_command_salome.log
    # ├── message
    # └── rc1_s1.comm
    stdir = cc['s1'].folder
    results = [
        osp.join(stdir, 'base-stage2', 'glob.1.gz'),
        osp.join(stdir, 'base-stage2', 'pick.1.gz'),
        osp.join(stdir, 'export'),
        osp.join(stdir, 'launcher_script'),
        osp.join(stdir, 'rc1_s1.comm'),
    ]
    logs = [
        osp.join(stdir, 'logs', 'error.log.run_xxx'),
        osp.join(stdir, 'logs', 'output.log.run_xxx'),
        osp.join(stdir, 'logs', 'stderr_command_salome.log'),
        osp.join(stdir, 'message'),
    ]
    for path in results + logs:
        add_file(path)

    assert_that(cc['s1'].state, equal_to(Success))
    assert_that(osp.exists(rc1.folder), equal_to(True))
    assert_that(cc.can_reuse(cc['s1']), equal_to(True))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Execute | Reuse))

    for path in results + logs:
        assert_that(osp.exists(path), equal_to(True), path)

    rc1.delete_dir(keep_logs=True)

    for path in results:
        assert_that(osp.exists(path), equal_to(False), path)
    for path in logs:
        assert_that(osp.exists(path), equal_to(True), path)
    assert_that(osp.exists(rc1.folder), equal_to(True))
    assert_that(cc.can_reuse(cc['s1']), equal_to(False))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Execute))

    rc1.delete_dir()

    assert_that(osp.exists(rc1.folder), equal_to(False))
    assert_that(cc.can_reuse(cc['s1']), equal_to(False))
    assert_that(cc.run_options(cc['s1']), equal_to(Skip | Execute))


#------------------------------------------------------------------------------
def test_job():
    from asterstudy.datamodel.result import Job
    job = Job()
    assert_that(job.mode, instance_of(int))

    job.set('mode', "Batch")
    assert_that(job.mode, instance_of(int))
    assert_that(job.mode, equal_to(Job.Batch))

    job.set('mpicpu', 2)
    assert_that(job.get('mpicpu'), instance_of(int))
    assert_that(job.get('mpicpu'), equal_to(2))

    job.set_parameters_from({'memory': 1234})
    assert_that(job.get('memory'), instance_of(int))
    assert_that(job.get('memory'), equal_to(1234))

    job.set_parameters_from({'compress': True})
    assert_that(job.get('compress'), instance_of(bool))
    assert_that(job.get('compress'), equal_to(True))

    assert_that(calling(job.get).with_args('unknown'), raises(AttributeError))

    new = Job()
    new.copy_parameters_from(job)
    assert_that(new.mode, equal_to(Job.Batch))
    assert_that(new.get('memory'), instance_of(int))
    assert_that(new.get('memory'), equal_to(1234))
    assert_that(new.server, empty())
    assert_that(new.get('nodes'), none())
    assert_that(new.get('mode'), equal_to(Job.Batch))
    assert_that(new.get('mpicpu'), equal_to(2))

    params = new.asdict()
    assert_that(params['mode'], equal_to(Job.BatchText))
    assert_that(params['memory'], equal_to(1234))
    assert_that(params, is_not(has_key('server')))
    assert_that(params, is_not(has_key('nodes')))
    assert_that(params['mpicpu'], equal_to(2))

    new.jobid = 'id123456'
    new.start_time = 'just now!'
    new.name = 'new job'
    new.server = 'remote'
    new.description = 'informations about job'
    new.studyid = 1
    new.set('version', 'stable')
    new.set('time', '00:12:34')
    new.set('mpicpu', 1)
    new.set('nodes', 1)
    new.set('threads', 4)
    new.set('folder', 'results_directory')
    new.set('partition', 'part')
    new.set('queue', 'aqueue')
    new.set('args', '--rcdir=/xxx')
    new.set('wckey', 'ABCDE')
    new.set('extra', '#param')
    params = new.asdict()
    assert_that(params['jobid'], equal_to('id123456'))
    for key in ['jobid', 'name', 'server', 'mode',
                'description'] + list(Job.ExecParameters):
        assert_that(params, has_key(key))
    assert_that(params, is_not(has_key('start_time')))
    assert_that(params, is_not(has_key('end_time')))

#------------------------------------------------------------------------------
def test_create_run_case_info():
    history = History()

    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'ssnv128a.export')
    case, _ = history.import_case(export)

    stgi = case.stages[0]
    info = stgi.handle2info[20]
    assert_that(info.filename, is_not(none()))
    assert_that(info.filename, contains_string("ssnv128a.mmed"))

    # Simulate first run
    rc1 = history.create_run_case(name='rc1')

    stgi = rc1.stages[0]
    info = stgi.handle2info[20]
    assert_that(info.filename, is_not(none()))
    assert_that(info.filename, contains_string("ssnv128a.mmed"))

    # Simulate second run
    rc2 = history.create_run_case(name='rc2')

    stgi = rc2.stages[0]
    info = stgi.handle2info[20]
    assert_that(info.filename, is_not(none()))
    assert_that(info.filename, contains_string("ssnv128a.mmed"))

#------------------------------------------------------------------------------
def test_copy_from():
    history = History()
    cc = history.current_case
    cc.name = 'c1'

    cc.create_stage('s1')
    cc.create_stage('s2')
    cc.create_stage('s3')

    rc1 = history.create_run_case(name='rc1', reusable_stages=[0, 1, 2]).run()
    rc2 = history.create_run_case((0, 1), name='rc2', reusable_stages=(0, 1)).run()

    with enable_autocopy(cc):
        cc.copy_from(rc1)

    with enable_autocopy(cc):
        cc.copy_from(rc2)

@attr('fixit')
def test_new_case():
    # similar to test_history:test_replace_current_case
    history = History()
    cc = history.current_case
    cc.name = 'c1'
    s1 = cc.create_stage('s1')

    rc1 = history.create_run_case(name='rc1')
    s1.result.state = Success
    assert_that(s1.result.state & Success)

    newc = history.create_case(replace=True)
    assert_that(s1.result.state & Success)


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
