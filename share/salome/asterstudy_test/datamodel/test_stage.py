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

"""Automatic tests for Stage class."""


import pickle
import unittest

from asterstudy.common import CFG, ConversionError
from asterstudy.datamodel import FileAttr
from asterstudy.datamodel.abstract_data_model import add_parent, compare_deps
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.dataset import TextDataSet
from asterstudy.datamodel.general import ConversionLevel
from asterstudy.datamodel.history import History
from asterstudy.datamodel.stage import Stage
from asterstudy.datamodel.study2comm import study2comm
from hamcrest import *
from testutils import attr
from testutils.node import is_not_referenced
from testutils.tools import check_text_eq


class TestStage(unittest.TestCase):
    """Test case for Stage class."""

    def test_add_commands(self):
        """Test for adding commands to stage"""

        # Create history.
        history = History()
        case = history.current_case
        stage = case.create_stage('Stage_1')

        # Add several commands.
        cmd1 = stage.add_command('DEFI_GROUP', 'g')
        cmd2 = stage.add_command('DEFI_MATERIAU', 'm1')
        cmd3 = stage.add_command('DEFI_MATERIAU', 'm2')

        # Add dependencies between commands:
        # cmd2 is an ancestor of cmd1, cmd2 < cmd1
        add_parent(cmd1, cmd2)
        # cmd3 is an ancestor of cmd1, cmd3 < cmd1
        add_parent(cmd1, cmd3)

        # Check data model nodes comparison.
        assert_that(compare_deps(cmd1, cmd1), equal_to(0))
        # cmd1 > cmd2
        assert_that(compare_deps(cmd1, cmd2), equal_to(1))
        assert_that(cmd1, greater_than(cmd2))
        # cmd2 < cmd1
        assert_that(cmd2, less_than(cmd1))
        assert_that(compare_deps(cmd2, cmd1), equal_to(-1))
        # cmd3 < cmd1
        assert_that(cmd3.depends_on(cmd1), equal_to(False))
        assert_that(cmd1.depends_on(cmd3), equal_to(True))
        # cmd1 > cmd3
        assert_that(compare_deps(cmd1, cmd3), equal_to(1))
        # no deps between cmd2 and cmd3
        assert_that(compare_deps(cmd2, cmd3), equal_to(0))
        assert_that(compare_deps(cmd3, cmd2), equal_to(0))

    def test_text_stage(self):
        """Test for a case with a text stage"""
        history = History()
        case = history.current_case
        stg1 = case.create_stage('Stage_1')
        self.assertTrue(stg1.is_graphical_mode())
        cmd = stg1.add_command('DEFI_MATERIAU', 'Acier')
        par = cmd['ELAS']['NU']
        par.value = 1
        # can not add text content in a graphical stage
        with self.assertRaises(TypeError):
            stg1.set_text('DEFI_MATERIAU(...)')

        stext2 = case.create_stage('Stage_2')
        stext2.use_text_mode()
        self.assertTrue(stext2.is_text_mode())
        # can not add Command in a text stage
        stext2.add_command('DEFI_MATERIAU', 'Acier')
        self.assertEqual(len(stext2.commands), 1)
        del stext2['Acier']
        self.assertEqual(len(stext2.commands), 0)

        stext3 = case.create_stage('Stage_3')
        # automatically in text mode because it follows a text stage
        self.assertTrue(stext3.is_graphical_mode())

    def test_switch_mode(self):
        """Test of switch stage mode from graphic to text and vice versa"""

        # Create history.
        history = History()
        case = history.current_case
        stage = case.create_stage('Stage_1')

        # Add several commands.
        text = \
"""
TAUN1 = DEFI_FONCTION(NOM_PARA='INST',
                      VALE=(0.0, 1.0, 1.0, 1.0, 2.0, 1.0, 3.0, 1))

interp = CALC_FONC_INTERP(FONCTION=TAUN1,
                          VALE_PARA=(0.5, 1.5, 2.5, 3.5))
"""
        comm2study(text, stage)
        commands = stage.commands

        # test if the stage in the graphic mode
        self._check_graphic_mode(stage, commands)

        # try to switch to graphic mode, check that data are the same
        stage.use_graphical_mode()
        self._check_graphic_mode(stage, commands)

        # switch to text mode
        text2 = study2comm(stage)
        stage.use_text_mode()
        self._check_text_mode(stage, text2)

        # try to switch to text mode, check that data are the same
        stage.use_text_mode()
        self._check_text_mode(stage, text)

        # switch back to graphic mode.
        stage.use_graphical_mode()
        self._check_graphic_mode(stage, commands)

    def _check_graphic_mode(self, stage, commands):
        """Test if the stage is in graphic mode"""
        self.assertTrue(stage.is_graphical_mode())
        self.assertFalse(stage.is_text_mode())
        with self.assertRaises(TypeError):
            stage.set_text("")
        #
        children = stage.commands
        self.assertEqual(len(stage), len(commands))
        for cmd in commands:
            self.assertIn(cmd.name, [i.name for i in children])
            self.assertIn(cmd.title, [i.title for i in children])

    def _check_text_mode(self, stage, text):
        """Test if the stage is in text mode"""
        self.assertTrue(stage.is_text_mode())
        self.assertFalse(stage.is_graphical_mode())
        #
        children = stage.child_nodes
        assert_that(children[0], instance_of(TextDataSet))

        self.assertEqual(children[0].name, "DataSet")
        self.assertTrue(check_text_eq(children[0].text, text))
        self.assertTrue(stage in children[0].parent_nodes)

