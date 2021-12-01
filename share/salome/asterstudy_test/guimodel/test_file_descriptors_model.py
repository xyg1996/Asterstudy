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

"""Automatic tests for category model."""


import unittest
from os import mkdir
from types import FunctionType

from hamcrest import *

from PyQt5.Qt import Qt
from PyQt5 import Qt as Q

from asterstudy.common import external_files_callback, FilesSupplier
from asterstudy.datamodel import FileAttr
from asterstudy.datamodel.command import Unit
from asterstudy.gui.behavior import behavior
from asterstudy.gui.datafiles.model import findIndex
from asterstudy.gui import Entity, Role, NodeType
from asterstudy.gui.datafiles.objects import Directory
from asterstudy.gui.study import Study

from testutils import tempdir
import testutils.gui_utils

_multiprocess_can_split_ = True

FileData_file = 0
FileData_unit = 1
FileData_inout = 2
FileData_exists = 3
FileData_embedded = 4


def check_model(model, target, root, expected):
    """
    Checks that model contains expected values for each provided role in each existing cell.

    If check is successful, this function returns silently.
    If not, it raises an ``AssertionError`.

    Arguments:
        model (asterstudy.gui.datafiles.model.ProxyModel): Model to check.
        target (Entity|None): Entity which should be set as "target" before starting check.
            This affects which rows in the model become invisible.
        root (Entity|None): Entity whose index should be set as root before collecting actual data.
            This is needed to imitate similar logic in real application's DataFiles.setSelection().
        expected (tuple[tuple[int,tuple[dict]],...]): Expected data.
            This must be an iterable with one item per each expected row.
            Each item must be a tuple containing level of that row (top-level items have level 0)
            and dictionaries with all data that needs to be validated in the row.
            In the dictionary, each key is a role to check, and each value is either expected data
            or function that returns `True` for a correct value and `False` otherwise.
            Roles that are not present in dictionary won't be tested.
    """
    def _read_rows(_parent, _level=0):
        for _row in range(model.rowCount(_parent)):
            yield _level, tuple(_read_cells(_row, _parent))
            for _subrow in _read_rows(model.index(_row, 0, _parent), _level + 1):
                yield _subrow

    def _read_cells(_row, _parent):
        for _col in range(model.columnCount(_parent)):
            yield model.index(_row, _col, _parent)

    model.target = target
    root_index = findIndex(model, root) if root else Q.QModelIndex()
    actual = tuple(_read_rows(root_index))

    assert len(actual) == len(expected), \
        'Expected {} rows, got {}'.format(len(expected), len(actual))

    for rownum, (expected_level, expected_row) in enumerate(expected):
        actual_level, actual_row = actual[rownum]

        assert actual_level == expected_level, \
            'Expected row #{} with level {}, got {}'.format(rownum, expected_level, actual_level)

        for colnum, expected_cell in enumerate(expected_row):
            actual_cell = actual_row[colnum]

            assert len(actual_row) == len(expected_row), \
                'Expected {} cells in row #{}, got {}' \
                .format(len(expected_row), rownum, len(actual_row))

            for role, expected_value in sorted(expected_cell.items()):
                actual_value = actual_cell.data(role)
                if isinstance(expected_value, FunctionType):
                    assert expected_value(actual_value), \
                        'Check failed on value {} in cell ({},{}) for rolw {}' \
                        .format(actual_value, rownum, colnum, role)
                else:
                    assert actual_value == expected_value, \
                        'Expected {}, got {} in cell ({},{}) for role {}' \
                        .format(expected_value, actual_value, rownum, colnum, role)


