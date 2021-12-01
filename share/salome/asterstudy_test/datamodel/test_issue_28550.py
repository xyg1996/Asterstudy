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

"""Bug #28550 - test ability to detect duplicate group name in MED files"""

import os
import os.path as osp

import unittest
from hamcrest import *
from testutils import attr

from asterstudy.common import (get_medfile_groups_by_type, MeshElemType, MeshGroupType)
from asterstudy.datamodel.engine.salome_runner import has_salome
from asterstudy.gui.salomegui import MeshObjects

from engine_testcases import mock_object_creation

@unittest.skipIf(not has_salome(), "salome is required")
def test_issue_28550():
    """Test reading groups in a MED file"""
    inputfile = osp.join(os.getenv('ASTERSTUDYDIR'),
                         'data', 'export', 'issue_28550.med')
    elem_types = MeshElemType.elem_types(MeshGroupType.GElement)
    group_infos = get_medfile_groups_by_type(inputfile, "Mesh_1",
                                             elem_types, with_size=True)
    groups = [elem[0] for elem in group_infos]
    occs = [elem[2] for elem in group_infos]
    assert_that("SUP", is_in(groups))
    assert_that("BASE", is_in(groups))
    assert_that(occs[groups.index("SUP")], equal_to(2))
    assert_that(occs[groups.index("BASE")], equal_to(1))

@unittest.skipIf(not has_salome(), "salome is required")
def test_issue_28550_smesh():
    """Test reading groups from a SMESH object"""
    inputfile = osp.join(os.getenv('ASTERSTUDYDIR'),
                         'data', 'export', 'issue_28550.med')

    with mock_object_creation(inputfile) as entry:
        group_infos = MeshObjects().groups_by_type(entry, MeshElemType.E2D, with_size=True)
        groups = [elem[0] for elem in group_infos]
        occs = [elem[2] for elem in group_infos]
        assert_that("SUP", is_in(groups))
        assert_that("BASE", is_in(groups))
        assert_that(occs[groups.index("SUP")], equal_to(2))
        assert_that(occs[groups.index("BASE")], equal_to(1))

if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