def test_delete_stage():
    """Test to delete a Stage.

    All child Stages are recursively deleted, to prevent using stages
    with unexisting parent, which would lead to defective execution.

    Note that this test only verifies that Stages are recursively removed.

    Checking that this operation would not lead to unwanted deletion,
    i.e. deletion of stages with different parent case from the one the
    user wanted to delete, is done in test_delete_case"""

    history = History()
    case = history.current_case

    # a first test with three stages in a row
    st1 = case.create_stage('Stage_1')
    st2 = case.create_stage('Stage_2')
    st2.add_command('LIRE_MAILLAGE')
    st3 = case.create_stage('Stage_3')

    assert_that(st1.child_stages, has_length(1))
    assert_that(st2.child_stages, has_length(1))
    assert_that(st3.child_stages, has_length(0))

    # now stage 2 is removed
    st2.delete(user_deletion=True)

    # check that st2 and st3 are undefined, but st1 still is
    # it is safe to rely on the order of conditions in Python
    assert_that('st2' not in locals() or st2 is None
                or is_not_referenced(st2, history))
    assert_that(is_not_referenced(st3, history))

    # check st1 has no child of Stage kind
    # getChildren
    for mychild in st1.child_nodes:
        assert_that(mychild, is_not(instance_of(Stage)))
    assert_that(st1.child_stages, empty())

    # check that a stage added now would have number 2 (counter has to be decremented when deleting)
    st2 = case.create_stage('Stage_2')
    assert_that(st2.number, equal_to(2))

def test_delete_empty_stage():
    # deleting an empty stage + use_deletion does not remove child stages
    history = History()
    case = history.current_case

    # a first test with three stages in a row
    st1 = case.create_stage('Stage_1')
    st2 = case.create_stage('Stage_2')
    st3 = case.create_stage('Stage_3')

    assert_that(st1.child_stages, has_length(1))
    assert_that(st2.child_stages, has_length(1))
    assert_that(st3.child_stages, has_length(0))

    # now stage 2 is removed
    st2.delete_empty()

    # check that st2 is undefined, but st1 still is
    # it is safe to rely on the order of conditions in Python
    assert_that('st2' not in locals() or st2 is None
                or is_not_referenced(st2, history))
    assert_that(st3.model, equal_to(history))

    assert_that(st1.child_stages, has_length(1))
    assert_that(st3, is_in(st1.child_stages))
    assert_that(st3.child_stages, has_length(0))

    # check that a stage added now would have number 2 (counter has to be decremented when deleting)
    st4 = case.create_stage('Stage_4')
    assert_that(st4.number, equal_to(3))


