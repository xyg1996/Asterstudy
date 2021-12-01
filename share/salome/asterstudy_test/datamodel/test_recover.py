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

"""Automatic tests for recovery feature."""

import os
import os.path as osp
import unittest

from asterstudy.datamodel.history import History
from asterstudy.datamodel.recovery import get_version_from_ajs
from hamcrest import *


def test_recover_from_ajs():
    data = osp.join(os.getenv('ASTERSTUDYDIR'),
                    'data', 'export', 'data_forma02b.ajs')

    vers = get_version_from_ajs(data)
    assert_that(vers, equal_to("stable"))

    nbs = 2
    history = History()
    case, _ = history.import_case(data)

    assert_that(case, has_length(nbs))
    assert_that(case[0].is_graphical_mode(), equal_to(True))
    assert_that(case[1].is_graphical_mode(), equal_to(True))
    assert_that(case[0].handle2info, has_length(1))
    assert_that(case[0].handle2info[20].filename, equal_to("0:1:2:11"))
    assert_that(case[1].handle2info, has_length(0))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
