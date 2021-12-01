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

"""Automatic tests for conversion of INCLUDE."""


import os
import os.path as osp
import unittest

from asterstudy.common.conversion import TextProvider
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.general import ConversionLevel, Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.aster_parser import comment_include, remove_include
from hamcrest import *


def test_stage_z100b():
    history = History()
    case = history.current_case

    def _file(ext):
        return osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'export',
                        'zzzz100b' + ext)

    provider = TextProvider("")
    with open(_file('.11'), 'rb') as fcomm:
        provider.add('unit:11', fcomm.read())

    with open(_file('.comm'), 'rb') as fcomm:
        text = fcomm.read()

    strict = ConversionLevel.Any
    stage = case.create_stage('zzzz100b')
    comm2study(text, stage, strict, provider)

    assert_that(case, has_length(4))
    assert_that(case[0].is_graphical_mode(), equal_to(True))
    assert_that(case[0].check(), equal_to(Validity.Nothing))

    assert_that(case[1].is_graphical_mode(), equal_to(True))
    assert_that(case[1].check(), equal_to(Validity.Nothing))

    assert_that(case[2].is_graphical_mode(), equal_to(True))
    # because of a by-tuple assignment
    assert_that(case[2].check(), equal_to(Validity.Dependency))

    assert_that(case[3].is_text_mode(), equal_to(True))
    assert_that(case[3].get_text(), contains_string("VALE_REFE=a0 + a1 +"))

    assert_that(case.check(), equal_to(Validity.Dependency))


def test_case_z100b():
    history = History()
    export = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'zzzz100b.export')

    case, _ = history.import_case(export)

    assert_that(case, has_length(4))
    assert_that(case[0].is_graphical_mode(), equal_to(True))
    assert_that(case[0].name, equal_to('zzzz100b'))
    assert_that(case[0].check(), equal_to(Validity.Nothing))

    assert_that(case[1].is_graphical_mode(), equal_to(True))
    assert_that(case[1].check(), equal_to(Validity.Nothing))

    assert_that(case[2].is_graphical_mode(), equal_to(True))
    # because of a by-tuple assignment
    assert_that(case[2].check(), equal_to(Validity.Dependency))

    assert_that(case[3].is_text_mode(), equal_to(True))
    assert_that(case[3].get_text(), contains_string("VALE_REFE=a0 + a1 +"))

    assert_that(case.check(), equal_to(Validity.Dependency))


def test_comment_include():
    text = \
"""
mesh = LIRE_MAILLAGE()

INCLUDE(UNITE=4, INFO=0)

INCLUDE(DONNEE='/path/to/input/file')

mat = DEFI_MATERIAU(ELAS=_F(E=young, NU=0.3))
"""
    expected = \
"""
mesh = LIRE_MAILLAGE()

# MissingInclude: unit:4

INCLUDE(DONNEE='/path/to/input/file')

mat = DEFI_MATERIAU(ELAS=_F(E=young, NU=0.3))
"""
    expected2 = \
"""
mesh = LIRE_MAILLAGE()



INCLUDE(DONNEE='/path/to/input/file')

mat = DEFI_MATERIAU(ELAS=_F(E=young, NU=0.3))
"""
    changed = comment_include(text)
    assert_that(changed, equal_to(expected))
    clean, args = remove_include(changed)
    assert_that(clean, equal_to(expected2))
    assert_that(args, equal_to("unit:4"))


def test_comment_include_data():
    text = \
"""
mesh = LIRE_MAILLAGE()

INCLUDE(DONNEE="afilename.datg", INFO=0)

INCLUDE(UNITE=24)

mat = DEFI_MATERIAU(ELAS=_F(E=young, NU=0.3))
"""
    expected = \
"""
mesh = LIRE_MAILLAGE()

# MissingInclude: data:afilename.datg

INCLUDE(UNITE=24)

mat = DEFI_MATERIAU(ELAS=_F(E=young, NU=0.3))
"""
    expected2 = \
"""
mesh = LIRE_MAILLAGE()



INCLUDE(UNITE=24)

mat = DEFI_MATERIAU(ELAS=_F(E=young, NU=0.3))
"""
    changed = comment_include(text)
    assert_that(changed, equal_to(expected))
    clean, args = remove_include(changed)
    assert_that(clean, equal_to(expected2))
    assert_that(args, equal_to('data:afilename.datg'))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
