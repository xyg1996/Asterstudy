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

"""Automatic tests for auto-copy feature.

Checks that when modifying something in the current case (the only
one that can be modified), the corresponding stage is automatically
copied. The current case keeps the original, the run case has the copy.
"""


import unittest
from hamcrest import *

from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.study2comm import study2comm

from asterstudy.datamodel.undo_redo import UndoRedo
from asterstudy.datamodel.history import History

from asterstudy.common.utilities import enable_autocopy

from testutils.tools import check_text_eq, check_text_ne

#------------------------------------------------------------------------------
def _setup():
    # Here is what is creates:
    #          current-case         run-case
    #             case1              case2
    #              |                   |
    # stage 1      --------------------o
    #              |                   |
    # stage 2      --------------------o
    #              |                   |
    # stage 3      --------------------o
    #
    # Any modification to the stages should apply to case1 (the current),
    # not case2 that is already ran and considered read-only.
    #--------------------------------------------------------------------------
    undo_redo = UndoRedo(History())

    case1 = undo_redo.model.create_case(':1:')
    assert_that(case1, is_(undo_redo.model[1]))

    #--------------------------------------------------------------------------
    stage1 = case1.create_stage(':a:')
    assert_that(':a:', is_in(case1))

    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)
"""
    comm2study(text1, stage1)

    #--------------------------------------------------------------------------
    stage2 = case1.create_stage(':b:')
    assert_that(':b:', is_in(case1))

    text2 = \
"""
mesh = MODI_MAILLAGE(
    reuse=mesh, MAILLAGE=mesh, ORIE_PEAU_2D=_F(GROUP_MA='groupname')
)

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""

    comm2study(text2, stage2)

    #--------------------------------------------------------------------------
    stage3 = case1.create_stage(':c:')
    assert_that(':c:', is_in(case1))

    text3 = \
"""
mesh = MODI_MAILLAGE(
    reuse=mesh, MAILLAGE=mesh, ORIE_PEAU_2D=_F(GROUP_MA='groupname')
)

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""

    comm2study(text3, stage3)

    #--------------------------------------------------------------------------
    case2 = undo_redo.model.create_run_case(None, name=':2:')

    assert_that(':a:', is_in(case2))
    assert_that(':b:', is_in(case2))

    #--------------------------------------------------------------------------
    undo_redo.commit("test")

    return undo_redo

#------------------------------------------------------------------------------
def _setup_3_cases():
    #--------------------------------------------------------------------------
    undo_redo = UndoRedo(History())

    case1 = undo_redo.model.create_case(':1:')
    assert_that(case1, is_(undo_redo.model[1]))

    #--------------------------------------------------------------------------
    # create first stage
    stage1 = case1.create_stage(':a:')
    assert_that(':a:', is_in(case1))

    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)
"""
    comm2study(text1, stage1)

    #--------------------------------------------------------------------------
    # create second stage
    stage2 = case1.create_stage(':b:')
    assert_that(':b:', is_in(case1))

    text2 = \
