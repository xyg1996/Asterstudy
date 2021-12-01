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


import os.path as osp
import unittest
from unittest import mock

from asterstudy.common.utilities import auto_datafile_naming
from asterstudy.datamodel.general import FileAttr
from asterstudy.datamodel.history import History
from hamcrest import *
from testutils import tempdir


def test_attr():
    history = History()
    case = history.current_case

    stage1 = case.create_stage('Stage_1')

    command1 = stage1('PRE_GMSH')
    command1.init({'UNITE_GMSH': {19: 'gmsh.file'},
                   'UNITE_MAILLAGE': {19: 'gmsh.file'}})

    attrs = stage1.handle2info[19][command1]
    assert_that(attrs, equal_to([FileAttr.In, FileAttr.Out]))

    command1.init({'UNITE_GMSH': {19: 'gmsh.file'}})

    attrs = stage1.handle2info[19][command1]
    assert_that(attrs, equal_to([FileAttr.In]))


def test_auto():
    def _setup():
        history = History()
        case = history.current_case

        st1 = case.create_stage('Stage_1')
        cmd = st1('PRE_GMSH')
        cmd.init({'UNITE_GMSH': 19, 'UNITE_MAILLAGE': 20})
        assert_that(st1.handle2info[19].filename, none())
        assert_that(st1.handle2info[20].filename, none())

        st2 = case.create_stage('Stage_2')
        cmd = st2('LIRE_MAILLAGE')
        cmd.init({'UNITE': 20})
        assert_that(st2.handle2info[20].filename, none())

        return case

    def _check(case):
        assert_that(case[0].handle2info[19].filename,
                    equal_to("/path/for/test/Stage_1.19"))
        assert_that(case[0].handle2info[20].filename,
                    equal_to("/path/for/test/Stage_1.20"))
        assert_that(case[1].handle2info[20].filename,
                    equal_to("/path/for/test/Stage_1.20"))

    case = _setup()
    file19 = mock.Mock(unit=19, stage=case[0])
    file20 = mock.Mock(unit=20, stage=case[0])
    file2b = mock.Mock(unit=20, stage=case[1])

    auto_datafile_naming('File', file20, '/path/for/test')
    auto_datafile_naming('File', file2b, '/path/for/test')
    auto_datafile_naming('File', file19, '/path/for/test')
    _check(case)

    case = _setup()
    auto_datafile_naming('Stage', case[0], '/path/for/test')
    auto_datafile_naming('Stage', case[1], '/path/for/test')
    _check(case)

    case = _setup()
    auto_datafile_naming('Case', case, '/path/for/test')
    _check(case)


@tempdir
def test_relocate(tmpdir):
    dir1 = osp.join(tmpdir, 'first_Files')
    history = History()
    history.folder = dir1
    case = history.current_case

    st1 = case.create_stage('Stage_1')
    cmd = st1('PRE_GMSH')
    cmd.init({'UNITE_GMSH': 19, 'UNITE_MAILLAGE': 20})
    auto_datafile_naming('Case', case, dir1)
    assert_that(st1.handle2info[19].filename.startswith(dir1), equal_to(True))
    assert_that(st1.handle2info[20].filename.startswith(dir1), equal_to(True))

    # save as...
    dir2 = osp.join(tmpdir, 'saveas_Files')
    history.folder = dir2
    case.relocate_result_files(dir1)
    # data file not relocated
    assert_that(st1.handle2info[19].filename.startswith(dir1), equal_to(True))
    # result file has been relocated
    assert_that(st1.handle2info[20].filename.startswith(dir2), equal_to(True))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