def test_duplicate():
    """Test for a simple case and stage copies."""

    # add some stages in the current case
    # examples from test_history / test_create are used
    # no tests here since they would be redundant with test_history

    history = History()
    case = history.current_case

    st1 = case.create_stage('Stage_1')
    cmd = st1.add_command('DEFI_MATERIAU', 'Acier')
    par = cmd['ELAS']['NU']
    par.value = 1

    st2 = case.create_stage('Stage_2')
    cmd = st2.add_command('DEFI_MATERIAU', 'Beton')
    par1 = cmd['ELAS_FO']['RHO']
    par1.value = 2

    # new case by duplicating current
    # copying now preserves the current_case
    case2 = case.copy()
    case2.name = 'Case_2'

    # test that current case is preserved
    assert_that(case, equal_to(history.current_case))
    assert_that(case2, is_not(equal_to(history.current_case)))

    # test name is 'Case_2'
    assert_that(case2.name, equal_to('Case_2'))

    # copy second stage for this new case
    st3 = st2.copy(case2)

    # Here is the situation now
    #
    #   cases      O case2        O case
    #              |              |
    #   stages     |--------------.->X st1
    #              |              |
    #              -->X st3       -->X st2

    # test that st1 and st3 are children for case2, but not st2
    assert_that(history.has_path(case.uid, st1.uid), equal_to(True))
    assert_that(history.has_path(case2.uid, st1.uid), equal_to(True))
    assert_that(st1, is_in(history.child_nodes(case2)))
    assert_that(case2, is_in(st1.parent_nodes))
    #
    assert_that(history.has_path(case2.uid, st3.uid), equal_to(True))
    assert_that(st3, is_in(history.child_nodes(case2)))
    assert_that(case2, is_in(st3.parent_nodes))

    # between case2 and st2, there is no path anymore
    # since there are no connection from stage to stage any more
    assert_that(history.has_path(case2.uid, st2.uid), equal_to(False))
    assert_that(st2, is_not(is_in(history.child_nodes(case2))))
    assert_that(case2, is_not(is_in(st2.parent_nodes)))

    # there are no connections anymore between stages
    assert_that(history.has_path(st1.uid, st2.uid), equal_to(False))
    assert_that(st2, is_not(is_in(history.child_nodes(st1))))
    assert_that(st1, is_not(is_in(st2.parent_nodes)))
    #
    assert_that(history.has_path(st1.uid, st3.uid), equal_to(False))
    assert_that(st3, is_not(is_in(history.child_nodes(st1))))
    assert_that(st1, is_not(is_in(st3.parent_nodes)))
    #
    assert_that(history.has_path(st2.uid, st3.uid), equal_to(False))
    assert_that(st2, is_not(is_in(history.child_nodes(st3))))
    assert_that(st3, is_not(is_in(st2.parent_nodes)))

    # test that command and parameters have been copied
    assert_that(cmd, is_in(st2))
    assert_that(cmd, is_not(is_in(st3)))

    # retrieve the copied command, test the copy is OK
    mylist = history.child_nodes(st3.dataset)
    assert_that(len(mylist), equal_to(1))
    cmd2 = mylist[0]
    assert_that(cmd * cmd2, equal_to(None))
    assert_that(cmd.uid, is_not(equal_to(cmd2.uid)))

    # retrieve the copied parameter, test the copy is OK
    assert_that('ELAS_FO', is_in(cmd2.keys()))
    par2 = cmd2['ELAS_FO']['RHO']
    assert_that(par1, is_not(same_instance(par2)))
    assert_that(par1.value, equal_to(par2.value))

    # now the first step is copied
    st4 = st1.copy(case2)

    # Here is the situation now
    #
    #   cases      O case2        O case
    #              |              |
    #   stages     |->X st4       |->X st1
    #              |              |
    #              -->X st3       -->X st2

    # test case2, st4, st3 connections
    assert_that(history.has_path(case2.uid, st4.uid), equal_to(True))
    assert_that(st4, is_in(history.child_nodes(case2)))
    assert_that(case2, is_in(st4.parent_nodes))
    #
    assert_that(history.has_path(case2.uid, st3.uid), equal_to(True))
    assert_that(st3, is_in(history.child_nodes(case2)))
    assert_that(case2, is_in(st3.parent_nodes))
    #
    # No more connections between stages
    assert_that(history.has_path(st4.uid, st3.uid), equal_to(False))
    assert_that(st3, is_not(is_in(history.child_nodes(st4))))
    assert_that(st4, is_not(is_in(st3.parent_nodes)))

    # test case, st1, st2 connections
    assert_that(history.has_path(case.uid, st1.uid), equal_to(True))
    assert_that(st1, is_in(history.child_nodes(case)))
    assert_that(case, is_in(st1.parent_nodes))
    #
    assert_that(history.has_path(case.uid, st2.uid), equal_to(True))
    assert_that(st2, is_in(history.child_nodes(case)))
    assert_that(case, is_in(st2.parent_nodes))
    #
    # No more connections between stages
    assert_that(history.has_path(st1.uid, st2.uid), equal_to(False))
    assert_that(st2, is_not(is_in(history.child_nodes(st1))))
    assert_that(st1, is_not(is_in(st2.parent_nodes)))

    # test the absence of any other connection
    assert_that(history.has_path(case.uid, st4.uid), equal_to(False))
    assert_that(history.has_path(case.uid, st3.uid), equal_to(False))
    assert_that(history.has_path(case2.uid, st1.uid), equal_to(False))
    assert_that(history.has_path(case2.uid, st2.uid), equal_to(False))


