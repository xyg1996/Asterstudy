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

"""Automatic tests for general services."""


import unittest

from hamcrest import *

from asterstudy.datamodel.general import FileAttr, Validity


def test_fileattr():
    """Test for file attribute enumerator conversion"""
    assert_that(FileAttr.str2value("in"), equal_to(FileAttr.In))
    assert_that(FileAttr.str2value("out"), equal_to(FileAttr.Out))
    assert_that(FileAttr.str2value("inout"), equal_to(FileAttr.InOut))
    assert_that(FileAttr.str2value("?"), equal_to(FileAttr.No))

    assert_that(FileAttr.value2str(FileAttr.In), equal_to("in"))
    assert_that(FileAttr.value2str(FileAttr.Out), equal_to("out"))
    assert_that(FileAttr.value2str(FileAttr.InOut), equal_to("inout"))
    assert_that(FileAttr.value2str(FileAttr.In | FileAttr.Named),
                equal_to("in+named"))
    assert_that(FileAttr.value2str(FileAttr.No), equal_to("?"))


def test_validity():
    """Test for validity enumerator conversion"""
    assert_that(Validity.value2str(Validity.Nothing), equal_to(''))
    assert_that(Validity.value2str(Validity.Ok), equal_to(''))
    assert_that(Validity.value2str(Validity.Valid), equal_to(''))

    assert_that(Validity.value2str(Validity.Syntaxic), equal_to('Syntax problem'))
    assert_that(Validity.value2str(Validity.Dependency), equal_to('Broken dependencies'))
    assert_that(Validity.value2str(Validity.Naming), equal_to('Naming conflict'))

    assert_that(Validity.value2str(Validity.Syntaxic|Validity.Dependency), equal_to('Syntax problem; Broken dependencies'))
    assert_that(Validity.value2str(Validity.Syntaxic|Validity.Naming), equal_to('Syntax problem; Naming conflict'))
    assert_that(Validity.value2str(Validity.Dependency|Validity.Naming), equal_to('Broken dependencies; Naming conflict'))

    assert_that(Validity.value2str(Validity.Complete), equal_to('Syntax problem; Broken dependencies; Naming conflict'))
    assert_that(Validity.value2str(Validity.Any), equal_to('Syntax problem; Broken dependencies; Naming conflict'))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
