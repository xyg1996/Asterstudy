# coding=utf-8

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


import sys

from PyQt5 import Qt as Q

from asterstudy.datamodel import History, UndoRedo
from asterstudy.gui import HistoryProxy

class HistoryHolder(HistoryProxy):
    """History adapter for History as a root node."""

    def __init__(self, history):
        self._history = history

    @property
    def root(self):
        return self._history

    @property
    def case(self):
        return self._history.current_case

class FakeStudy:
    """Fake study for UI tests."""
    def __init__(self):
        history = History()
        self._undo_redo = UndoRedo(history)

    @property
    def history(self):
        return self._undo_redo.model

    @property
    def activeCase(self):
        return self.history.current_case

    def commit(self, msg):
        self._undo_redo.commit(msg)

    def revert(self):
        self._undo_redo.revert()

class FakeGui(Q.QObject):
    """Fake GUI for UI tests."""

    preferencesChanged = Q.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._study = FakeStudy()

    def study(self):
        return self._study

    def preferencesMgr(self):
        return None

    def update(self, *args, **kwargs):
        pass

class TestApp(Q.QApplication):
    """Test application."""

    main = None

    def __init__(self, argv):
        super().__init__(argv)

        self.main = Q.QMainWindow()
        self.main.setGeometry(100, 200, 600, 400)

    def exec_(self):
        self.main.show()
        super().exec_()

    def show(self):
        self.main.show()

    def hide(self):
        self.main.hide()

def get_application():
    if not hasattr(get_application, "_app"):
        get_application._app = TestApp(sys.argv)
    return get_application._app
