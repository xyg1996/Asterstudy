# -*- coding: utf-8 -*-

# Copyright 2016 - 2017 EDF R&D
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

"""Automatic tests for BackupHistory utility."""


import glob
import os
import os.path as osp
import tempfile
import unittest

from hamcrest import *
from testutils import attr, tempdir

from asterstudy.common import rotate_path
from asterstudy.datamodel.backup import BackupHistory
from asterstudy.datamodel.general import FileAttr


@tempdir
def _test_rotate(base, pathtype):
    prefix = osp.join(base, "file_prefix")
    def _name(num):
        return '{}.{}'.format(prefix, num) if num else prefix

    def _content():
        return glob.glob(_name('*'))

    _test_rotate._i = 0
    def _create(num):
        _create._i = getattr(_create, '_i', 0) + 1
        string = "file #{0} - {1}".format(_create._i, _name(num))
        if pathtype == 'file':
            with open(_name(num), 'w') as fobj:
                fobj.write(string)
        else:
            os.mkdir(_name(num))
            with open(_name(num) + '/file', 'w') as fobj:
                fobj.write(string)

    # no file yet
    rotate_path(prefix, 99)
    assert_that(_content(), has_length(0))

    # init: prefix => prefix.1
    _create(0)
    rotate_path(prefix, 99)
    assert_that(_content(), contains_inanyorder(_name(1)))

    # without prefix: no change
    rotate_path(prefix, 99)
    assert_that(_content(), contains_inanyorder(_name(1)))

    os.rename(_name(1), _name(3))
    rotate_path(prefix, 99)
    assert_that(_content(), contains_inanyorder(_name(3)))

    # with .1, .2, .3
    _create(2)
    _create(1)
    rotate_path(prefix, 99)
    assert_that(_content(), contains_inanyorder(_name(1), _name(2), _name(3)))

    # with prefix, .1, .2, .3 => .1, .2, .3, .4
    _create(0)
    rotate_path(prefix, 99)
    assert_that(_content(),
                contains_inanyorder(_name(1), _name(2), _name(3), _name(4)))

    # with prefix, .1, .2, .3, .4 => .1, .2, .3
    _create(0)
    rotate_path(prefix, 3)
    assert_that(_content(), contains_inanyorder(_name(1), _name(2), _name(3)))

    rotate_path(prefix, 3)
    assert_that(_content(), contains_inanyorder(_name(1), _name(2), _name(3)))

    # remove all
    rotate_path(prefix, 0)
    assert_that(_content(), empty())


def test_rotate_file():
    _test_rotate('file')


def test_rotate_directory():
    _test_rotate('directory')


@tempdir
def test_backup(tmpdir):
    class FakeStage:
        pass

    backup = BackupHistory(tmpdir, _unittest=True)
    assert_that(osp.isdir(osp.join(tmpdir, ".asterstudy", "backup")))

    fake = FakeStage()
    fake.name = "name"
    fake.number = 1
    backup.save_stage(fake, "DEBUT()\nFIN()")
    fname = osp.join(backup.path, "name_1.comm")
    assert_that(osp.isfile(fname))
    with open(fname) as file:
        content = file.read()
    assert_that(content, contains_string("DEBUT()\nFIN()"))

    backup.add_file("/path/to/data20", 20, FileAttr.In)
    backup.add_file("/path/to/result80", 80, FileAttr.Out)
    backup.add_file("/path/to/inout", 55, FileAttr.InOut)
    backup.end()

    export = osp.join(backup.path, "backup.export")
    assert_that(osp.isfile(export))
    with open(export) as file:
        content = file.read()
    assert_that(content, contains_string("F comm name_1.comm D 1"))
    assert_that(content, contains_string("F libr /path/to/data20 D 20"))
    assert_that(content, contains_string("F libr /path/to/result80 R 80"))
    assert_that(content, contains_string("F libr /path/to/inout DR 55"))

    # check rotate_path is called the next time
    prefix = osp.join(tmpdir, ".asterstudy", "backup")
    assert_that(osp.isdir(prefix))
    assert_that(osp.isdir(prefix + '.1'), equal_to(False))

    backup = BackupHistory(tmpdir, _unittest=True)
    assert_that(osp.isdir(prefix))
    assert_that(osp.isdir(prefix + '.1'))


@tempdir
def test_backup_nofail(tmpdir):
    class FakeStage:
        pass

    backup = BackupHistory(tmpdir, _unittest=True)

    fake = FakeStage()
    fake.name = "/usr/forbidden/path"
    fake.number = 1
    # must not fail if it can not write the file
    backup.save_stage(fake, "")
    assert_that(osp.exists(fake.name), equal_to(False))

    # skip if root dir is not valid
    fake.name = "name"
    backup = BackupHistory("/usr/forbidden/path", _unittest=True)
    assert_that(backup.path, none())
    backup.save_stage(fake, "blabla")


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
