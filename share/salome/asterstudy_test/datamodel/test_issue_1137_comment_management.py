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

"""Data Model tests for 'Manage variables (CCTP 2.2.1.3)' functionality"""


import unittest
from hamcrest import *

from asterstudy.datamodel.history import History
from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel import command

from testutils.tools import check_persistence
from testutils.tools import check_export, check_text_eq

#------------------------------------------------------------------------------
def test_from_text():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = '\n'.join(["# read ",
                      "#the",
                      "mesh = LIRE_MAILLAGE()",
                      "# mesh"])
    stage = case.create_stage(':1:')

    comm2study(text, stage)

    assert_that(stage, has_length(3))
    assert_that(stage.check(), equal_to(Validity.Ok))

    commands = stage.sorted_commands

    assert_that(commands[0], instance_of(command.Comment))
    assert_that(commands[0].content, equal_to('read \nthe'))

    assert_that(commands[2], instance_of(command.Comment))
    assert_that(commands[2].content, equal_to('mesh'))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_via_api():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':0:')

    #--------------------------------------------------------------------------
    stage.add_comment('read ')
    stage.add_comment('the')
    stage.add_command('LIRE_MAILLAGE', 'mesh')
    stage.add_comment('mesh')

    assert_that(stage, has_length(3))
    assert_that(stage.check(), equal_to(Validity.Ok))

    commands = stage.sorted_commands

    assert_that(commands[0], instance_of(command.Comment))
    assert_that(commands[0].content, equal_to('read \nthe'))

    assert_that(commands[2], instance_of(command.Comment))
    assert_that(commands[2].content, equal_to('mesh'))

    #--------------------------------------------------------------------------
    commands[0].content = 'read the mesh'
    assert_that(commands[0].content, equal_to('read the mesh'))

    del stage[2]

    text = \
"""
# read the mesh
mesh = LIRE_MAILLAGE()
"""
    assert(check_export(stage, text))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_on_removing_command_should_remove_corresponding_comment():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
# read the mesh
mesh = LIRE_MAILLAGE()
"""
    stage = case.create_stage(':1:')

    comm2study(text, stage)

    assert_that(stage, has_length(2))
    assert_that(stage.check(), equal_to(Validity.Ok))
    assert_that(stage[0], instance_of(command.Comment))

    #--------------------------------------------------------------------------
    del stage[1]

    assert_that(stage, has_length(0))
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_on_removing_comment_should_not_remove_corresponding_command():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
# read the mesh
mesh = LIRE_MAILLAGE()
"""
    stage = case.create_stage(':1:')

    comm2study(text, stage)

    assert_that(stage, has_length(2))
    assert_that(stage.check(), equal_to(Validity.Ok))
    assert_that(stage[0], instance_of(command.Comment))

    #--------------------------------------------------------------------------
    del stage[0]

    assert_that(stage, has_length(1))
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_copy_paste():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
# read the mesh
mesh = LIRE_MAILLAGE(UNITE=20)
"""
    stage = case.create_stage(':1:')
    stage.paste(text)

    #--------------------------------------------------------------------------
    snippet = stage.copy2str(0)
    lines = text.strip().split('\n')
    assert_that(snippet, equal_to(lines[0]))

    snippet = stage.copy2str(1)
    assert_that(check_text_eq(snippet, text))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_adding_comment_to_an_existing_command():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    stage.paste('mesh = LIRE_MAILLAGE(UNITE=20)')
    assert_that(stage, has_length(1))

    stage[0].comment = 'read'
    assert_that(stage, has_length(2))
    assert_that(stage[0].comment.content, equal_to('read'))

    commands = stage.sorted_commands
    assert_that(commands[0], instance_of(command.Comment))

    #--------------------------------------------------------------------------
    stage[0].comment = 'read the'
    assert_that(stage, has_length(2))
    assert_that(stage[0].comment.content, equal_to('read the'))

    #--------------------------------------------------------------------------
    stage[0].comment += ' mesh'
    assert_that(stage, has_length(2))
    assert_that(stage[0].comment.content, equal_to('read the mesh'))

    text = \
"""
# read the mesh
mesh = LIRE_MAILLAGE(UNITE=20)
"""
    assert(check_export(stage, text, sort=True))

    #--------------------------------------------------------------------------
    stage[0].comment.delete()
    assert_that(stage, has_length(1))
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_trailing_comment():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    snippet = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)
# comment
"""
    stage.paste(snippet)
    assert_that(stage, has_length(2))
    assert_that(stage[0].comment, none())
    assert_that(stage[1].content, equal_to('comment'))

    #--------------------------------------------------------------------------
    stage[0].comment = "command"
    assert_that(stage, has_length(3))
    assert_that(stage[0].comment.content, equal_to('command'))
    assert_that(stage[1].content, equal_to('comment'))
    assert_that(stage[2].content, equal_to('command'))

    #--------------------------------------------------------------------------
    result = stage.paste("# snippet")
    assert_that(result, only_contains(stage[2]))
    assert_that(stage, has_length(3))
    assert_that(stage[0].content, equal_to('command'))
    assert_that(stage[1].comment.content, equal_to('command'))
    assert_that(stage[2].content, equal_to('comment\nsnippet'))

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_variable_comment():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    snippet = \
"""
# comment
a = 1
"""
    stage.paste(snippet)
    assert_that(stage, has_length(2))
    assert_that(stage[0].content, equal_to('comment'))
    assert_that(stage[1].comment.content, equal_to('comment'))

    #--------------------------------------------------------------------------
    stage[1].update('2', 'b')
    assert_that(stage, has_length(2))
    assert_that(stage[0].content, equal_to('comment'))
    assert_that(stage[1].comment.content, equal_to('comment'))

    #--------------------------------------------------------------------------
    stage[1].comment = "changed comment"
    assert_that(stage, has_length(2))
    assert_that(stage[0].content, equal_to('changed comment'))
    assert_that(stage[1].comment.content, equal_to('changed comment'))

    #--------------------------------------------------------------------------
    stage[1].comment.delete()
    assert_that(stage, has_length(1))
    assert_that(stage[0].comment, none())

    #--------------------------------------------------------------------------
    check_persistence(history)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_debut_comment():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    #--------------------------------------------------------------------------
    a = stage.add_variable('a', '1')
    assert_that(stage, has_length(1))
    assert_that(a.comment, none())
    a.comment = 'variable a'
    assert_that(stage, has_length(2))
    assert_that(a.comment.content, equal_to('variable a'))

    #--------------------------------------------------------------------------
    c = stage.add_command('DEBUT')
    assert_that(stage, has_length(3))
    assert_that(c.comment, none())
    c.comment = 'command DEBUT'
    assert_that(stage, has_length(4))
    assert_that(a.comment.content, equal_to('variable a'))
    assert_that(c.comment.content, equal_to('command DEBUT'))

    #--------------------------------------------------------------------------
    a.comment.delete()
    assert_that(stage, has_length(3))
    assert_that(a.comment, none())
    assert_that(c.comment.content, equal_to('command DEBUT'))

    #--------------------------------------------------------------------------
    c.comment.delete()
    assert_that(stage, has_length(2))
    assert_that(c.comment, none())

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
