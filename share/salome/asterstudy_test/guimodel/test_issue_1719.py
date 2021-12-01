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

"""Automatic tests for concepts editor (issue 1684)."""


import unittest
from hamcrest import *

from PyQt5 import Qt as Q

from asterstudy.datamodel import History
from asterstudy.gui.cmdtexteditor import CmdTextEditor

from common_test_gui import FakeGui, get_application

def text2line(text):
    lines = text.split("\n")
    return " ".join([i.strip() for i in lines]).strip()

def setup():
    """required to create widgets"""
    get_application()

def _init():
    """Initialize model"""
    gui = FakeGui()
    study = gui.study()
    stage = study.history.current_case.create_stage()
    stage.add_command('LIRE_MAILLAGE', 'mesh')
    study.commit("create stage with one command")

    return gui

def test_set_good_text():
    """Positive test for Command text editor"""
    gui = _init()
    study = gui.study()

    assert_that(study.history.current_case[0], has_length(1))
    orig_text = study.history.current_case[0][0].text

    editor = CmdTextEditor(study.history.current_case[0][0], gui)
    assert_that(text2line(editor.editor.text()), equal_to(text2line(orig_text)))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Ok), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Apply), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Close), equal_to(True))

    good_text_1 = 'mesh = LIRE_MAILLAGE(UNITE=20)'

    editor.editor.setText(good_text_1)
    assert_that(text2line(editor.editor.text()), equal_to(text2line(good_text_1)))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Ok), equal_to(True))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Apply), equal_to(True))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Close), equal_to(True))

    editor.perform(Q.QDialogButtonBox.Close)
    assert_that(text2line(study.history.current_case[0][0].text), equal_to(text2line(orig_text)))

    editor.perform(Q.QDialogButtonBox.Apply)
    new_text = study.history.current_case[0][0].text
    assert_that(text2line(new_text), equal_to(text2line(good_text_1)))

    good_text_2 = 'mesh = LIRE_MAILLAGE(INFO=1, UNITE=20)'

    editor.editor.setText(good_text_2)
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Ok), equal_to(True))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Apply), equal_to(True))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Close), equal_to(True))

    editor.perform(Q.QDialogButtonBox.Apply)

    new_text = study.history.current_case[0][0].text
    assert_that(text2line(new_text), equal_to(text2line(good_text_2)))

    good_text_3 = 'mesh = LIRE_MAILLAGE(INFO=2, UNITE=20)'

    editor.editor.setText(good_text_3)
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Ok), equal_to(True))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Apply), equal_to(True))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Close), equal_to(True))

    editor.perform(Q.QDialogButtonBox.Ok)

    new_text = study.history.current_case[0][0].text
    assert_that(text2line(new_text), equal_to(text2line(good_text_3)))

def test_set_bad_text():
    """Negative test for Command text editor"""
    gui = _init()
    study = gui.study()

    assert_that(study.history.current_case[0], has_length(1))
    orig_text = study.history.current_case[0][0].text

    editor = CmdTextEditor(study.history.current_case[0][0], gui)
    assert_that(text2line(editor.editor.text()), equal_to(text2line(orig_text)))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Ok), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Apply), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Close), equal_to(True))

    bad_text_1 = 'mesh = LIRE_MAILLAGE(UNIT=20)'

    editor.editor.setText(bad_text_1)
    assert_that(text2line(editor.editor.text()), equal_to(text2line(bad_text_1)))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Ok), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Apply), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Close), equal_to(True))

    bad_text_2 = 'mesh = AAA()'

    editor.editor.setText(bad_text_2)
    assert_that(text2line(editor.editor.text()), equal_to(text2line(bad_text_2)))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Ok), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Apply), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Close), equal_to(True))

    bad_text_3 = ''

    editor.editor.setText(bad_text_3)
    assert_that(text2line(editor.editor.text()), equal_to(text2line(bad_text_3)))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Ok), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Apply), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Close), equal_to(True))

    bad_text_4 = 'mesh = DEBUT()'

    editor.editor.setText(bad_text_4)
    assert_that(text2line(editor.editor.text()), equal_to(text2line(bad_text_4)))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Ok), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Apply), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Close), equal_to(True))


def test_read_only():
    """Test for read-only mode of Command text editor"""
    gui = _init()
    study = gui.study()

    assert_that(study.history.current_case[0], has_length(1))
    orig_text = study.history.current_case[0][0].text

    editor = CmdTextEditor(study.history.current_case[0][0], gui)
    editor.setReadOnly(True)

    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Ok), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Apply), equal_to(False))
    assert_that(editor.isButtonEnabled(Q.QDialogButtonBox.Close), equal_to(True))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
