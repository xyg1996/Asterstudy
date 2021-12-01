# -*- coding: utf-8 -*-

# Copyright 2017 EDF R&D
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

"""Automatic tests for running services on remote server."""


import unittest

from hamcrest import *

from asterstudy.datamodel.engine.engine_utils import has_asrun
from asterstudy.datamodel.engine import Engine

from engine_testcases import (remote_server, xtest_infos, xtest_success,
                              xtest_remote, xtest_remote_in_file,
                              xtest_remote_out_file, xtest_run_with_data)


_multiprocess_can_split_ = False
ENGINE = Engine.AsRun

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_asrun(), "asrun is required")
def test_infos():
    xtest_infos(ENGINE, remote_server(ENGINE))

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_asrun(), "asrun is required")
def test_success():
    xtest_success(ENGINE, remote_server(ENGINE))

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_asrun(), "asrun is required")
def test_run_with_data():
    xtest_run_with_data(ENGINE, remote_server(ENGINE))

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_asrun(), "asrun is required")
def test_remote_in_file():
    xtest_remote_in_file(ENGINE, remote_server(ENGINE))

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_asrun(), "asrun is required")
def test_remote_out_file():
    xtest_remote_out_file(ENGINE, remote_server(ENGINE))

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_asrun(), "asrun is required")
def test_remote():
    xtest_remote(ENGINE, remote_server(ENGINE))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
