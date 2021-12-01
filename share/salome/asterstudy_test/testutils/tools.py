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

"""Common functionality for testing export feature."""


import os
import os.path as osp
import sys

from hamcrest import *

from asterstudy.common import to_unicode, debug_message
from asterstudy.datamodel.study2code import study2code
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.study2comm import study2comm
from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History

#------------------------------------------------------------------------------
def check_text_diff(ref, cur, debug=True):
    ref = to_unicode(ref.strip())
    cur = to_unicode(cur.strip())
    if ref != cur:
        from difflib import context_diff
        for line in context_diff(ref.split('\n'), cur.split('\n')):
            if debug:
                print(line, file=sys.stderr)
        return False

    return True

#------------------------------------------------------------------------------
def check_text_eq(ref, cur):
    return check_text_diff(ref, cur, debug=True)

#------------------------------------------------------------------------------
def check_text_ne(ref, cur):
    return not check_text_diff(ref, cur, debug=False)

#------------------------------------------------------------------------------
def check_translation(stage, text, sort=False):
    text2 = study2code(stage, 'stage2')

    history = History()
    case = history.current_case
    stage2 = case.create_stage(':memory:')

    exec(text2)  # pragma pylint: disable=exec-used

    for command in stage2:
        assert_that(command.check(safe=False), equal_to(Validity.Nothing))

    text3 = study2comm(stage2, sort=sort)

    if not check_text_diff(text, text3):
        return False

    return True

#------------------------------------------------------------------------------
def check_import(text, sort=False):
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    debug_message("--- check_import: comm2study #1")
    comm2study(text, stage)

    debug_message("--- check_import: check commands")
    for command in stage:
        assert_that(command.check(safe=False), equal_to(Validity.Nothing))

    debug_message("--- check_import: study2comm #1")
    text1 = study2comm(stage, sort=sort)
    if not check_text_diff(text, text1):
        return False

    #--------------------------------------------------------------------------
    stage.delete()
    stage = case.create_stage(':once_again:')
    debug_message("--- check_import: comm2study #2")
    comm2study(text1, stage)

    #--------------------------------------------------------------------------
    debug_message("--- check_import: study2comm #2")
    text2 = study2comm(stage, sort=sort)

    if not check_text_diff(text, text2):
        return False

    #--------------------------------------------------------------------------
    return True

#------------------------------------------------------------------------------
def check_export(stage, text, validity=True, sort=False):
    if validity:
        for command in stage:
            assert_that(command.check(safe=False), equal_to(Validity.Nothing))

    text2 = study2comm(stage, sort=sort)

    return check_text_diff(text, text2)

#------------------------------------------------------------------------------
def check_persistence(history):
    from tempfile import mkstemp
    an_outfile = mkstemp(prefix='asterstudy' + '-', suffix='.ajs')[1]

    History.save(history, an_outfile)
    history2 = History.load(an_outfile)
    # folder is not saved in JSON file
    if history.folder is not None:
        history2.folder = history.folder

    assert_that(history * history2, none())

    os.remove(an_outfile)

#------------------------------------------------------------------------------
def print_stage(stage, title=""):
    print('-' * 10 + title + '-' * 10)
    for i, cmd in enumerate(stage.sorted_commands):
        print("DEBUG:", i, cmd.node_repr(), getattr(cmd, 'parent_id', -1))


def add_file(path, content="x"):
    """Create a dummy file."""
    dirn = osp.dirname(path)
    if not osp.exists(dirn):
        os.makedirs(dirn)
    with open(path, 'w') as fobj:
        fobj.write(content)


def add_database(path):
    """Create a dummy results database."""
    for path in [osp.join(path, 'base-stageName', 'glob.1.gz'),
                 osp.join(path, 'base-stageName', 'pick.1.gz')]:
        assert not osp.exists(path)
        add_file(path)