def test_delete_stage_tree():
    """A somewhat more complex test to delete a Stage

       We assume the user has confirmed the action

       All stages are then deleted"""

    history = History()
    # as a reminder, at this stage history contains a current case
    # named 'Case_1'

    history.create_case('Case_2')
    # at this stage 'Case_2' is the new current, 'Case_1' still exists

    # odd syntax to retrieve both of these cases, with getChildren method
    # explanation: gets all nodes without parent, i.e. all cases
    case1, case2 = history.child_nodes(None)

    st1 = case1.create_stage('Stage_1')
    st2 = case1.create_stage('Stage_2')
    st3 = case1.create_stage('Stage_3')

    # A 'branching' stage is created by copy
    # Note here the new behavior of stage.copy() after issue26514
    #
    # Before: `stage.copy(case1)` with empty case1 would automatically:
    #     - reference parent stages;
    #     - add a copy of `stage`;
    #     - copy child ones.
    #
    # After: `stage.copy(case1)` with empty case1 would just:
    #     - add a copy `stage` as the first stage of `case1`.
    #
    # This difference is on purpose. We have the `copy_shared_stages_from`
    #     method for the first behavior, and it was redundant to
    #     have `stage.copy` do the same.
    #
    # This explain the lines below.
    case2.add_stage(st1)
    case2.add_stage(st2)
    case2.add_stage(st3)
    st4 = st3.copy(case2)

    # Here is the situation now
    #
    #   cases      O case2        O case1
    #              |              |
    #   stages     |--------------.->X st1
    #              |              |
    #              |--------------.->X st2
    #              |              |
    #              -->X st4       -->X st3

    # deleting st2, calling Case.__delitem__
    del case1[1]

    # verifying that st3 and st4 have been deleted as a result
    assert_that(is_not_referenced(st1, history), equal_to(False))
    assert_that(is_not_referenced(st2, history), equal_to(True))
    assert_that(is_not_referenced(st3, history), equal_to(True))
    assert_that(is_not_referenced(st4, history), equal_to(True))

    # assert st1 has no Stage child
    for mychild in st1.child_nodes:
       assert_that(mychild, is_not(instance_of(Stage)))


#------------------------------------------------------------------------------
def test_copy_simple_command():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    stage = case.create_stage('Stage_1')
    assert_that(stage, has_length(0))

    cmd = stage.add_command('DEFI_MATERIAU')

    assert_that(stage, has_length(1))

    cmd2 = cmd.copy()
    assert_that(stage, has_length(2))

    cmd3 = cmd.copy()
    assert_that(stage, has_length(3))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_copy_stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    stage1 = case.create_stage('Stage_1')
    stage1('LIRE_MAILLAGE').init({'UNITE': {20: 'test.med'}})

    assert_that(stage1, has_length(1))
    assert_that(stage1.handle2info[20].filename, equal_to('test.med'))

    stage2 = stage1.copy()

    assert_that(stage2, has_length(1))
    assert_that(stage2.handle2info[20].filename, equal_to('test.med'))

    #--------------------------------------------------------------------------
    pass


def test_adlv100a():
    # origin of issue25975
    """Test for copy on adlv100a"""
    import os
    import os.path as osp
    adlv100a = osp.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'export', 'adlv100a.comm')

    history = History()
    case = history.create_case()
    orig = case.import_stage(adlv100a)
    assert_that(orig, has_length(33))

    new = orig.copy(case)
    assert_that(new, has_length(33))


def test_cmd_dependence():
    """Test intra-stage command dependence after copy."""
    #--------------------------------------------------------------------------

    history = History()
    cc = history.create_case(':1:')

    # create a content with a dependence between commands
    st1 = cc.create_stage(':a:')
    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)

load=AFFE_CHAR_CINE(MODELE=model,
                    MECA_IMPO=(_F(GROUP_MA='Sym_x',
                                  DX=0.0,),
                               _F(GROUP_NO='Sym_y',
                                  DY=0.0,),),)
