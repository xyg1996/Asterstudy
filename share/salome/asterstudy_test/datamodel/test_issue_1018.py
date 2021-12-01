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
from asterstudy.datamodel.general import FileAttr

#------------------------------------------------------------------------------
def test():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage1 = case.create_stage('Stage_1')

    command1 = stage1('PRE_GMSH')

    #--------------------------------------------------------------------------
    command1.init({'UNITE_GMSH': {19: 'gmsh.file'},
                   'UNITE_MAILLAGE': {19: 'gmsh.file'}})

    attrs = stage1.handle2info[19][command1]
    assert_that(attrs, equal_to([FileAttr.In, FileAttr.Out]))

    #--------------------------------------------------------------------------
    command1.init({'UNITE_GMSH': {19: 'gmsh.file'}})

    attrs = stage1.handle2info[19][command1]
    assert_that(attrs, equal_to([FileAttr.In]))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