#------------------------------------------------------------------------------
def test_file_model():
    behavior().show_catalogue_name_data_files = True
    behavior().use_business_translations = False

    #--------------------------------------------------------------------------
    study = Study(None)
    history = study.history
    case = history.current_case
    case_entity = Entity(case.uid, NodeType.Case)

    #--------------------------------------------------------------------------
    model = study.dataFilesModel()
    assert_that(model, not_none())

    #--------------------------------------------------------------------------
    # check header data
    assert_that(model.headerData(FileData_inout, Qt.Horizontal), equal_to('Mode'))
    assert_that(model.headerData(FileData_unit, Qt.Horizontal), equal_to('Unit'))
    assert_that(model.headerData(FileData_file, Qt.Horizontal), equal_to('Filename'))
    assert_that(model.headerData(FileData_exists, Qt.Horizontal), equal_to('Exists'))
    assert_that(model.headerData(FileData_embedded, Qt.Horizontal), equal_to('Embedded'))
    assert_that(model.sourceModel().headerData(0, Qt.Vertical), equal_to(1))

    #--------------------------------------------------------------------------
    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)


    #--------------------------------------------------------------------------
    # create stage
    stage = case.create_stage(':memory:')
    stage_entity = Entity(stage.uid, NodeType.Stage)
    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)


    #--------------------------------------------------------------------------
    # add command
    # in this command:
    #    - UNITE_GMSH is keyword of type 'in'
    #    - UNITE_MAILLAGE is keyword of type 'out'
    command = stage('PRE_GMSH')
    command_entity = Entity(command.uid, NodeType.Command)

    # initialize a keyword that refers to 'in' file
    command['UNITE_GMSH'].value = {19: 'gmsh.file'}
    assert_that(command['UNITE_GMSH'], instance_of(Unit))
    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'gmsh.file', Qt.ToolTipRole: 'File: gmsh.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'gmsh.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'gmsh.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 19, Qt.ToolTipRole: 19,
             Qt.BackgroundRole: None, Qt.UserRole: 19, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 19, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in expected_for_case if level==1)

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # enable sorting stages
    behavior().sort_stages = True

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 0, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 0, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 0, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 0, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 0, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 1, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 1, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'gmsh.file', Qt.ToolTipRole: 'File: gmsh.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'gmsh.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'gmsh.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 19, Qt.ToolTipRole: 19,
             Qt.BackgroundRole: None, Qt.UserRole: 19, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 19, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in expected_for_case if level==1)

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # disable sorting stages again
    behavior().sort_stages = False

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'gmsh.file', Qt.ToolTipRole: 'File: gmsh.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'gmsh.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'gmsh.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 19, Qt.ToolTipRole: 19,
             Qt.BackgroundRole: None, Qt.UserRole: 19, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 19, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in expected_for_case if level==1)

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # switch ON embedded state
    info = stage.handle2info[19]
    info.embedded = True
    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'gmsh.file (embedded)', Qt.ToolTipRole: 'File: gmsh.file (embedded)',
             Qt.BackgroundRole: None, Qt.UserRole: 'gmsh.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'gmsh.file (embedded)', Role.ReferenceRole: False},
            {Qt.DisplayRole: 19, Qt.ToolTipRole: 19,
             Qt.BackgroundRole: None, Qt.UserRole: 19, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 19, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'Yes', Qt.ToolTipRole: 'Yes',
             Qt.BackgroundRole: None, Qt.UserRole: True, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'Yes', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in expected_for_case if level==1)

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # initialize a keyword that refers to 'out' file
    command['UNITE_MAILLAGE'].value = {20: 'maillage.file'}
    assert_that(command['UNITE_MAILLAGE'], instance_of(Unit))
    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'gmsh.file (embedded)', Qt.ToolTipRole: 'File: gmsh.file (embedded)',
             Qt.BackgroundRole: None, Qt.UserRole: 'gmsh.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'gmsh.file (embedded)', Role.ReferenceRole: False},
            {Qt.DisplayRole: 19, Qt.ToolTipRole: 19,
             Qt.BackgroundRole: None, Qt.UserRole: 19, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 19, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'Yes', Qt.ToolTipRole: 'Yes',
             Qt.BackgroundRole: None, Qt.UserRole: True, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'Yes', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: None, Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'out', Qt.ToolTipRole: 'out',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.Out, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'out', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in expected_for_case if level==1)

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # modify a keyword that refers to 'in' file: older unit 19 no longer used

    command['UNITE_GMSH'].value = {20: 'folder/maillage.file'}
    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'gmsh.file (embedded)', Qt.ToolTipRole: 'File: gmsh.file (embedded)',
             Qt.BackgroundRole: None, Qt.UserRole: 'gmsh.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'gmsh.file (embedded)', Role.ReferenceRole: False},
            {Qt.DisplayRole: 19, Qt.ToolTipRole: 19,
             Qt.BackgroundRole: None, Qt.UserRole: 19, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 19, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'Yes', Qt.ToolTipRole: 'Yes',
             Qt.BackgroundRole: None, Qt.UserRole: True, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'Yes', Role.ReferenceRole: False},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: folder/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'folder/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: None, Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'inout', Qt.ToolTipRole: 'inout',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.InOut, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'inout', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in expected_for_case[3:4])

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # modify a keyword that refers to 'out' file

    # change unit value with undefined file name
    # while not associated to a command,
    # older value 'maillage.file' is kept in memory (stage)
    command['UNITE_MAILLAGE'].value = 21
    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'gmsh.file (embedded)', Qt.ToolTipRole: 'File: gmsh.file (embedded)',
             Qt.BackgroundRole: None, Qt.UserRole: 'gmsh.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'gmsh.file (embedded)', Role.ReferenceRole: False},
            {Qt.DisplayRole: 19, Qt.ToolTipRole: 19,
             Qt.BackgroundRole: None, Qt.UserRole: 19, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 19, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'Yes', Qt.ToolTipRole: 'Yes',
             Qt.BackgroundRole: None, Qt.UserRole: True, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'Yes', Role.ReferenceRole: False},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: folder/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'folder/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: None, Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: '<undefined>', Qt.ToolTipRole: 'File: <undefined>',
             Qt.BackgroundRole: None, Qt.UserRole: None, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: False, Role.VisibilityRole: True,
             Role.SortRole: '<undefined>', Role.ReferenceRole: False},
            {Qt.DisplayRole: 21, Qt.ToolTipRole: 21,
             Qt.BackgroundRole: None, Qt.UserRole: 21, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: False, Role.VisibilityRole: True,
             Role.SortRole: 21, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'out', Qt.ToolTipRole: 'out',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.Out, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: False, Role.VisibilityRole: True,
             Role.SortRole: 'out', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: False, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: False, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in (expected_for_case[3], expected_for_case[5]))

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # change filename for the 'out' file
    stage.handle2info[21].filename = 'dir/maillage.file'
    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'gmsh.file (embedded)', Qt.ToolTipRole: 'File: gmsh.file (embedded)',
             Qt.BackgroundRole: None, Qt.UserRole: 'gmsh.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'gmsh.file (embedded)', Role.ReferenceRole: False},
            {Qt.DisplayRole: 19, Qt.ToolTipRole: 19,
             Qt.BackgroundRole: None, Qt.UserRole: 19, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 19, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'Yes', Qt.ToolTipRole: 'Yes',
             Qt.BackgroundRole: None, Qt.UserRole: True, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'Yes', Role.ReferenceRole: False},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: folder/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'folder/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: None, Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: dir/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'dir/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 21, Qt.ToolTipRole: 21,
             Qt.BackgroundRole: None, Qt.UserRole: 21, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 21, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'out', Qt.ToolTipRole: 'out',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.Out, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'out', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in (expected_for_case[3], expected_for_case[5]))

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # switch stage to text mode
    assert_that(stage.is_graphical_mode(), equal_to(True))
    stage.use_text_mode()
    assert_that(stage.is_text_mode(), equal_to(True))
    model.update()

    # at this point, the text stage reads:
    #   PRE_GMSH(UNITE_GMSH=20,
    #            UNITE_MAILLAGE=21)

    # since 'gmsh.file' is no longer used,
    # it has been removed from memory

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: folder/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'folder/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: None, Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: dir/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'dir/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 21, Qt.ToolTipRole: 21,
             Qt.BackgroundRole: None, Qt.UserRole: 21, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 21, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'out', Qt.ToolTipRole: 'out',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.Out, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'out', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)


    #--------------------------------------------------------------------------
    # switch stage to graphical mode
    stage.use_graphical_mode()
    assert_that(stage.is_graphical_mode(), equal_to(True))
    model.update()

    # command were recreated, so get its new uid
    command = stage.commands[0]
    command_entity = Entity(command.uid, NodeType.Command)

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: folder/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'folder/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: None, Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: dir/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'dir/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 21, Qt.ToolTipRole: 21,
             Qt.BackgroundRole: None, Qt.UserRole: 21, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 21, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'out', Qt.ToolTipRole: 'out',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.Out, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'out', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname] (PRE_GMSH)', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in expected_for_case if level==1)

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # check that 'show catalogue name' option is taken into account
    behavior().show_catalogue_name_data_files = False
    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: folder/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'folder/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: None, Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname]', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: dir/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'dir/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 21, Qt.ToolTipRole: 21,
             Qt.BackgroundRole: None, Qt.UserRole: 21, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 21, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'out', Qt.ToolTipRole: 'out',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.Out, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'out', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname]', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in expected_for_case if level==1)

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # add command from another category
    command2 = stage('LIRE_MAILLAGE')
    command2.init({'UNITE': {22: 'dir/lire_maillage.file'}})
    command2_entity = Entity(command2.uid, NodeType.Command)
    model.update()

    study.categoryModel().update()
    category1_entity = Entity(-2, NodeType.Category)
    category2_entity = Entity(-1, NodeType.Category)

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: folder/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'folder/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: None, Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname]', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'maillage.file', Qt.ToolTipRole: 'File: dir/maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'dir/maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 21, Qt.ToolTipRole: 21,
             Qt.BackgroundRole: None, Qt.UserRole: 21, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 21, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'out', Qt.ToolTipRole: 'out',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.Out, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'out', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '[noname]', Qt.ToolTipRole:
                '<pre>Command: <b>[noname]</b> (PRE_GMSH)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '[noname]', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'lire_maillage.file', Qt.ToolTipRole: 'File: dir/lire_maillage.file',
             Qt.BackgroundRole: None, Qt.UserRole: 'dir/lire_maillage.file', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'lire_maillage.file', Role.ReferenceRole: False},
            {Qt.DisplayRole: 22, Qt.ToolTipRole: 22,
             Qt.BackgroundRole: None, Qt.UserRole: 22, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 22, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command2.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_category1 = list((level-1,row) for (level,row) in expected_for_case[2:6])
    expected_for_category2 = list((level-1,row) for (level,row) in expected_for_case[6:])
    expected_for_command = list((level-1,row) for (level,row) in [expected_for_case[2], expected_for_case[4]])
    expected_for_command2 = list((level-1,row) for (level,row) in [expected_for_case[6]])

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, category1_entity, stage_entity, expected_for_category1)
    check_model(model, category2_entity, stage_entity, expected_for_category2)
    check_model(model, command_entity, stage_entity, expected_for_command)
    check_model(model, command2_entity, stage_entity, expected_for_command2)