"""
    comm2study(text, st1)

    # check that duplicating stage preserves command dependencies
    rc = history.create_case(':2:')
    st2 = st1.copy(rc)

    #
    mesh1 = cc[':a:']['mesh']
    model1 = cc[':a:']['model']
    load1 = cc[':a:']['load']

    mesh2 = rc[':a:']['mesh']
    model2 = rc[':a:']['model']
    load2 = rc[':a:']['load']

    #
    assert_that(mesh1, is_in(model1.parent_nodes))
    assert_that(model1, is_in(mesh1.child_nodes))

    #
    assert_that(mesh2, is_in(model2.parent_nodes))
    assert_that(model2, is_in(mesh2.child_nodes))

    #
    assert_that(mesh1, is_not(is_in(model2.parent_nodes)))
    assert_that(model1, is_not(is_in(mesh2.child_nodes)))
    assert_that(mesh2, is_not(is_in(model1.parent_nodes)))
    assert_that(model2, is_not(is_in(mesh1.child_nodes)))

    # check that storage has the right command instances
    assert_that(rc[':a:']['model']['MAILLAGE'], is_(mesh2))
    assert_that(cc[':a:']['model']['MAILLAGE'], is_(mesh1))

    #
    assert_that(model1, is_in(load1.parent_nodes))
    assert_that(load1, is_in(model1.child_nodes))

    #
    assert_that(model2, is_in(load2.parent_nodes))
    assert_that(load2, is_in(model2.child_nodes))

    #
    assert_that(model1, is_not(is_in(load2.parent_nodes)))
    assert_that(load1, is_not(is_in(model2.child_nodes)))
    assert_that(model2, is_not(is_in(load1.parent_nodes)))
    assert_that(load2, is_not(is_in(model1.child_nodes)))

    # check that storage has the right command instances
    assert_that(rc[':a:']['load']['MODELE'], is_(model2))
    assert_that(cc[':a:']['load']['MODELE'], is_(model1))

    #--------------------------------------------------------------------------
    # now check a command copy WITHIN a stage
    copy = st1['model'].copy()
    copy.rename('copy')

    # parent relationship shall be preserved
    mesh1 = cc[':a:']['mesh']
    model1 = cc[':a:']['model']
    copy1 = cc[':a:']['copy']
    load1 = cc[':a:']['load']

    # check original parenthood
    assert_that(mesh1, is_in(model1.parent_nodes))
    assert_that(model1, is_in(mesh1.child_nodes))

    # check copy parenthood
    assert_that(mesh1, is_in(copy1.parent_nodes))
    assert_that(copy1, is_in(mesh1.child_nodes))

    # check original descendants
    assert_that(model1, is_in(load1.parent_nodes))
    assert_that(load1, is_in(model1.child_nodes))

    # check copy descendants: should be empty
    assert_that(copy1, is_not(is_in(load1.parent_nodes)))
    assert_that(copy1.child_nodes, equal_to([]))

    #--------------------------------------------------------------------------
    # now check a command copy WITHIN a stage
    copy = st2['model'].copy()
    copy.rename('copy')

    # parent relationship shall be preserved
    mesh1 = rc[':a:']['mesh']
    model1 = rc[':a:']['model']
    copy1 = rc[':a:']['copy']
    load1 = rc[':a:']['load']

    # check original parenthood
    assert_that(mesh1, is_in(model1.parent_nodes))
    assert_that(model1, is_in(mesh1.child_nodes))

    # check copy parenthood
    assert_that(mesh1, is_in(copy1.parent_nodes))
    assert_that(copy1, is_in(mesh1.child_nodes))

    # check original descendants
    assert_that(model1, is_in(load1.parent_nodes))
    assert_that(load1, is_in(model1.child_nodes))

    # check copy descendants: should be empty
    assert_that(copy1, is_not(is_in(load1.parent_nodes)))
    assert_that(copy1.child_nodes, equal_to([]))


def test_interstage_cmd_dependence():
    """Test inter-stage command dependence after copy."""
    #--------------------------------------------------------------------------
    history = History()
    cc = history.create_case(':1:')

    # create a content with a dependence between commands
    st1 = cc.create_stage(':a:')
    st2 = cc.create_stage(':b:')
    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""

    text2 = \
"""
load=AFFE_CHAR_CINE(MODELE=model,
                    MECA_IMPO=(_F(GROUP_MA='Sym_x',
                                  DX=0.0,),
                               _F(GROUP_NO='Sym_y',
                                  DY=0.0,),),)
