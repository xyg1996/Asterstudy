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

"""Automatic tests for version selection."""


import unittest
from collections import OrderedDict

from asterstudy.datamodel.engine.engine_utils import nearest_versions
from hamcrest import *


def test_select():
    # server infos
    server_versions = OrderedDict(
        [('stable', '14.4.0'),
         ('oldstable', '13.8.0'),
         ('unstable', '15.0.3'),
         ('unstable_mpi', '15.0.3'),
         ('stable-updates', '14.4.2'),
         ('DEV', '15.0.3'),
         ('xxx', None),
         ('test2', '15.0.5beta'),
         ('error', 'non numeric'),
         ])

    exact, lvers = nearest_versions((14, 4, 0), {})
    assert_that(exact, equal_to(False))
    assert_that(lvers, empty())

    exact, lvers = nearest_versions((14, 4, 0), server_versions)
    assert_that(exact, equal_to(True))
    assert_that(lvers, contains('stable', 'stable-updates', 'oldstable',
                                'unstable', 'unstable_mpi', 'DEV', 'test2',
                                'xxx', 'error'))

    cfg = server_versions.copy()
    del cfg['oldstable']
    exact, lvers = nearest_versions((13, 8, 0), cfg)
    assert_that(exact, equal_to(False))
    assert_that(lvers, contains('stable', 'stable-updates', 'unstable',
                                'unstable_mpi', 'DEV', 'test2', 'xxx', 'error'))

    exact, lvers = nearest_versions((15, 3, 0), cfg)
    assert_that(exact, equal_to(False))
    assert_that(lvers, contains('unstable', 'unstable_mpi', 'DEV', 'test2',
                                'stable', 'stable-updates', 'xxx', 'error'))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