def test_reference():
    behavior().show_catalogue_name_data_files = False
    behavior().use_business_translations = False

    class Supplier(FilesSupplier):
        _files = {'0:1:1:1':"referenced object"}
        def files(self, file_format):
            return self._files.keys()
        def filename(self, uid):
            return self._files.get(uid)

    supplier = Supplier()
    external_files_callback(supplier, True)

    study = Study(None)
    history = study.history

    case = history.current_case
    case_entity = Entity(case.uid, NodeType.Case)
    stage = case.create_stage(':memory:')
    stage_entity = Entity(stage.uid, NodeType.Stage)
    command = stage('LIRE_MAILLAGE')
    command.init({'UNITE':{20: '0:1:1:1'}})
    command_entity = Entity(command.uid, NodeType.Command)

    model = study.dataFilesModel()
    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'referenced object', Qt.ToolTipRole: 'File: referenced object (0:1:1:1)',
             Qt.BackgroundRole: None, Qt.UserRole: '0:1:1:1', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'referenced object', Role.ReferenceRole: True},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: None, Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: True},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: True},
            {Qt.DisplayRole: 'Yes', Qt.ToolTipRole: 'Yes',
             Qt.BackgroundRole: None, Qt.UserRole: True, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'Yes', Role.ReferenceRole: True},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: True},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in expected_for_case if level==1)

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


    #--------------------------------------------------------------------------
    # Unregister file supplier
    external_files_callback(supplier, False)
    model.update()

    #--------------------------------------------------------------------------
    parent = model.index(1, FileData_file, Q.QModelIndex())
    assert_that(model.rowCount(parent), equal_to(1))

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':memory:', Qt.ToolTipRole: '<pre>Stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: '<undefined>', Qt.ToolTipRole: 'File: <undefined> (0:1:1:1)',
             Qt.BackgroundRole: None, Qt.UserRole: '0:1:1:1', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: False, Role.VisibilityRole: True,
             Role.SortRole: '<undefined>', Role.ReferenceRole: True},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: None, Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: False, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: True},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: False, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: True},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: False, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: True},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: False, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: True},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>:memory:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command, Role.IdRole: command.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command = list((level-1,row) for (level,row) in expected_for_case if level==1)

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command_entity, stage_entity, expected_for_command)


