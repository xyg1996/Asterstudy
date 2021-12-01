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

"""Automatic tests for export feature."""


import tempfile
import unittest

from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.history import History
from asterstudy.datamodel.result import RunOptions, StateOptions
from asterstudy.datamodel.study2comm import study2comm
from asterstudy.datamodel.undo_redo import UndoRedo
from hamcrest import *
from testutils import attr, tempdir
from testutils.tools import add_database, check_text_eq, check_text_ne

Skip = RunOptions.Skip
Reuse = RunOptions.Reuse
Execute = RunOptions.Execute

Waiting = StateOptions.Waiting
Success = StateOptions.Success

#------------------------------------------------------------------------------
def _setup(tmpdir):
    #--------------------------------------------------------------------------
    history = History()
    history.folder = tempfile.mkdtemp(dir=tmpdir, prefix='history-')
    undo_redo = UndoRedo(history)
    undo_redo.model.autocopy_enabled = True

    cc = undo_redo.model.create_case(':1:')
    assert_that(cc, is_(undo_redo.model[1]))
    assert_that(cc, is_(undo_redo.model.current_case))

    #--------------------------------------------------------------------------
    stage1 = cc.create_stage(':a:')
    assert_that(':a:', is_in(cc))

    #--------------------------------------------------------------------------
    stage2 = cc.create_stage(':b:')
    assert_that(':b:', is_in(cc))

    text2 = \
"""
mesh = LIRE_MAILLAGE(FORMAT='ASTER', UNITE=20)
"""
    comm2study(text2, stage2)

    #--------------------------------------------------------------------------
    rc = undo_redo.model.create_run_case(name=':2:', reusable_stages=[0, 1])

    assert_that(rc, is_in(undo_redo.model.run_cases))
    assert_that(rc, is_not(undo_redo.model.current_case))
    assert_that(':a:', is_in(rc))
    assert_that(':b:', is_in(rc))

    rc.run()
    add_database(rc[0].folder)
    add_database(rc[1].folder)

    #--------------------------------------------------------------------------
    undo_redo.commit("test")

    #--------------------------------------------------------------------------
    # CC:
    assert_that(cc.can_reuse(cc[':a:']), equal_to(True))
    assert_that(cc.can_reuse(cc[':b:']), equal_to(True))
    assert_that(cc.run_options(cc[':a:']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc[':b:']), equal_to(Skip | Reuse | Execute))
    #: CC shares :a: somehow from RC, but not :b: !!!
    assert_that(cc[':a:'].state, equal_to(Success))
    assert_that(cc[':b:'].state, equal_to(Success))
    assert_that(cc[':a:'], equal_to(rc[':a:']))
    assert_that(cc[':b:'], equal_to(rc[':b:']))

    #--------------------------------------------------------------------------
    # RC:
    assert_that(rc[':a:'].state, equal_to(Success))
    assert_that(rc[':b:'].state, equal_to(Success))

    #--------------------------------------------------------------------------
    return undo_redo

#------------------------------------------------------------------------------
@tempdir
def test_modify_command(tmpdir):
    #--------------------------------------------------------------------------
    undo_redo = _setup(tmpdir)
    undo_redo.model.autocopy_enabled = True

    #--------------------------------------------------------------------------
    cc = undo_redo.model[':1:']

    rc = undo_redo.model[':2:']

    #--------------------------------------------------------------------------
    text1 = \
"""
mesh = LIRE_MAILLAGE(FORMAT='ASTER',
                     UNITE=20)
"""

    text = study2comm(cc[':b:'])
    assert_that(check_text_eq(text, text1))

    cc[':b:']['mesh']['FORMAT'] = 'MED'

    text1 = \
"""
mesh = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)
"""

    text = study2comm(cc[':b:'])
    assert_that(check_text_eq(text, text1))

    text = study2comm(rc[':b:'])
    assert_that(check_text_ne(text, text1))

    #--------------------------------------------------------------------------
    # CC:
    assert_that(cc.can_reuse(cc[':a:']), equal_to(True))
    assert_that(cc.can_reuse(cc[':b:']), equal_to(False))
    assert_that(cc.run_options(cc[':a:']), equal_to(Skip | Reuse | Execute))
    assert_that(cc.run_options(cc[':b:']), equal_to(Skip | Execute))
    #: CC shares :a: somehow from RC, but not :b: !!!
    assert_that(cc[':a:'].state, equal_to(Success))
    assert_that(cc[':b:'].state, is_not(equal_to(Success)))
    assert_that(cc[':a:'], equal_to(rc[':a:']))
    assert_that(cc[':b:'], is_not(rc[':b:'])) # !!!

    #--------------------------------------------------------------------------
    # RC:
    assert_that(rc[':a:'].state, equal_to(Success))
    assert_that(rc[':b:'].state, equal_to(Success))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
