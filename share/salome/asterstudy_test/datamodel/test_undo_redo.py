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

"""Automatic tests for undo-redo."""
import re
import unittest
from testutils import attr
from asterstudy.common import CFG

from asterstudy.datamodel.undo_redo import UndoRedo, TransactionUndoRedo
from asterstudy.datamodel.history import History

from hamcrest import *

#------------------------------------------------------------------------------
class Test:
    """Test class for undo/redo."""

    def __init__(self):
        """Constructor."""
        self.name = ''
        self.abc = 0
        self.value = None

#------------------------------------------------------------------------------
class UndoRedoEngine(unittest.TestCase):
    """Basic class for testing undo/redo mechanism."""

    @property
    def obj(self):
        return self._obj.model

    @property
    def undo_redo(self):
        return self._obj

    def checkObject(self, name, abc, value):
        """Auxiliary method: check test object's content."""
        self.assertEqual(self.obj.name, name)
        self.assertEqual(self.obj.abc, abc)
        self.assertEqual(self.obj.value, value)

#------------------------------------------------------------------------------
class TestSimpleUndoRedo(UndoRedoEngine):
    """Test case for simple undo/redo mechanism."""

    def setUp(self):
        """Initial set-up for each test case."""
        self._obj = UndoRedo(Test())

    def test(self):
        """Test for conventional undo/redo"""
        undo_redo = self.undo_redo
        # test default state of object
        self.checkObject('', 0, None)
        self.assertEqual(undo_redo.last.name, '')
        self.assertEqual(undo_redo.last.abc, 0)
        self.assertEqual(undo_redo.last.value, None)
        # test default state of undo-redo
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.undo_limit, -1)
        self.assertEqual(undo_redo.current_state, 0)
        # make two commits
        self.obj.name = 'x'
        undo_redo.commit("change name")
        self.obj.value = 10
        undo_redo.commit("change value")
        self.assertEqual(undo_redo.nb_undo, 2)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 2)
        self.assertEqual(undo_redo.undo_messages,
                         ["change value", "change name"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 0, 10)
        # undo one operation
        undo_redo.undo()
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 1)
        self.assertEqual(undo_redo.current_state, 1)
        self.assertEqual(undo_redo.undo_messages, ["change name"])
        self.assertEqual(undo_redo.redo_messages, ["change value"])
        self.checkObject('x', 0, None)
        # undo one more operation
        undo_redo.undo()
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 2)
        self.assertEqual(undo_redo.current_state, 0)
        self.assertEqual(undo_redo.undo_messages, [])
        self.assertEqual(undo_redo.redo_messages,
                         ["change name", "change value"])
        self.checkObject('', 0, None)
        # redo one operation
        undo_redo.redo()
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 1)
        self.assertEqual(undo_redo.current_state, 1)
        self.assertEqual(undo_redo.undo_messages, ["change name"])
        self.assertEqual(undo_redo.redo_messages, ["change value"])
        self.checkObject('x', 0, None)
        # redo one more operation
        undo_redo.redo()
        self.assertEqual(undo_redo.nb_undo, 2)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 2)
        self.assertEqual(undo_redo.undo_messages,
                         ["change value", "change name"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 0, 10)
        # undo two operations
        undo_redo.undo(2)
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 2)
        self.assertEqual(undo_redo.current_state, 0)
        self.assertEqual(undo_redo.undo_messages, [])
        self.assertEqual(undo_redo.redo_messages,
                         ["change name", "change value"])
        self.checkObject('', 0, None)
        # redo two operations
        undo_redo.redo(2)
        self.assertEqual(undo_redo.nb_undo, 2)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 2)
        self.assertEqual(undo_redo.undo_messages,
                         ["change value", "change name"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 0, 10)
        # make local changes
        self.obj.name = "changed"
        self.obj.value = 123
        self.obj.abc = 100
        self.checkObject('changed', 100, 123)
        # test revert
        undo_redo.revert()
        self.checkObject('x', 0, 10)
        self.assertEqual(undo_redo.current_state, 2)
        # set undo limit to 0
        undo_redo.undo_limit = 0
        self.assertEqual(undo_redo.undo_limit, 0)
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 2)
        self.assertEqual(undo_redo.undo_messages, [])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 0, 10)
        # make commit
        self.obj.abc = 999
        undo_redo.commit("change abc")
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 3)
        self.assertEqual(undo_redo.undo_messages, [])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 999, 10)
        # set undo limit to 1
        undo_redo.undo_limit = 1
        self.assertEqual(undo_redo.undo_limit, 1)
        self.assertEqual(undo_redo.current_state, 3)
        self.checkObject('x', 999, 10)
        # make commit
        self.obj.value = 321
        undo_redo.commit("change value")
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 4)
        self.assertEqual(undo_redo.undo_messages, ["change value"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 999, 321)
        # make another commit
        self.obj.name = "y"
        undo_redo.commit("change name")
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 5)
        self.assertEqual(undo_redo.undo_messages, ["change name"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('y', 999, 321)
        # undo
        undo_redo.undo()
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 1)
        self.assertEqual(undo_redo.current_state, 4)
        self.assertEqual(undo_redo.undo_messages, [])
        self.assertEqual(undo_redo.redo_messages, ["change name"])
        self.checkObject('x', 999, 321)
        # make new commit
        self.obj.value = 654
        undo_redo.commit("change value")
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 6)
        self.assertEqual(undo_redo.undo_messages, ["change value"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 999, 654)
        # set undo limit to 2
        undo_redo.undo_limit = 2
        self.assertEqual(undo_redo.undo_limit, 2)
        self.assertEqual(undo_redo.current_state, 6)
        self.checkObject('x', 999, 654)
        # make one more commit
        self.obj.abc = 444
        undo_redo.commit("change abc")
        self.assertEqual(undo_redo.nb_undo, 2)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 7)
        self.assertEqual(undo_redo.undo_messages,
                         ["change abc", "change value"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 444, 654)
        # set undo limit back to 1
        undo_redo.undo_limit = 1
        self.assertEqual(undo_redo.undo_limit, 1)
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 7)
        self.assertEqual(undo_redo.undo_messages,
                         ["change abc"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 444, 654)
        # check last state's behavior
        self.assertEqual(undo_redo.last.name, 'x')
        self.assertEqual(undo_redo.last.abc, 444)
        self.assertEqual(undo_redo.last.value, 654)
        self.obj.name = 'z'
        self.obj.abc = 555
        self.obj.value = 'aaa'
        self.assertEqual(undo_redo.last.name, 'x')
        self.assertEqual(undo_redo.last.abc, 444)
        self.assertEqual(undo_redo.last.value, 654)
        undo_redo.commit("change model")
        self.assertEqual(undo_redo.last.name, 'z')
        self.assertEqual(undo_redo.last.abc, 555)
        self.assertEqual(undo_redo.last.value, 'aaa')

#------------------------------------------------------------------------------
class TestTransactionalUndoRedo(UndoRedoEngine):
    """Test case for transactional undo/redo mechanism."""

    def setUp(self):
        """Initial set-up for each test case."""
        self._obj = TransactionUndoRedo(Test())

    def test(self):
        """Test for transactional undo/redo"""
        undo_redo = self.undo_redo
        # test default state of object
        self.checkObject('', 0, None)
        # test default state of undo-redo
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.undo_limit, -1)
        self.assertEqual(undo_redo.current_state, 0)
        self.assertEqual(undo_redo.opened, False)
        # try to commit, check that exception is raised
        with self.assertRaises(RuntimeError) as exc:
            undo_redo.commit()
        self.assertEqual('There is no open transaction.',
                         exc.exception.args[0])
        # make two commits
        undo_redo.open("change name")
        self.assertEqual(undo_redo.opened, True)

        # try to undo, check that exception is raised
        with self.assertRaises(RuntimeError) as exc:
            undo_redo.undo()

        # try to redo, check that exception is raised
        with self.assertRaises(RuntimeError) as exc:
            undo_redo.redo()

        self.obj.name = 'x'
        undo_redo.commit()
        self.assertEqual(undo_redo.opened, False)
        undo_redo.open("change value")
        self.obj.value = 10
        undo_redo.commit()
        self.assertEqual(undo_redo.nb_undo, 2)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 2)
        self.assertEqual(undo_redo.undo_messages,
                         ["change value", "change name"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 0, 10)
        # undo one operation
        undo_redo.undo()
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 1)
        self.assertEqual(undo_redo.current_state, 1)
        self.assertEqual(undo_redo.undo_messages, ["change name"])
        self.assertEqual(undo_redo.redo_messages, ["change value"])
        self.checkObject('x', 0, None)
        # undo one more operation
        undo_redo.undo()
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 2)
        self.assertEqual(undo_redo.current_state, 0)
        self.assertEqual(undo_redo.undo_messages, [])
        self.assertEqual(undo_redo.redo_messages,
                         ["change name", "change value"])
        self.checkObject('', 0, None)
        # redo one operation
        undo_redo.redo()
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 1)
        self.assertEqual(undo_redo.current_state, 1)
        self.assertEqual(undo_redo.undo_messages, ["change name"])
        self.assertEqual(undo_redo.redo_messages, ["change value"])
        self.checkObject('x', 0, None)
        # redo one more operation
        undo_redo.redo()
        self.assertEqual(undo_redo.nb_undo, 2)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 2)
        self.assertEqual(undo_redo.undo_messages,
                         ["change value", "change name"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 0, 10)
        # undo two operations
        undo_redo.undo(2)
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 2)
        self.assertEqual(undo_redo.current_state, 0)
        self.assertEqual(undo_redo.undo_messages, [])
        self.assertEqual(undo_redo.redo_messages,
                         ["change name", "change value"])
        self.checkObject('', 0, None)
        # redo two operations
        undo_redo.redo(2)
        self.assertEqual(undo_redo.nb_undo, 2)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 2)
        self.assertEqual(undo_redo.undo_messages,
                         ["change value", "change name"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 0, 10)
        # open transaction
        undo_redo.open("change abc")
        self.obj.name = "aaa"
        self.obj.abc = 100
        self.obj.value = 1111
        # try to open another transaction, check that exception is raised
        with self.assertRaises(RuntimeError) as exc:
            undo_redo.open("change abc")
        self.assertEqual('There is already open transaction.',
                         exc.exception.args[0])
        # abort transaction
        undo_redo.abort()
        self.assertEqual(undo_redo.current_state, 2)
        self.checkObject('x', 0, 10)
        # try to abort, check that exception is raised
        with self.assertRaises(RuntimeError) as exc:
            undo_redo.abort()
        self.assertEqual('There is no open transaction.',
                         exc.exception.args[0])
        # set undo limit to 0
        undo_redo.undo_limit = 0
        self.assertEqual(undo_redo.undo_limit, 0)
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 2)
        self.assertEqual(undo_redo.undo_messages, [])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 0, 10)
        # make commit
        undo_redo.open("change abc")
        self.obj.abc = 999
        undo_redo.commit()
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 3)
        self.assertEqual(undo_redo.undo_messages, [])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 999, 10)
        # set undo limit to 1
        undo_redo.undo_limit = 1
        self.assertEqual(undo_redo.undo_limit, 1)
        self.assertEqual(undo_redo.current_state, 3)
        self.checkObject('x', 999, 10)
        # make commit
        undo_redo.open("change value")
        self.obj.value = 321
        undo_redo.commit()
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 4)
        self.assertEqual(undo_redo.undo_messages, ["change value"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 999, 321)
        # make another commit
        undo_redo.open("change name")
        self.obj.name = "y"
        undo_redo.commit()
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 5)
        self.assertEqual(undo_redo.undo_messages, ["change name"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('y', 999, 321)
        # undo
        undo_redo.undo()
        self.assertEqual(undo_redo.nb_undo, 0)
        self.assertEqual(undo_redo.nb_redo, 1)
        self.assertEqual(undo_redo.current_state, 4)
        self.assertEqual(undo_redo.undo_messages, [])
        self.assertEqual(undo_redo.redo_messages, ["change name"])
        self.checkObject('x', 999, 321)
        # make new commit
        undo_redo.open("change value")
        self.obj.value = 654
        undo_redo.commit()
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 6)
        self.assertEqual(undo_redo.undo_messages, ["change value"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 999, 654)
        # set undo limit to 2
        undo_redo.undo_limit = 2
        self.assertEqual(undo_redo.undo_limit, 2)
        self.assertEqual(undo_redo.current_state, 6)
        self.checkObject('x', 999, 654)
        # make one more commit
        undo_redo.open("change abc")
        self.obj.abc = 444
        undo_redo.commit()
        self.assertEqual(undo_redo.nb_undo, 2)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 7)
        self.assertEqual(undo_redo.undo_messages,
                         ["change abc", "change value"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 444, 654)
        # set undo limit back to 1
        undo_redo.undo_limit = 1
        self.assertEqual(undo_redo.undo_limit, 1)
        self.assertEqual(undo_redo.nb_undo, 1)
        self.assertEqual(undo_redo.nb_redo, 0)
        self.assertEqual(undo_redo.current_state, 7)
        self.assertEqual(undo_redo.undo_messages,
                         ["change abc"])
        self.assertEqual(undo_redo.redo_messages, [])
        self.checkObject('x', 444, 654)

#------------------------------------------------------------------------------
class TestHistoryUndoRedo(unittest.TestCase):
    """Test case for History undo/redo."""

    def test_history_undo_redo(self):
        """Test for History undo/redo"""
        #----------------------------------------------------------------------
        undo_redo = UndoRedo(History())
        case = undo_redo.model.current_case

        assert_that(case.uid, is_in(undo_redo.model))
        assert_that(undo_redo.model.current_case.uid, is_in(undo_redo.model))

        stage = case.create_stage(':1:')
        assert_that(stage.uid, is_in(undo_redo.model))

        #----------------------------------------------------------------------
        undo_redo.commit("first stage created")
        undo_redo.undo()

        assert_that(case.uid, is_in(undo_redo.model))
        assert_that(undo_redo.model.current_case.uid, is_in(undo_redo.model))

        assert_that(stage.uid, is_not(is_in(undo_redo.model)))

        #----------------------------------------------------------------------
        undo_redo.redo()

        assert_that(case.uid, is_in(undo_redo.model))
        assert_that(undo_redo.model.current_case.uid, is_in(undo_redo.model))

        assert_that(stage.uid, is_in(undo_redo.model))

        stage2 = case.create_stage(':2:')
        assert_that(stage.uid, is_in(undo_redo.model))
        pass

#------------------------------------------------------------------------------
def test_stage_with_python_variables():
    #--------------------------------------------------------------------------
        undo_redo = UndoRedo(History())
        case = undo_redo.model.current_case

        import os
        filename = os.path.join(os.getenv('ASTERSTUDYDIR'),
                                'data', 'comm2study', 'hsns101a.comm')
        case.import_stage(filename)

        undo_redo.commit("first stage created")
        undo_redo.undo()
        undo_redo.redo()

        pass


def test_disable_undo_redo():
    def disabler():
        return True

    history = History()
    undo_redo = UndoRedo(history, disable_cbck=disabler)
    assert_that(undo_redo.last, is_(history))
    undo_redo.undo_limit = 0
    assert_that(undo_redo.undo_limit, equal_to(0))
    assert_that(undo_redo.nb_undo, equal_to(0))
    assert_that(undo_redo.nb_redo, equal_to(0))
    assert_that(undo_redo.undo_messages, empty())
    assert_that(undo_redo.redo_messages, empty())

    _id = undo_redo.current_state
    assert_that(_id, equal_to(0))
    assert_that(undo_redo.current_state, equal_to(0))
    undo_redo.commit('simulation')
    assert_that(undo_redo.current_state, greater_than(_id))

    _id = undo_redo.current_state
    undo_redo.undo('simulation')
    assert_that(undo_redo.current_state, greater_than(_id))

    _id = undo_redo.current_state
    undo_redo.redo('simulation')
    assert_that(undo_redo.current_state, greater_than(_id))

    _id = undo_redo.current_state
    undo_redo.revert()
    assert_that(undo_redo.current_state, greater_than(_id))

    _id = undo_redo.current_state
    undo_redo._move(5)
    assert_that(undo_redo.current_state, greater_than(_id))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