def test_highlight_files():
    """Test files that appear twice are highlighted"""

    behavior().show_catalogue_name_data_files = False
    behavior().use_business_translations = False

    study = Study(None)
    history = study.history
    case = history.current_case
    case_entity = Entity(case.uid, NodeType.Case)

    model = study.dataFilesModel()
    assert_that(model, not_none())

    stage1 = case.create_stage(':stage1:')
    stage1_entity = Entity(stage1.uid, NodeType.Stage)

    stage2 = case.create_stage(':stage2:')
    stage2_entity = Entity(stage2.uid, NodeType.Stage)

    command1 = stage1('LIRE_MAILLAGE')
    command1.init({'UNITE':{20: '/my/duplicate/name'}})
    command1_entity = Entity(command1.uid, NodeType.Command)

    command2 = stage2('LIRE_MAILLAGE')
    command2.init({'UNITE':{20: '/my/duplicate/name'}})
    command2_entity = Entity(command2.uid, NodeType.Command)

    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':stage1:', Qt.ToolTipRole: '<pre>Stage: <b>:stage1:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage1, Role.IdRole: stage1.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage1, Role.IdRole: stage1.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage1, Role.IdRole: stage1.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage1, Role.IdRole: stage1.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage1, Role.IdRole: stage1.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'name', Qt.ToolTipRole: 'File: /my/duplicate/name',
             Qt.BackgroundRole: Q.QColor(Qt.yellow), Qt.UserRole: '/my/duplicate/name', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'name', Role.ReferenceRole: False},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: Q.QColor(Qt.yellow), Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: Q.QColor(Qt.yellow), Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: Q.QColor(Qt.yellow), Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: Q.QColor(Qt.yellow), Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>:stage1:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command1.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: ':stage2:', Qt.ToolTipRole: '<pre>Stage: <b>:stage2:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage2, Role.IdRole: stage2.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage2, Role.IdRole: stage2.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage2, Role.IdRole: stage2.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage2, Role.IdRole: stage2.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage2, Role.IdRole: stage2.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'name', Qt.ToolTipRole: 'File: /my/duplicate/name',
             Qt.BackgroundRole: Q.QColor(Qt.yellow), Qt.UserRole: '/my/duplicate/name', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'name', Role.ReferenceRole: False},
            {Qt.DisplayRole: 20, Qt.ToolTipRole: 20,
             Qt.BackgroundRole: Q.QColor(Qt.yellow), Qt.UserRole: 20, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 20, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: Q.QColor(Qt.yellow), Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: Q.QColor(Qt.yellow), Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: Q.QColor(Qt.yellow), Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>:stage2:</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command2.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage1 = list((level-1,row) for (level,row) in expected_for_case[2:4])
    expected_for_stage2 = list((level-1,row) for (level,row) in expected_for_case[5:7])
    expected_for_command1 = list((level-1,row) for (level,row) in [expected_for_case[2]])
    expected_for_command2 = list((level-1,row) for (level,row) in [expected_for_case[5]])

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage1_entity, stage1_entity, expected_for_stage1)
    check_model(model, stage2_entity, stage2_entity, expected_for_stage2)
    check_model(model, command1_entity, stage1_entity, expected_for_command1)
    check_model(model, command2_entity, stage2_entity, expected_for_command2)


