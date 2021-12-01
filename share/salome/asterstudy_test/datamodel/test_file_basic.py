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

"""Automatic tests for commands."""


import unittest

from hamcrest import *

from asterstudy.datamodel.history import History


def _setup_test():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
#--------------------------------------------------------------------------
    command = stage('LIRE_MAILLAGE')
    return command, stage

def test():
    """Test basic properties of file object in the datamodel."""
    command, stage = _setup_test()

    #--------------------------------------------------------------------------
    # Unit value corresponding to no file: test filename is *None*
    command.init({'UNITE': 20})

    assert_that(len(stage.handle2info), equal_to(1))
    assert_that(stage.handle2file(20), none())
    assert_that(stage.handle2info[20].filename, none())
    assert_that(stage.handle2info[20].embedded, equal_to(False))
    assert_that(stage.handle2info[20].isreference, equal_to(False))

    #--------------------------------------------------------------------------
    # Unit value with empty file name: same behaviour
    command.init({'UNITE': {20: ''}})

    assert_that(len(stage.handle2info), equal_to(1))
    assert_that(stage.handle2file(20), none())
    assert_that(stage.handle2info[20].filename, none())
    assert_that(stage.handle2info[20].embedded, equal_to(False))
    assert_that(stage.handle2info[20].isreference, equal_to(False))
    assert_that(stage.handle2info[20].isremote, equal_to(False))
    assert_that(stage.handle2info[20].server, none())

    #--------------------------------------------------------------------------
    # Unit value with external file
    command.init({'UNITE': {20: '/aaa/bbb/ccc.py'}})

    assert_that(len(stage.handle2info), equal_to(1))
    assert_that(stage.handle2file(20), equal_to('/aaa/bbb/ccc.py'))
    assert_that(stage.handle2info[20].filename, equal_to('/aaa/bbb/ccc.py'))
    assert_that(stage.handle2info[20].embedded, equal_to(False))
    assert_that(stage.handle2info[20].isreference, equal_to(False))
    assert_that(stage.handle2info[20].isremote, equal_to(False))
    assert_that(stage.handle2info[20].server, none())

    #--------------------------------------------------------------------------
    # Test embedded property
    stage.handle2info[20].embedded = True
    assert_that(stage.handle2info[20].embedded, equal_to(True))
    stage.handle2info[20].embedded = False
    assert_that(stage.handle2info[20].embedded, equal_to(False))

    #--------------------------------------------------------------------------
    # Test salome reference
    command.init({'UNITE': {20: '0:1:2'}})

    assert_that(len(stage.handle2info), equal_to(1))
    assert_that(stage.handle2file(20), equal_to('0:1:2'))
    assert_that(stage.handle2info[20].filename, equal_to('0:1:2'))

    # A SMESH file descriptors shall NOT be considered embedded
    assert_that(stage.handle2info[20].embedded, equal_to(False))
    assert_that(stage.handle2info[20].isreference, equal_to(True))
    assert_that(stage.handle2info[20].isremote, equal_to(False))
    assert_that(stage.handle2info[20].server, none())

    #--------------------------------------------------------------------------
    stage.handle2info[20].embedded = True
    assert_that(stage.handle2info[20].embedded, equal_to(True))
    stage.handle2info[20].embedded = False
    assert_that(stage.handle2info[20].embedded, equal_to(False))

    #--------------------------------------------------------------------------
    # Test remote file given as a URL
    theurl = 'sftp://NNI@host/absolute/path'
    command.init({'UNITE': {20: theurl}})
    assert_that(len(stage.handle2info), equal_to(1))
    assert_that(stage.handle2file(20), equal_to(theurl))
    assert_that(stage.handle2info[20].filename, equal_to(theurl))
    assert_that(stage.handle2info[20].embedded, equal_to(False))
    assert_that(stage.handle2info[20].isreference, equal_to(False))
    assert_that(stage.handle2info[20].isremote, equal_to(True))
    assert_that(stage.handle2info[20].server, equal_to("host"))
    assert_that(stage.handle2info[20].exists, equal_to(False))
    assert_that(stage.handle2info[20].relpath, equal_to("/absolute/path"))
    assert_that(stage.basename2unit("path"), equal_to(20))
    assert_that(stage.has_remote_files(), equal_to(True))

def test_2():
    """Test exists property for file objects, except for remote ones."""

    # This was made a separate test because of the OS operations involved.
    import tempfile, os
    command, stage = _setup_test()

    command.init({'UNITE': 20})
    assert_that(stage.handle2info[20].exists, equal_to(False))

    command.init({'UNITE': {20: ''}})
    assert_that(stage.handle2info[20].exists, equal_to(False))

    # Check existence for a local file
    fpath = tempfile.mkstemp(suffix="-test", prefix="tmp-for-astudy-")[1]
    command.init({'UNITE': {20: fpath}})
    assert_that(stage.handle2info[20].exists, equal_to(True))

    # Remove and test
    os.remove(fpath)
    assert_that(stage.handle2info[20].exists, equal_to(False))


def test_unite():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    matergc = stage.add_command('DEFI_MATER_GC', 'matergc')
    # check that UnitVisitor doesn't fail on UNITE* keywords that are not of
    # UnitBaseType type.
    matergc.init({'MAZARS': {'CODIFICATION': 'BAEL91', 'FCJ': 1.,
                             'UNITE_CONTRAINTE': 'MPa'}})


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
