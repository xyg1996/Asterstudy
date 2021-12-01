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

"""Automatic tests for running services."""

from __future__ import unicode_literals

import unittest

from asterstudy.common import RunnerError
from asterstudy.datamodel.engine import (Engine, runner_factory,
                                         serverinfos_factory)
from asterstudy.datamodel.engine.engine_utils import has_asrun
from asterstudy.datamodel.result import Job
from engine_testcases import (_parameters, _setup_run_case, xtest_25975,
                              xtest_27166, xtest_failure,
                              xtest_init_from_database, xtest_run_with_data,
                              xtest_run_with_directory,
                              xtest_run_with_embfiles, xtest_run_with_error,
                              xtest_run_with_smesh_data, xtest_several_stages,
                              xtest_success, xtest_userhost, xtest_zzzz241a,
                              xtest_zzzz241a_once)
from hamcrest import *
from testutils import tempdir

_multiprocess_can_split_ = False
ENGINE = Engine.Direct


@tempdir
def test_initial_checking(tmpdir, server=None):
    nbs = 1
    rc1 = _setup_run_case(tmpdir, 0)
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))

    runner = runner_factory(ENGINE, case=rc1, logger=lambda x: None)

    # initialisation checkings
    assert_that(calling(runner.check_parameters).with_args({}),
                raises(RunnerError, 'Missing parameters.*server'))

def test_infos():
    infos = serverinfos_factory(ENGINE)
    assert_that(infos.available_servers, contains("localhost"))
    assert_that(infos.server_versions("all_servers"), empty())
    assert_that(infos.server_modes("all_servers"),
                contains(Job.InteractiveText))
    assert_that(infos.exec_modes(), empty())

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_success():
    xtest_success(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_init_from_database():
    xtest_init_from_database(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_run_with_data():
    xtest_run_with_data(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_run_with_smesh_data():
    xtest_run_with_smesh_data(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_run_with_embfiles():
    xtest_run_with_embfiles(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_run_with_error():
    xtest_run_with_error(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_failure():
    xtest_failure(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_several_stages():
    xtest_several_stages(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_zzzz241a():
    xtest_zzzz241a(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_zzzz241a_once():
    xtest_zzzz241a_once(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_25975():
    xtest_25975(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_27166():
    xtest_27166(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_userhost():
    xtest_userhost(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_run_with_directory():
    xtest_run_with_directory(ENGINE)


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