"""
    comm2study(text1, st1)
    comm2study(text2, st2)

    # check that duplicating stage preserves command dependencies
    rc = cc.copy(':2:')
    rc.copy_shared_stages_from(1)

    #
    mesh1 = cc[':a:']['mesh']
    model1 = cc[':a:']['model']
    load1 = cc[':b:']['load']

    mesh2 = rc[':a:']['mesh']
    model2 = rc[':a:']['model']
    load2 = rc[':b:']['load']

    #
    assert_that(mesh1, is_in(model1.parent_nodes))
    assert_that(model1, is_in(mesh1.child_nodes))

    #
    assert_that(mesh2, is_in(model2.parent_nodes))
    assert_that(model2, is_in(mesh2.child_nodes))

    #
    assert_that(mesh1, is_not(is_in(model2.parent_nodes)))
    assert_that(model1, is_not(is_in(mesh2.child_nodes)))
    assert_that(mesh2, is_not(is_in(model1.parent_nodes)))
    assert_that(model2, is_not(is_in(mesh1.child_nodes)))

    # check that storage has the right command instances
    assert_that(rc[':a:']['model']['MAILLAGE'], is_(mesh2))
    assert_that(cc[':a:']['model']['MAILLAGE'], is_(mesh1))

    #
    assert_that(model1, is_in(load1.parent_nodes))
    assert_that(load1, is_in(model1.child_nodes))

    #
    assert_that(model2, is_in(load2.parent_nodes))
    assert_that(load2, is_in(model2.child_nodes))

    #
    assert_that(model1, is_not(is_in(load2.parent_nodes)))
    assert_that(load1, is_not(is_in(model2.child_nodes)))
    assert_that(model2, is_not(is_in(load1.parent_nodes)))
    assert_that(load2, is_not(is_in(model1.child_nodes)))

    # check that storage has the right command instances
    assert_that(rc[':b:']['load']['MODELE'], is_(model2))
    assert_that(cc[':b:']['load']['MODELE'], is_(model1))

def test_text_stage_duplication():
    #--------------------------------------------------------------------------
    history = History()
    cc = history.create_case(':1:')

    # create a content with a dependence between commands
    st1 = cc.create_stage(':a:')
    st1.use_text_mode()
    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""
    st1.dataset.text = text

    # check that duplicating stage preserves command dependencies
    rc = history.create_case(':2:')
    st2 = st1.copy(rc)

    # check that the text has been copied
    assert_that(st2.dataset.text, equal_to(text))

#------------------------------------------------------------------------------
def test_copy_complex_stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE()

MATER = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
    ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER, TOUT='OUI'), MAILLAGE=MAIL_Q)

MODELUPG = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MODELUPQ = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MODELUPL = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UP', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MATMUPG = CALC_MATR_ELEM(
    CHAM_MATER=CHMAT_Q, MODELE=MODELUPG, OPTION='MASS_MECA'
)

FIN()
"""
    comm2study(text, stage)

    assert_that(stage, has_length(9))

    cmd = stage['MAIL_Q']
    dup = cmd.copy()
    assert_that(cmd * dup, none())
    assert_that(stage, has_length(10))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_misc():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage0 = case.create_stage()
    assert_that(stage0.is_graphical_mode(), equal_to(True))

    stage1 = case.create_stage()
    assert_that(stage1.is_graphical_mode(), equal_to(True))

    #--------------------------------------------------------------------------
    assert_that(stage0.name, equal_to('Stage_1'))
    assert_that(stage1.name, equal_to('Stage_2'))

    stage1.rename('Stage_1')
    assert_that(stage1.name, equal_to('Stage_1'))

    #--------------------------------------------------------------------------
    assert_that(stage0, has_length(0))

    stage0.add_command('DEFI_MATERIAU', 'Acier')

    assert_that('Acier', is_in(stage0))

    assert_that(stage0, has_length(1))

    stage0.clear()

    assert_that(stage0, has_length(0))
    #--------------------------------------------------------------------------
    stage0.database = '/path/db0'
    assert_that(stage0.database, equal_to('/path/db0'))
    assert_that(calling(setattr).with_args(stage1, "database", "/path/db1"),
                raises(ValueError))


#------------------------------------------------------------------------------
def test_append_text():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=20)

MATER = DEFI_MATERIAU(ECRO_LINE=_F(D_SIGM_EPSI=-1950.0,
                                   SY=3.0),
                      ELAS=_F(E=30000.0,
                              NU=0.2,
                              RHO=2764.0))

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER,
                                TOUT='OUI'),
                        MAILLAGE=MAIL_Q)
"""
    stage = case.create_stage()
    stage.use_text_mode()
    stage.set_text(text)

    stage.use_graphical_mode()
    assert_that(stage, has_length(3))

    #--------------------------------------------------------------------------
    stage.use_text_mode()
    assert_that(check_text_eq(stage.get_text(), text))

    #--------------------------------------------------------------------------
    text = \
"""
MODELUPG = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MODELUPQ = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MODELUPL = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UP', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MATMUPG = CALC_MATR_ELEM(
    CHAM_MATER=CHMAT_Q, MODELE=MODELUPG, OPTION='MASS_MECA'
)
"""

    stage.append_text(text)

    stage.use_graphical_mode()
    assert_that(stage, has_length(7))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_export_stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    text = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=20)

MATER = DEFI_MATERIAU(ECRO_LINE=_F(D_SIGM_EPSI=-1950.0,
                                   SY=3.0),
                      ELAS=_F(E=30000.0,
                              NU=0.2,
                              RHO=2764.0))

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER,
                                TOUT='OUI'),
                        MAILLAGE=MAIL_Q)
""".strip()

    stage = case.create_stage()
    stage.use_text_mode()
    stage.set_text(text)

    from tempfile import mkstemp
    filename = mkstemp(prefix='stage' + '-', suffix='comm')[1]
    stage.export(filename, lang='en')

    stage.use_graphical_mode()
    assert_that(stage, has_length(3))

    stage.delete()

    #--------------------------------------------------------------------------
    stage2 = case.import_stage(filename)
    assert_that(stage2.is_graphical_mode(), equal_to(True))
    assert_that(stage2, has_length(5))

    filename2 = mkstemp(prefix='stage' + '-', suffix='comm')[1]
    stage2.export(filename2)

    try:
        import filecmp
        assert_that(filecmp.cmp(filename, filename2, shallow=False),
                    equal_to(True))
    except:
        print(filename, filename2)
        raise

    import os
    os.remove(filename)
    os.remove(filename2)

