# -*- coding: utf-8 -*-

# Copyright 2016 - 2019 EDF R&D
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

"""Automatic tests corresponding to SV1.01.02 documentation."""
# test/squish/suite_salome/fixit/tst_acceptance_lot6/

import os
import os.path as osp
import unittest

from asterstudy.datamodel import History, Validity
from hamcrest import *


def test_import_stage():
    history = History()
    case = history.current_case
    assert_that(case, has_length(0))

    filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'validation', 'lot6_stage1.comm')
    stage = case.import_stage(filename)
    assert_that(case, has_length(1))
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    meshfile = osp.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'validation', 'lot6.mmed')
    unit20 = stage.handle2info[20]
    unit20.filename = meshfile
    assert_that(unit20.exists, equal_to(True))

    filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'validation', 'lot6_stage2.comm')
    stage = case.import_stage(filename)
    assert_that(case, has_length(2))
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'validation', 'lot6_stage3.comm')
    stage = case.import_stage(filename)
    assert_that(case, has_length(3))
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