"""
mesh = MODI_MAILLAGE(
    reuse=mesh, MAILLAGE=mesh, ORIE_PEAU_2D=_F(GROUP_MA='groupname')
)

model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""

    comm2study(text2, stage2)

    #--------------------------------------------------------------------------
    # create a run case with both stages executed

    case2 = undo_redo.model.create_run_case(name=':2:')
    case2.run()

    assert_that(':a:', is_in(case2))
    assert_that(':b:', is_in(case2))

    #--------------------------------------------------------------------------
    # create a run case with only the second stage executed

    case3 = undo_redo.model.create_run_case(1, name=':3:')
    case3.run()

    assert_that(':a:', is_in(case3))
    assert_that(':b:', is_in(case3))

    #--------------------------------------------------------------------------
    undo_redo.commit("test")
    return undo_redo

#------------------------------------------------------------------------------
def test_add_new_stage():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(case1, has_length(3))

    case2 = undo_redo.model[':2:']
    assert_that(case1, has_length(3))

    #--------------------------------------------------------------------------
    stage4 = case2.create_stage(':b:')

    assert_that(case2, has_length(4))
    assert_that(case1, has_length(3))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_remove_stage_1():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(case1, has_length(3))

    case2 = undo_redo.model[':2:']
    assert_that(case1, has_length(3))

    #--------------------------------------------------------------------------
    case2.detach(case2[':b:'])

    assert_that(case2, has_length(1))
    assert_that(case1, has_length(3))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_remove_stage_2():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(case1, has_length(3))

    case2 = undo_redo.model[':2:']
    assert_that(case1, has_length(3))

    #--------------------------------------------------------------------------
    case1[':b:'].delete(user_deletion=True)

    assert_that(case1, has_length(1))
    assert_that(case2, has_length(3))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_add_command():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(case1[':b:'], has_length(2))

    case2 = undo_redo.model[':2:']
    assert_that(case2[':b:'], has_length(2))

    #--------------------------------------------------------------------------
    case1[':b:']('FIN')

    assert_that(case1[':b:'], has_length(3))
    assert_that(case2[':b:'], has_length(2))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_add_command_2():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(case1[':b:'], has_length(2))

    case2 = undo_redo.model[':2:']
    assert_that(case2[':b:'], has_length(2))

    #--------------------------------------------------------------------------
    case1[':b:'].add_command('FIN')

    assert_that(case1[':b:'], has_length(3))
    assert_that(case2[':b:'], has_length(2))

    #--------------------------------------------------------------------------
    pass

def test_remove_command_1():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(case1[':b:'], has_length(2))

    case2 = undo_redo.model[':2:']
    assert_that(case2[':b:'], has_length(2))

    #--------------------------------------------------------------------------
    case1[':b:']['model'].delete(user_deletion=True)

    assert_that(case1[':b:'], has_length(1))
    assert_that(case2[':b:'], has_length(2))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_modify_command_1():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']

    case2 = undo_redo.model[':2:']

    #--------------------------------------------------------------------------
    case1[':a:']['mesh']['FORMAT'] = 'MED'

    text1 = \
"""
mesh = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)
"""

    text = study2comm(case1[':a:'])
    assert_that(check_text_eq(text, text1))

    text = study2comm(case2[':a:'])
    assert_that(check_text_ne(text, text1))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_modify_command_2():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']

    case2 = undo_redo.model[':2:']

    #--------------------------------------------------------------------------
    cmd = case1[':a:']['mesh']
    cmd.init({'FORMAT':'MED', 'UNITE':20})

    text1 = \
"""
mesh = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)
"""

    text = study2comm(case1[':a:'])
    assert_that(check_text_eq(text, text1))

    text = study2comm(case2[':a:'])
    assert_that(check_text_ne(text, text1))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_modify_unite_1():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']

    case2 = undo_redo.model[':2:']

    #--------------------------------------------------------------------------
    assert_that(case1[':a:']['mesh']['UNITE'].filename, none())

    case1[':a:']['mesh']['UNITE'].value = {20: 'dummy.txt'}

    assert_that(case1[':a:']['mesh']['UNITE'].filename, equal_to('dummy.txt'))
    assert_that(case2[':a:']['mesh']['UNITE'].filename, none())

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_modify_unite_2():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']

    case2 = undo_redo.model[':2:']

    #--------------------------------------------------------------------------
    assert_that(case1[':a:']['mesh']['UNITE'].filename, none())

    cmd = case1[':a:']['mesh']
    cmd.init( {'UNITE': {20:'dummy.txt'} } )

    assert_that(case1[':a:']['mesh']['UNITE'].filename, equal_to('dummy.txt'))
    assert_that(case2[':a:']['mesh']['UNITE'].filename, none())

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_modify_text():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    case1[':c:'].use_text_mode()
    case1[':b:'].use_text_mode()

    case2 = undo_redo.model[':2:']
    case2[':c:'].use_text_mode()
    case2[':b:'].use_text_mode()

    #--------------------------------------------------------------------------
    text = \
"""
mesh = MODI_MAILLAGE(
    reuse=mesh, MAILLAGE=mesh, ORIE_PEAU_2D=_F(GROUP_MA='groupname')
)
"""

    assert_that(case1[':b:'].get_text(), is_not(equal_to(text)))
    assert_that(case2[':b:'].get_text(), is_not(equal_to(text)))

    #--------------------------------------------------------------------------
    case1[':b:'].set_text(text)

    assert_that(case1[':b:'].get_text(), equal_to(text))
    assert_that(case2[':b:'].get_text(), is_not(equal_to(text)))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_copy_command_1():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(case1[':a:'], has_length(1))

    case2 = undo_redo.model[':2:']
    assert_that(case2[':a:'], has_length(1))

    #--------------------------------------------------------------------------
    case1[':a:']['mesh'].copy()

    assert_that(case1[':a:'], has_length(2))
    assert_that(case2[':a:'], has_length(1))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_copy_command_2():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(case1[':a:'], has_length(1))

    case2 = undo_redo.model[':2:']
    assert_that(case2[':a:'], has_length(1))

    #--------------------------------------------------------------------------
    cmd = case1[':a:']['mesh']
    cmd.copy()

    assert_that(case1[':a:'], has_length(2))
    assert_that(case2[':a:'], has_length(1))

    #--------------------------------------------------------------------------
    pass
#------------------------------------------------------------------------------
def test_switch_stage_mode():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(case1[':b:'].is_graphical_mode(), equal_to(True))

    case2 = undo_redo.model[':2:']
    assert_that(case2[':b:'].is_graphical_mode(), equal_to(True))

    #--------------------------------------------------------------------------
    case1[':c:'].use_text_mode()
    case1[':b:'].use_text_mode()

    assert_that(case1[':b:'].is_text_mode(), equal_to(True))
    assert_that(case2[':b:'].is_graphical_mode(), equal_to(True))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_rename_stage_1():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(':b:', is_in(case1))
    assert_that(case1[':b:'], is_in(case1))

    case2 = undo_redo.model[':2:']
    assert_that(':b:', is_in(case1))
    assert_that(case2[':b:'], is_in(case2))

    #--------------------------------------------------------------------------
    case1[':b:'].name = ':x:'

    assert_that(':x:', is_in(case1))
    assert_that(':b:', is_not(is_in(case1)))

    assert_that(':b:', is_in(case2))
    assert_that(':x:', is_not(is_in(case2)))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_rename_stage_2():
    #--------------------------------------------------------------------------
    undo_redo = _setup()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    assert_that(':b:', is_in(case1))
    assert_that(case1[':b:'], is_in(case1))

    case2 = undo_redo.model[':2:']
    assert_that(':b:', is_in(case1))
    assert_that(case2[':b:'], is_in(case2))

    #--------------------------------------------------------------------------
    case1[':b:'].rename(':x:')

    assert_that(':x:', is_in(case1))
    assert_that(':b:', is_not(is_in(case1)))

    assert_that(':b:', is_in(case2))
    assert_that(':x:', is_not(is_in(case2)))

#------------------------------------------------------------------------------
def test_3_cases():
    #--------------------------------------------------------------------------

    undo_redo = _setup_3_cases()
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']

    assert_that(':a:', is_in(case1))
    assert_that(case1[':a:'], is_in(case1))

    assert_that(':b:', is_in(case1))
    assert_that(case1[':b:'], is_in(case1))

    #--------------------------------------------------------------------------
    case2 = undo_redo.model[':2:']

    assert_that(':a:', is_in(case2))
    assert_that(case1[':a:'], is_in(case2))

    assert_that(':b:', is_in(case2))
    assert_that(case1[':b:'], is_not(is_in(case2)))
    assert_that(case2[':b:'], is_in(case2))

    #--------------------------------------------------------------------------
    case3 = undo_redo.model[':3:']

    assert_that(':a:', is_in(case2))
    assert_that(case1[':a:'], is_in(case3))

    assert_that(':b:', is_in(case3))
    assert_that(case1[':b:'], is_in(case3))
    assert_that(case2[':b:'], is_not(is_in(case3)))

    assert_that(case1[':a:'].parent_case, same_instance(case2))
    assert_that(case1[':b:'].parent_case, same_instance(case3))

    result = case1[':b:'].result

    #--------------------------------------------------------------------------
    # A modification to the current creates a new stage
    case1[':b:'].name = ':x:'

    assert_that(':x:', is_in(case1))
    assert_that(':b:', is_not(is_in(case1)))

    assert_that(':b:', is_in(case2))
    assert_that(':x:', is_not(is_in(case2)))

    assert_that(':b:', is_in(case3))
    assert_that(':x:', is_not(is_in(case3)))

    assert_that(case1[':a:'].parent_case, same_instance(case2))
    assert_that(case1[':x:'].parent_case, same_instance(case1))

    assert_that(case1[':x:'].result, is_not(same_instance(result)))
    assert_that(case3[':b:'].result, same_instance(result))

    result = case1[':a:'].result

    #--------------------------------------------------------------------------
    case1[':a:']['mesh']['FORMAT'] = 'MED'
    text1 = \
"""
mesh = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)
"""

    text = study2comm(case1[':a:'])
    assert_that(check_text_eq(text, text1))

    text = study2comm(case2[':a:'])
    assert_that(check_text_ne(text, text1))

    text = study2comm(case3[':a:'])
    assert_that(check_text_ne(text, text1))

    #--------------------------------------------------------------------------
    # by now, cases ':2:' and ':3:' share the same stage ':a:'

    assert_that(case2[':a:'], same_instance(case3[':a:']))

    assert_that(case1[':a:'].result, is_not(same_instance(result)))
    assert_that(case2[':a:'].result, same_instance(result))
    assert_that(case3[':a:'].result, same_instance(result))
    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_3_cases_2():
    #--------------------------------------------------------------------------
    undo_redo = _setup_3_cases()

    case1 = undo_redo.model[':1:']
    case2 = undo_redo.model[':2:']
    case3 = undo_redo.model[':3:']

    #--------------------------------------------------------------------------
    # add a new stage in ':1:'

    new = case1.create_stage(':c:')

    # under autocopy_enabled mode modify the second stage from ':1:'
    undo_redo.model.autocopy_enabled = True
    case1[':b:']['model'].rename('fem_model')

    #--------------------------------------------------------------------------
    assert_that(len(case1), equal_to(3))
    assert_that(len(case2), equal_to(2))
    assert_that(len(case3), equal_to(2))

    # case1[':b:'] has a child stage, but not case2[':b:']
    assert_that(case1[':b:'].child_stages, equal_to([new]))
    assert_that(case2[':b:'].child_stages, equal_to([]))
    assert_that(case3[':b:'].child_stages, equal_to([]))



def test_modify_files_1():
    #--------------------------------------------------------------------------
    undo_redo = _setup()

    #--------------------------------------------------------------------------
    # automatic copy off
    case1 = undo_redo.model[':1:']
    case2 = undo_redo.model[':2:']
    case1[':a:']['mesh']['UNITE'].value = {20: 'dummy.txt'}
    assert_that(case1[':a:']['mesh']['UNITE'].filename, equal_to('dummy.txt'))
    assert_that(case2[':a:']['mesh']['UNITE'].filename, equal_to('dummy.txt'))

    #--------------------------------------------------------------------------
    # change a file name with automatic copy on
    undo_redo.model.autocopy_enabled = True
    case1[':a:'].handle2info[20].filename = 'fake.txt'

    assert_that(case1[':a:'].handle2info[20].filename, equal_to('fake.txt'))
    assert_that(case2[':a:'].handle2info[20].filename, equal_to('dummy.txt'))
    assert_that(case1[':a:'].handle2file(20), equal_to('fake.txt'))
    assert_that(case2[':a:'].handle2file(20), equal_to('dummy.txt'))
    assert_that(case1[':a:']['mesh']['UNITE'].filename, equal_to('fake.txt'))
    assert_that(case2[':a:']['mesh']['UNITE'].filename, equal_to('dummy.txt'))

    #--------------------------------------------------------------------------
    pass
    #--------------------------------------------------------------------------

def test_context_manager_1():
    #--------------------------------------------------------------------------
    undo_redo = _setup()

    #--------------------------------------------------------------------------
    case1 = undo_redo.model[':1:']
    case2 = undo_redo.model[':2:']

    # `calling_case` is first case2 (context manager)
    # but it is overrideb by case1 inside
    with enable_autocopy(case2):
        case1[':a:']['mesh']['FORMAT'] = 'MED'

    text1 = \
"""
mesh = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)
"""

    text = study2comm(case1[':a:'])
    assert_that(check_text_eq(text, text1))

    text = study2comm(case2[':a:'])
    assert_that(check_text_ne(text, text1))

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