@tempdir
def test_indir_outdir(directory):
    behavior().show_catalogue_name_data_files = False
    behavior().use_business_translations = False

    indir = directory + '/in'
    outdir = directory + '/out'
    mkdir(indir)
    mkdir(outdir)

    study = Study(None)
    history = study.history
    case = history.current_case
    case_entity = Entity(case.uid, NodeType.Case)

    stage = case.create_stage('Stage_1')
    stage_entity = Entity(stage.uid, NodeType.Stage)

    command1 = stage('LIRE_MAILLAGE')
    command1.init({'UNITE': {50: indir + '/file1'}})
    command1_entity = Entity(command1.uid, NodeType.Command)

    command2 = stage('LIRE_MAILLAGE')
    command2.init({'UNITE': {60: outdir + '/file2'}})
    command2_entity = Entity(command2.uid, NodeType.Command)

    model = study.dataFilesModel()
    model.update()

    expected_for_case = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: 'Stage_1', Qt.ToolTipRole: '<pre>Stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'file1', Qt.ToolTipRole: 'File: {}/file1'.format(indir),
             Qt.BackgroundRole: None, Qt.UserRole: indir + '/file1', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'file1', Role.ReferenceRole: False},
            {Qt.DisplayRole: 50, Qt.ToolTipRole: 50,
             Qt.BackgroundRole: None, Qt.UserRole: 50, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 50, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command1.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'file2', Qt.ToolTipRole: 'File: {}/file2'.format(outdir),
             Qt.BackgroundRole: None, Qt.UserRole: outdir + '/file2', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'file2', Role.ReferenceRole: False},
            {Qt.DisplayRole: 60, Qt.ToolTipRole: 60,
             Qt.BackgroundRole: None, Qt.UserRole: 60, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 60, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command2.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_stage = list((level-1,row) for (level,row) in expected_for_case[2:])
    expected_for_command1 = list((level-1,row) for (level,row) in [expected_for_case[2]])
    expected_for_command2 = list((level-1,row) for (level,row) in [expected_for_case[4]])

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command1_entity, stage_entity, expected_for_command1)
    check_model(model, command2_entity, stage_entity, expected_for_command2)


    #--------------------------------------------------------------------------
    # configure input directory
    case.in_dir = indir
    model.update()

    expected = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'Input directory', Qt.ToolTipRole: 'Input directory: {}'.format(indir),
             Qt.BackgroundRole: None, Qt.UserRole: indir, Role.IdRole: Directory.InDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: indir, Role.IdRole: Directory.InDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: indir, Role.IdRole: Directory.InDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: indir, Role.IdRole: Directory.InDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: indir, Role.IdRole: Directory.InDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (2, (
            {Qt.DisplayRole: 'file1', Qt.ToolTipRole: 'File: {}/file1'.format(indir),
             Qt.BackgroundRole: None, Qt.UserRole: indir + '/file1', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'file1', Role.ReferenceRole: False},
            {Qt.DisplayRole: 50, Qt.ToolTipRole: 50,
             Qt.BackgroundRole: None, Qt.UserRole: 50, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 50, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: '', Qt.ToolTipRole: '',
             Qt.BackgroundRole: None, Qt.UserRole: None, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '', Role.ReferenceRole: False},
        )),
        (3, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command1.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: 'Stage_1', Qt.ToolTipRole: '<pre>Stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'file1', Qt.ToolTipRole: 'File: {}/file1'.format(indir),
             Qt.BackgroundRole: None, Qt.UserRole: indir + '/file1', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'file1', Role.ReferenceRole: False},
            {Qt.DisplayRole: 50, Qt.ToolTipRole: 50,
             Qt.BackgroundRole: None, Qt.UserRole: 50, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 50, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command1.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'file2', Qt.ToolTipRole: 'File: {}/file2'.format(outdir),
             Qt.BackgroundRole: None, Qt.UserRole: outdir + '/file2', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'file2', Role.ReferenceRole: False},
            {Qt.DisplayRole: 60, Qt.ToolTipRole: 60,
             Qt.BackgroundRole: None, Qt.UserRole: 60, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 60, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command2.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_case = expected[:5] + expected[7:]
    expected_for_stage = list((level-1,row) for (level,row) in expected[5:])
    expected_for_command1 = list((level-1,row) for (level,row) in [expected[5]])
    expected_for_command2 = list((level-1,row) for (level,row) in [expected[7]])

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command1_entity, stage_entity, expected_for_command1)
    check_model(model, command2_entity, stage_entity, expected_for_command2)


    #--------------------------------------------------------------------------
    # configure output directory
    case.out_dir = outdir
    model.update()

    expected = (
        (0, (
            {Qt.DisplayRole: 'CurrentCase', Qt.ToolTipRole: '<pre>Case: <b>CurrentCase</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: case, Role.IdRole: case.uid,
             Role.TypeRole: NodeType.Case, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'Input directory', Qt.ToolTipRole: 'Input directory: {}'.format(indir),
             Qt.BackgroundRole: None, Qt.UserRole: indir, Role.IdRole: Directory.InDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: indir, Role.IdRole: Directory.InDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: indir, Role.IdRole: Directory.InDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: indir, Role.IdRole: Directory.InDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: indir, Role.IdRole: Directory.InDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (2, (
            {Qt.DisplayRole: 'file1', Qt.ToolTipRole: 'File: {}/file1'.format(indir),
             Qt.BackgroundRole: None, Qt.UserRole: indir + '/file1', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'file1', Role.ReferenceRole: False},
            {Qt.DisplayRole: 50, Qt.ToolTipRole: 50,
             Qt.BackgroundRole: None, Qt.UserRole: 50, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 50, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: '', Qt.ToolTipRole: '',
             Qt.BackgroundRole: None, Qt.UserRole: None, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '', Role.ReferenceRole: False},
        )),
        (3, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command1.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'Output directory', Qt.ToolTipRole: 'Output directory: {}'.format(outdir),
             Qt.BackgroundRole: None, Qt.UserRole: outdir, Role.IdRole: Directory.OutDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: outdir, Role.IdRole: Directory.OutDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: outdir, Role.IdRole: Directory.OutDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: outdir, Role.IdRole: Directory.OutDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: outdir, Role.IdRole: Directory.OutDir,
             Role.TypeRole: NodeType.Dir, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (2, (
            {Qt.DisplayRole: 'file2', Qt.ToolTipRole: 'File: {}/file2'.format(outdir),
             Qt.BackgroundRole: None, Qt.UserRole: outdir + '/file2', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'file2', Role.ReferenceRole: False},
            {Qt.DisplayRole: 60, Qt.ToolTipRole: 60,
             Qt.BackgroundRole: None, Qt.UserRole: 60, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 60, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'out', Qt.ToolTipRole: 'out',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.Out, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'out', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: '', Qt.ToolTipRole: '',
             Qt.BackgroundRole: None, Qt.UserRole: None, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '', Role.ReferenceRole: False},
        )),
        (3, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command2.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (0, (
            {Qt.DisplayRole: 'Stage_1', Qt.ToolTipRole: '<pre>Stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: stage, Role.IdRole: stage.uid,
             Role.TypeRole: NodeType.Stage, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'file1', Qt.ToolTipRole: 'File: {}/file1'.format(indir),
             Qt.BackgroundRole: None, Qt.UserRole: indir + '/file1', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'file1', Role.ReferenceRole: False},
            {Qt.DisplayRole: 50, Qt.ToolTipRole: 50,
             Qt.BackgroundRole: None, Qt.UserRole: 50, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 50, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command1.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command1, Role.IdRole: command1.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
        (1, (
            {Qt.DisplayRole: 'file2', Qt.ToolTipRole: 'File: {}/file2'.format(outdir),
             Qt.BackgroundRole: None, Qt.UserRole: outdir + '/file2', Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'file2', Role.ReferenceRole: False},
            {Qt.DisplayRole: 60, Qt.ToolTipRole: 60,
             Qt.BackgroundRole: None, Qt.UserRole: 60, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 60, Role.ReferenceRole: False},
            {Qt.DisplayRole: 'in', Qt.ToolTipRole: 'in',
             Qt.BackgroundRole: None, Qt.UserRole: FileAttr.In, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'in', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
            {Qt.DisplayRole: 'No', Qt.ToolTipRole: 'No',
             Qt.BackgroundRole: None, Qt.UserRole: False, Role.IdRole: lambda x: x<0,
             Role.TypeRole: NodeType.Unit, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: 'No', Role.ReferenceRole: False},
        )),
        (2, (
            {Qt.DisplayRole: '_', Qt.ToolTipRole:
                '<pre>Command: <b>_</b> (LIRE_MAILLAGE)<br>From stage: <b>Stage_1</b></pre>',
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: '_', Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: command2.uid, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
            {Qt.DisplayRole: None, Qt.ToolTipRole: None,
             Qt.BackgroundRole: None, Qt.UserRole: command2, Role.IdRole: command2.uid,
             Role.TypeRole: NodeType.Command, Role.ValidityRole: True, Role.VisibilityRole: True,
             Role.SortRole: None, Role.ReferenceRole: None},
        )),
    )
    expected_for_case = expected[:8]
    expected_for_stage = list((level-1,row) for (level,row) in expected[8:])
    expected_for_command1 = list((level-1,row) for (level,row) in [expected[8]])
    expected_for_command2 = list((level-1,row) for (level,row) in [expected[10]])

    check_model(model, None, None, expected_for_case)
    check_model(model, case_entity, None, expected_for_case)
    check_model(model, stage_entity, stage_entity, expected_for_stage)
    check_model(model, command1_entity, stage_entity, expected_for_command1)
    check_model(model, command2_entity, stage_entity, expected_for_command2)


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