def test_unicode():
    import os
    history = History()
    case = history.current_case

    comm = os.path.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'comm2study', 'unicode_strings.comm')
    comm2 = os.path.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'comm2study', 'unicode_stringsres.comm')
    with open(comm, 'rb') as file:
        text = file.read()
    with open(comm2, 'rb') as file:
        text_res = file.read()
    assert_that(u"coding=utf-8", is_not(is_in(text.decode('iso-8859-1'))))

    stage = case.create_stage()
    stage.use_text_mode()
    stage.set_text(text)

    from tempfile import mkstemp
    filename = mkstemp(prefix='stage' + '-', suffix='comm')[1]
    stage.export(filename)

    with open(filename, 'rb') as fexport:
        text_out = fexport.read().decode('utf-8')
    assert_that(text_out, equal_to(text_res.decode('iso-8859-1')))

#------------------------------------------------------------------------------
def test_validate_stage_in_text_mode():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage("Stage")
    cmd1 = stage.add_command('DEFI_GROUP')
    stage.use_text_mode()

    from asterstudy.datamodel.general import Validity
    assert_that(stage.check(), equal_to(Validity.Nothing))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_dataset_create():
    #--------------------------------------------------------------------------
    from asterstudy.datamodel.dataset import DataSet
    assert_that(calling(DataSet.factory).with_args(-1), raises(NotImplementedError))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_compare():
    #--------------------------------------------------------------------------
    history = History()
    case1 = history.current_case
    case2 = history.create_case()

    assert_that(case1.name, is_not(equal_to(case2.name)))
    assert_that(calling(case1.__mul__).with_args(case2), raises(AssertionError))

    case1.name = case2.name
    assert_that(case1 * case2, none())

    stage1 = case1.create_stage()
    assert_that(calling(case1.__mul__).with_args(case2), raises(AssertionError))

    stage2 = case2.create_stage()
    assert_that(stage1 * stage2, none())
    assert_that(case1 * case2, none())

    #--------------------------------------------------------------------------
    stage1.handle2info[1]
    assert_that(calling(stage1.__mul__).with_args(stage2), raises(AssertionError))

    stage2.handle2info[1].filename = 'xxx'
    assert_that(calling(stage1.__mul__).with_args(stage2), raises(AssertionError))

    stage1.handle2info[1].filename = 'yyy'
    assert_that(calling(stage1.__mul__).with_args(stage2), raises(AssertionError))

    stage1.handle2info[1].filename = 'xxx'
    assert_that(stage1 * stage2, none())

    stage1('PRE_GMSH').init({'UNITE_GMSH': {2: 'gmsh.file'}})
    assert_that(calling(stage1.__mul__).with_args(stage2), raises(AssertionError))

    stage2('PRE_GMSH').init({'UNITE_GMSH': {2: 'gmsh.file'}})
    assert_that(stage1 * stage2, none())

    stage1.handle2info[1].attr = 'in'
    assert_that(calling(stage1.__mul__).with_args(stage2), raises(AssertionError))

    stage2.handle2info[1].attr = 'in'
    assert_that(stage1 * stage2, none())

    stage1.handle2info[1].embedded = True
    assert_that(calling(stage1.__mul__).with_args(stage2), raises(AssertionError))

    stage2.handle2info[1].embedded = True
    assert_that(stage1 * stage2, none())

    del stage1[0]
    assert_that(calling(stage1.__mul__).with_args(stage2), raises(AssertionError))

    del stage2[0]
    assert_that(stage1 * stage2, none())

    #--------------------------------------------------------------------------
    stage2.use_text_mode()
    assert_that(calling(stage1.__mul__).with_args(stage2), raises(AssertionError))
    assert_that(calling(case1.__mul__).with_args(case2), raises(AssertionError))

    stage1.use_text_mode()
    assert_that(stage1 * stage2, none())
    assert_that(case1 * case2, none())

    stage1.set_text('xxx')
    assert_that(calling(stage1.__mul__).with_args(stage2), raises(AssertionError))
    assert_that(calling(case1.__mul__).with_args(case2), raises(AssertionError))

    stage2.set_text('xxx')
    assert_that(stage1 * stage2, none())
    assert_that(case1 * case2, none())


def test_partial_conv():
    """Test for partial conversion"""
    history = History()
    case = history.current_case

    text = \
"""
MAIL_Q = LIRE_MAILLAGE()

MATER = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
    ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)

import matplotlib
matplotlib.plot(data)
# if is_ok:
#     IMPR_RESU(MAILLAGE=MAIL_Q)
"""
    stage = case.create_stage()
    stage.use_text_mode()
    stage.set_text(text)

    assert_that(calling(stage.use_graphical_mode),
                raises(ConversionError, "Python statements"))

    stage.use_graphical_mode(ConversionLevel.NoFail | ConversionLevel.Partial)
    assert_that(case, has_length(2))
    assert_that(stage, has_length(2))
    assert_that(case[0].is_graphical_mode())
    assert_that(case[0], has_length(2))
    assert_that(case[0][0].name, equal_to("MAIL_Q"))
    assert_that(case[0][1].name, equal_to("MATER"))

    assert_that(case[1].name, case[0].name + "_1")
    assert_that(case[1].is_text_mode())


