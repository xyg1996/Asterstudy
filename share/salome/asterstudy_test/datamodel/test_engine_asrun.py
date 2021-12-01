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


import unittest
import time

from hamcrest import *
from testutils import tempdir

from asterstudy.common import RunnerError
from asterstudy.datamodel.result import StateOptions as SO
from asterstudy.datamodel.engine.engine_utils import has_asrun
from asterstudy.datamodel.engine import runner_factory, serverinfos_factory, Engine

from engine_testcases import (_setup_run_case, _parameters,
                              xtest_infos,
                              xtest_run_with_data,
                              xtest_run_with_smesh_data,
                              xtest_run_with_embfiles,
                              xtest_run_with_error,
                              xtest_failure,
                              xtest_success,
                              xtest_several_stages,
                              xtest_stop,
                              xtest_reload,
                              xtest_zzzz241a,
                              xtest_zzzz241a_once,
                              xtest_25975,
                              xtest_27166,
                              xtest_userhost,
                              xtest_init_from_database,
                              xtest_run_with_directory)

_multiprocess_can_split_ = False
ENGINE = Engine.AsRun


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_asrun_import():
    # check for import error
    import sys
    sys.modules['asrun'] = None
    has_asrun.cache = None
    assert_that(has_asrun(), equal_to(False))
    del sys.modules['asrun']
    has_asrun.cache = None
    assert_that(has_asrun(), equal_to(True))


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_infos():
    xtest_infos(ENGINE)


@unittest.skipIf(not has_asrun(), "asrun is required")
@tempdir
def test_initial_checking(tmpdir, server=None):
    nbs = 1
    rc1 = _setup_run_case(tmpdir, 0)
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))

    runner = runner_factory(ENGINE, case=rc1, logger=lambda x: None,
                            unittest=True)

    # initialisation checkings
    assert_that(calling(runner.check_parameters).with_args({}),
                raises(RunnerError, 'Missing parameters.*server'))

    params = _parameters(ENGINE, server, failure=True)
    runner.check_parameters(params)
    assert_that(calling(getattr).with_args(runner, 'hdlr'),
                raises(RunnerError, 'Unknown server'))


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
def test_success():
    xtest_success(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_several_stages():
    xtest_several_stages(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_stop():
    xtest_stop(ENGINE)

@unittest.skipIf(not has_asrun(), "asrun is required")
def test_reload():
    xtest_reload(ENGINE)

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

@unittest.skipIf(not has_asrun(), "asrun is required")
@unittest.skip("`--nologcapture` option of nosetests is required")
def test_logging():
    text = []
    infos = serverinfos_factory(ENGINE)
    infos.set_log_callback(text.append)
    from asrun.core import magic
    magic.log.info("info called")
    assert_that(text, has_length(1))


@unittest.skipIf(not has_asrun(), "asrun is required")
@tempdir
def test_submission_failure1(tmpdir):
    rc1 = _setup_run_case(tmpdir, 0)
    expected_results = rc1.results()

    runner = runner_factory(ENGINE, case=rc1, unittest=True)
    assert_that(runner.result_state(expected_results[0]) & SO.Waiting)

    # force an error by changing the server configuration on the fly!
    params = _parameters(ENGINE)
    cfg = runner._infos.server_config(params['server'])
    # add another server for this test
    runner._infos._client._serv['test_server'] = cfg.copy()
    cfg = runner._infos.server_config('test_server')
    params['server'] = 'test_server'
    cfg['rep_serv'] = '/unavailable_directory'
    try:
        assert_that(calling(runner.start).with_args(params),
                    raises(RunnerError))
        assert_that(runner.result_state(expected_results[0]) & SO.Error)
    finally:
        del runner._infos._client._serv['test_server']

    time.sleep(0.25)
    runner.cleanup()


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
