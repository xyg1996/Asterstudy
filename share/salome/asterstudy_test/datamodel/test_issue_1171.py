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

def test_reference():
    """Test for reference to SALOME study object"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    command = stage('LIRE_MAILLAGE')

    #--------------------------------------------------------------------------
    command.init({'UNITE': 20})

    assert_that(len(stage.handle2info), equal_to(1))
    assert_that(stage.handle2file(20), none())
    assert_that(stage.handle2info[20].filename, none())
    assert_that(stage.handle2info[20].embedded, equal_to(False))
    assert_that(stage.handle2info[20].isreference, equal_to(False))

    #--------------------------------------------------------------------------
    command.init({'UNITE': {20: ''}})

    assert_that(len(stage.handle2info), equal_to(1))
    assert_that(stage.handle2file(20), none())
    assert_that(stage.handle2info[20].filename, none())
    assert_that(stage.handle2info[20].embedded, equal_to(False))
    assert_that(stage.handle2info[20].isreference, equal_to(False))

    #--------------------------------------------------------------------------
    command.init({'UNITE': {20: '/aaa/bbb/ccc.py'}})

    assert_that(len(stage.handle2info), equal_to(1))
    assert_that(stage.handle2file(20), equal_to('/aaa/bbb/ccc.py'))
    assert_that(stage.handle2info[20].filename, equal_to('/aaa/bbb/ccc.py'))
    assert_that(stage.handle2info[20].embedded, equal_to(False))
    assert_that(stage.handle2info[20].isreference, equal_to(False))

    #--------------------------------------------------------------------------
    stage.handle2info[20].embedded = True
    assert_that(stage.handle2info[20].embedded, equal_to(True))
    stage.handle2info[20].embedded = False
    assert_that(stage.handle2info[20].embedded, equal_to(False))

    #--------------------------------------------------------------------------
    command.init({'UNITE': {20: '0:1:2'}})

    assert_that(len(stage.handle2info), equal_to(1))
    assert_that(stage.handle2file(20), equal_to('0:1:2'))
    assert_that(stage.handle2info[20].filename, equal_to('0:1:2'))

    # A SMESH file descriptors shall NOT be considered embedded
    assert_that(stage.handle2info[20].embedded, equal_to(False))
    assert_that(stage.handle2info[20].isreference, equal_to(True))

    #--------------------------------------------------------------------------
    stage.handle2info[20].embedded = True
    assert_that(stage.handle2info[20].embedded, equal_to(True))
    stage.handle2info[20].embedded = False
    assert_that(stage.handle2info[20].embedded, equal_to(False))

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