def test_partial_conv_empty():
    """Test for conversion with no graphical stage"""
    history = History()
    case = history.current_case

    text = \
"""
import os

mesh = LIRE_MAILLAGE()
"""
    stage = case.create_stage()
    stage.use_text_mode()
    stage.set_text(text)

    assert_that(calling(stage.use_graphical_mode),
                raises(ConversionError, "Python statements"))

    stage.use_graphical_mode(ConversionLevel.NoFail | ConversionLevel.Partial)
    assert_that(stage.is_text_mode(), equal_to(True))
    assert_that(stage.conversion_report.get_errors(), empty())


def test_conv_report():
    """Test for conversion report"""
    history = History()
    case = history.current_case

    text = \
"""
mesh = LIRE_MAILLAGE()

import matplotlib

IMPR_RESU(MAILLAGE=mesh)
"""
    stage = case.create_stage()
    stage.use_text_mode()
    stage.set_text(text)

    try:
        stage.use_graphical_mode()
    except ConversionError as exc:
        report = stage.conversion_report.get_errors()
        assert_that(report, contains_string("Python statements"))

    # ConversionError is not picklable (and hasn't to be)
    assert_that(stage.conversion_report.get_errors(), is_not(empty()))
    pickle.dumps(stage)
    assert_that(stage.conversion_report.get_errors(), empty())


def test_get_cmd_by_index():
    history = History()
    case = history.current_case
    stage = case.create_stage()
    cmd = stage.add_command('LIRE_MAILLAGE')
    assert_that(stage.get_cmd_by_index(0), same_instance(cmd))
    assert_that(stage.get_cmd_by_index(1), none())


def test_copy_deps1():
    text = \
"""
mesh = LIRE_MAILLAGE()

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='3D', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)
    assert_that(stage, has_length(2))
    assert_that(stage[1].depends_on(stage[0]))

    stage2 = stage.copy(case)
    assert_that(stage2, has_length(2))
    assert_that(stage2[1].depends_on(stage2[0]))
    assert_that(stage2[0], is_not(stage[0]))
    assert_that(stage2[1], is_not(stage[1]))


def test_copy_with_hidden():
    text = \
"""
MACR_ADAP_MAIL(
    ADAPTATION="RAFFINEMENT_UNIFORME",
    MAILLAGE_NP1=CO("meshout")
)
"""
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)
    assert_that(stage, has_length(2))
    assert_that(stage[1].depends_on(stage[0]))

    stage2 = stage.copy(case)
    assert_that(stage2, has_length(2))
    assert_that(stage2[1].depends_on(stage2[0]))
    assert_that(stage2[0], is_not(stage[0]))
    assert_that(stage2[1], is_not(stage[1]))

def test_issue_28124():
    # Test `first_attr` attribute for files
    hist = History()
    case = hist.current_case
    st = case.create_stage(':1:')

    # Test in then out case: should fail during export
    cmd_in = st("LIRE_MAILLAGE")
    cmd_in.init({'UNITE': {20: 'foo.txt'}, 'FORMAT': 'MED'})
    cmd_out = st("IMPR_RESU")
    cmd_out.init({'RESU': {'MAILLAGE': cmd_in}, 'UNITE': {20: 'foo.txt'}})
    assert_that(st.handle2info[20].first_attr, equal_to(FileAttr.In))

    # Test file does not appear
    st.handle2info[81].filename = 'I_am_not_used.txt'
    assert_that(st.handle2info[81].first_attr, equal_to(FileAttr.No))

    # Test text stage
    st.use_text_mode()
    assert_that(st.handle2info[20].first_attr, equal_to(FileAttr.InOut))


def test_issue_28124_out_in():
    # Test `first_attr` attribute for files
    hist = History()
    case = hist.current_case
    st = case.create_stage(':1:')

    # Test in then out case
    cmd_out = st("CREA_LIB_MFRONT")
    cmd_out.init({'UNITE_MFRONT': {38: 'behav.mfront'},
                  'UNITE_LIBRAIRIE': {39: 'lib.so'}})

    cmd_in = st("LIRE_RESU")
    cmd_in.init({'FORMAT': 'MED', 'UNITE': 39})

    assert_that(st.handle2info[38].first_attr, equal_to(FileAttr.In))
    assert_that(st.handle2info[39].first_attr, equal_to(FileAttr.Out))

    # Test text stage
    st.use_text_mode()
    assert_that(st.handle2info[38].first_attr, equal_to(FileAttr.In))
    assert_that(st.handle2info[39].first_attr, equal_to(FileAttr.InOut))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
