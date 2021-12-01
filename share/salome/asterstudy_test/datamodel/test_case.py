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

"""Automatic tests for Case class."""


import unittest

from asterstudy.common import CFG
from asterstudy.datamodel.case import Case
from asterstudy.datamodel.history import History
from hamcrest import *
from testutils import attr
from testutils.node import is_not_referenced
from testutils.tools import check_persistence


class TestCase(unittest.TestCase):
    """Test case for Case class."""

    def test_common_desc_stages(self):
        """Tests detection of common descendant stages to two cases"""

        history = History()
        case1 = history.current_case

        # as a reminder, there are now 1 case in our project
        # it is named 'Case_1'

        # creating three stages in Case_1
        # and two stage in Case_2 with a parent in Case_1
        # one stage in Case_3 with a parent in Case_2
        st0 = case1.create_stage('Stage_0')
        st1 = case1.create_stage('Stage_1')
        st2 = case1.create_stage('Stage_2')

        #
        case2 = case1.copy()
        st3 = st2.copy(case2)
        st4 = case2.create_stage('Stage_4')

        #
        case3 = case2.copy()
        st5 = st4.copy(case3)

        # test that one of case1's descendant is contained by case2
        # note: current case (which is case1 now) is not taken into account!
        self.assertTrue(case1.is_used_by_others())
        self.assertTrue(case2.is_used_by_others())
        self.assertFalse(case3.is_used_by_others())
        self.assertTrue(case2 in case1.used_by_others())
        self.assertTrue(case3 in case1.used_by_others())
        self.assertTrue(case3 in case2.used_by_others())

    def test_case_deletion(self):
        """Test deletion of a Case instance

        This implies deletion of all cases that contain descendent
        stages to the case to be deleted.
        """

        history = History()
        case1 = history.current_case

        #
        st0 = case1.create_stage('Stage_0')
        st1 = case1.create_stage('Stage_1')
        st2 = case1.create_stage('Stage_2')
        # there's only one case in the history
        assert_that(history.cases, equal_to([case1]))

        #
        case2 = case1.copy()
        st3 = st2.copy(case2)
        st4 = case2.create_stage('Stage_4')

        # copy now preserves current
        # there are two cases in the history; case1 is the current one
        assert_that(history.cases, equal_to([case2, case1]))
        assert_that(history.current_case, is_(case1))

        #
        case3 = case2.copy()
        st5 = st4.copy(case3)

        # copy now preserves current
        # there are three cases in the history; case1 is the current one
        assert_that(history.cases, equal_to([case2, case3, case1]))
        assert_that(history.current_case, is_(case1))

        # test that current case cannot be deleted
        assert_that(calling(case1.delete), raises(RuntimeError))

        # test that deleting case2 deletes also case3
        case2.delete()
        assert_that(is_not_referenced(case2, history), equal_to(True))
        assert_that(is_not_referenced(case3, history), equal_to(True))
        assert_that(is_not_referenced(case1, history), equal_to(False))

        # there's now only one case in the history, and this is case1, the current
        assert_that(history.cases, equal_to([case1]))
        assert_that(history.current_case, is_(case1))

    def test_copy_shared_stages(self):
        """Test recursive copy of stages

        Makes stages owned rather than referenced in a case
        This is especially useful when executing a case
        """

        history = History()
        case1 = history.current_case

        #
        st0 = case1.create_stage('st0')
        st1 = case1.create_stage('st1')
        st2 = case1.create_stage('st2')

        # copy case, which will make the stages referenced
        case2 = case1.copy()

        # now, I'd like to own stages 'st1' to 'st2'
        case2.copy_shared_stages_from(2)

        # test stages have been properly copied and reordered
        assert_that(case2['st0'], equal_to(case1['st0']))
        assert_that(case2['st1'], is_not(equal_to(case1['st1'])))
        assert_that(case2[1], equal_to(case2['st1']))
        assert_that(case2['st2'], is_not(equal_to(case1['st2'])))
        assert_that(case2[2], equal_to(case2['st2']))

        # test reordering based on non existing attribute raises an error
        with self.assertRaises(AttributeError):
            case1.sort_children(type(st0), 'unexisting_attr')

        # test this also works with objects with heterogeneous content
        st1.sort_children(type(st0), 'number')

#------------------------------------------------------------------------------
def test_getitem_func():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage0 = case.create_stage('Stage_0')
    stage1 = case.create_stage('Stage_1')
    stage2 = case.create_stage('Stage_2')

    #--------------------------------------------------------------------------
    assert_that(tuple(case[:stage0]), equal_to(tuple()))
    assert_that(tuple(case[:0]), equal_to(tuple()))
    assert_that(case['Stage_0'], equal_to(stage0))
    assert_that(case[0], equal_to(stage0))

    #--------------------------------------------------------------------------
    assert_that(tuple(case[:stage1]), equal_to((stage0,)))
    assert_that(tuple(case[:1]), equal_to((stage0,)))
    assert_that(case['Stage_1'], equal_to(stage1))
    assert_that(case[1], equal_to(stage1))

    #--------------------------------------------------------------------------
    assert_that(tuple(case[:stage2]), equal_to((stage0, stage1)))
    assert_that(tuple(case[:2]), equal_to((stage0, stage1)))
    assert_that(case['Stage_2'], equal_to(stage2))
    assert_that(case[2], equal_to(stage2))

    #--------------------------------------------------------------------------
    #   check that two stages with same number returns None
    #   this check has been moved before deletion is tested

    stage = case[0]
    assert_that(stage.name, equal_to(stage0.name))
    #
    stage.number = 3
    assert_that(stage0.number, equal_to(stage2.number))

    assert_that(case.get_stage_by_num(3), none())
    stage.number = 1

    #--------------------------------------------------------------------------
    del case['Stage_1']

    # because of recursive deletion, Stage_2 has been deleted as well
    assert_that(tuple(case[:]), equal_to((stage0,)))

    #--------------------------------------------------------------------------
    # delete first Stage and check there is nothing left in Case

    del case[0]
    assert_that(tuple(case[:]), equal_to(tuple()))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_text2stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE()

