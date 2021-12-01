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

"""Bug #1233 - filterby fails with non-finished commands"""


import unittest
from hamcrest import *
from testutils import attr

from asterstudy.datamodel.history import History
from asterstudy.datamodel.command import Command
from asterstudy.datamodel.catalogs import CATA


def test():
    """Test for bug #1233"""
    history = History()
    case = history.current_case
    stage = case.create_stage()

    stage.add_command('LIRE_MAILLAGE')
    stage.add_command('DEFI_FONCTION')

    DS = CATA.package('DataStructure')
    filtered = Command.filterby(stage, DS.maillage_sdaster)
    assert_that(filtered, has_length(1))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
