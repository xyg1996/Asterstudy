# -*- coding: utf-8 -*-

# Copyright 2016 - 2018 EDF R&D
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

"""Automatic tests for parametric studies."""


import os
import unittest

from asterstudy.datamodel.engine import Engine
from asterstudy.datamodel.engine.salome_runner import has_salome
from asterstudy.datamodel.result import StateOptions as SO
from engine_testcases import remote_server, DEFAULT_PARAMS
from hamcrest import *
from test_api_execution import exec_case
from testutils import tempdir


@unittest.skipIf(not remote_server(Engine.Salome), "no server available")
@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def test_remote(tmpdir):
    # remote execution
    server = DEFAULT_PARAMS['server']
    version = DEFAULT_PARAMS['version']
    calc = exec_case(tmpdir, server, version)
    calc.set("time", 10)
    calc.run()
    assert_that(calc.state, equal_to(SO.Success | SO.Warn))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