MATER = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
    ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER, TOUT='OUI'), MAILLAGE=MAIL_Q)
"""

    stage = case.text2stage(text, 'Case_1')
    assert_that(stage.is_graphical_mode(), equal_to(True))

    assert_that('MAIL_Q', is_in(stage))
    assert_that('MATER', is_in(stage))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_text2stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    text = \
"""
CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER, TOUT='OUI'), MAILLAGE=MAIL_Q)
"""

    stage = case.text2stage(text, 'Case_1')
    assert_that(stage.is_graphical_mode(), equal_to(False))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_import_stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    import os
    filename = os.path.join(os.getenv('ASTERSTUDYDIR'),
                            'data', 'comm2study', 'zzzz289f.comm')
    stage = case.import_stage(filename)
    assert_that(stage.is_graphical_mode(), equal_to(True))

    for command in stage:
        command.type


def test_inout_dirs():
    """Test for in / out directory attributes"""
    #--------------------------------------------------------------------------
    history = History()

    case = history.current_case

    #--------------------------------------------------------------------------
    def _set_attr(_case, _dir, _is_in_dir):
        if _is_in_dir:
            _case.in_dir = _dir
        else:
            _case.out_dir = _dir

    #--------------------------------------------------------------------------
    # check default values
    assert_that(case.in_dir, none())
    assert_that(case.out_dir, none())

    #--------------------------------------------------------------------------
    # check that dirs can be set
    case.in_dir = '/usr'
    case.out_dir = '/tmp'

    assert_that(case.in_dir, equal_to('/usr'))
    assert_that(case.out_dir, equal_to('/tmp'))

    check_persistence(history)

    #--------------------------------------------------------------------------
    # check that the same dir can be set as both input and output
    assert_that(calling(_set_attr).with_args(case, '/tmp', True), raises(ValueError))
    assert_that(calling(_set_attr).with_args(case, '/usr', False), raises(ValueError))

    #--------------------------------------------------------------------------
    # check that the one dir can be a sub-path of another one
    assert_that(calling(_set_attr).with_args(case, '/usr/bin', False), raises(ValueError))
    assert_that(calling(_set_attr).with_args(case, '/tmp/aaa', True), raises(ValueError))
    assert_that(calling(_set_attr).with_args(case, '/', False), raises(ValueError))
    assert_that(calling(_set_attr).with_args(case, '/', True), raises(ValueError))

    #--------------------------------------------------------------------------
    # check that only existing dir can be set as input
    assert_that(calling(_set_attr).with_args(case, '/bla/bla/bla', True), raises(ValueError))

    #--------------------------------------------------------------------------
    # check that dirs can be unset
    case.in_dir = None
    assert_that(case.in_dir, none())

    case.out_dir = None
    assert_that(case.out_dir, none())

    #--------------------------------------------------------------------------
    # check case copy
    case.in_dir = '/usr'
    case.out_dir = '/tmp'

    case_dup = case.copy('dup')

    assert_that(case_dup.in_dir, equal_to('/usr'))
    assert_that(case_dup.out_dir, equal_to('/tmp'))

    #--------------------------------------------------------------------------
    # check backup case
    case_backup = history.create_backup_case("backup")

    assert_that(case_backup.in_dir, equal_to('/usr'))
    assert_that(case_backup.out_dir, equal_to('/tmp'))

    #--------------------------------------------------------------------------
    # check run case
    case.create_stage()
    case_run = history.create_run_case(name="run")

    assert_that(case_run.in_dir, equal_to('/usr'))
    assert_that(case_run.out_dir, equal_to('/tmp'))


def test_insert_stage():
    case = History().current_case
    assert_that(case.stages, empty())

    sta = case.create_stage("A")
    stb = case.create_stage("B")
    stc = case.create_stage("C")
    uids = [i.uid for i in case.stages]
    assert_that(uids, contains(sta.uid, stb.uid, stc.uid))

    stx = case.create_stage("X", 0)
    uids = [i.uid for i in case.stages]
    assert_that(uids, contains(stx.uid, sta.uid, stb.uid, stc.uid))

    sty = case.create_stage("Y", 1)
    uids = [i.uid for i in case.stages]
    assert_that(uids, contains(stx.uid, sty.uid, sta.uid, stb.uid, stc.uid))

    stz = case.create_stage("Z", 4)
    uids = [i.uid for i in case.stages]
    assert_that(uids,
                contains(stx.uid, sty.uid, sta.uid, stb.uid, stz.uid, stc.uid))


def test_case_name():
    case = History().current_case
    assert_that(case.stages, empty())

    case.create_stage()
    assert_that([i.name for i in case.stages],
                contains("Stage_1"))

    case.create_stage()
    assert_that([i.name for i in case.stages],
                contains("Stage_1", "Stage_2"))

    case.create_stage("test")
    assert_that([i.name for i in case.stages],
                contains("Stage_1", "Stage_2", "test"))

    case.create_stage("test")
    assert_that([i.name for i in case.stages],
                contains("Stage_1", "Stage_2", "test", "test_1"))

    case.create_stage("test_1")
    assert_that([i.name for i in case.stages],
                contains("Stage_1", "Stage_2", "test", "test_1", "test_2"))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
