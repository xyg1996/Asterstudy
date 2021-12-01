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

"""Automatic tests for issue27902."""


import os
import unittest

from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.general import ConversionLevel
from asterstudy.datamodel.history import History
from hamcrest import *
from testutils import attr


def test_27902():
    history = History()
    case = history.current_case
    stage = case.create_stage()

    commfile = os.path.join(os.getenv('ASTERSTUDYDIR'),
                            'data', 'export', 'forma07a.comm')
    with open(commfile, "r") as file:
        text = file.read()
    strict = ConversionLevel.Any
    comm2study(text, stage, strict)


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
