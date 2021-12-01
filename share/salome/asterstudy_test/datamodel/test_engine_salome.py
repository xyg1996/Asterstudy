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

"""Automatic tests for Salome services.

This tests must be run in the SALOME environment, using "salome shell" and
with a SALOME application running.

Example::

    salome start -t
    <running unittests>
    salome shell killSalome.py
"""


import unittest
import os
import os.path as osp
import tempfile
import time
import shutil

from hamcrest import *
from testutils import tempdir, attr

from asterstudy.common import RunnerError, CFG, StudyDirectoryError
from asterstudy.datamodel.result import StateOptions as SO
from asterstudy.datamodel.engine import runner_factory, serverinfos_factory, Engine
from asterstudy.datamodel.engine.engine_utils import database_path
from asterstudy.datamodel.engine.salome_runner import (has_salome, remote_file_copy,
                                                       salome_shell)

from engine_testcases import (_setup_run_case, _parameters,
                              xtest_infos,
                              xtest_init_from_database,
                              xtest_run_with_data,
                              xtest_run_with_smesh_data,
                              xtest_run_with_embfiles,
                              xtest_run_with_error,
                              xtest_failure,
                              xtest_success_with_results,
                              xtest_success,
                              xtest_several_stages,
                              xtest_stop,
                              xtest_reload,
                              xtest_zzzz241a,
                              xtest_zzzz241a_once,
                              xtest_25975,
                              xtest_27166,
                              xtest_userhost,
                              xtest_run_with_directory,
                              xtest_override_output_dir,
                              xtest_error_output_dir)

_multiprocess_can_split_ = False
ENGINE = Engine.Salome


def test_closures():
    """Test for unavailable engines"""
    assert_that(calling(serverinfos_factory).with_args(engine=0x1000),
                raises(TypeError))
    assert_that(calling(runner_factory).with_args(engine=0x1000),
                raises(TypeError))

@unittest.skipIf(not has_salome(), "salome is required")
def test_singleton():
    """Test for singleton of SalomeInfos"""
    name = '_0_server1_0_'
    info1 = serverinfos_factory()   # Engine.Default is Engine.Salome
    info1._servers.append(name)
    info2 = serverinfos_factory(ENGINE)
    assert_that(info1, same_instance(info2))
    # if the unittests are executed in the same session, another SalomeInfos
    # may have been created before, so it may contain "real" servers!
    assert_that(name, is_in(info2._servers))
    info2._servers.remove(name)
    assert_that(name, is_not(is_in(info1._servers)))


@unittest.skipIf(not has_salome(), "salome is required")
def test_infos():
    """Test for servers informations for SALOME"""
    xtest_infos(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_init_from_database():
    xtest_init_from_database(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_run_with_data():
    xtest_run_with_data(ENGINE)

# Salome is required anyway for this test
def test_run_with_smesh_data():
    xtest_run_with_smesh_data(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_run_with_embfiles():
    xtest_run_with_embfiles(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_run_with_error():
    xtest_run_with_error(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_failure():
    xtest_failure(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_success_with_results():
    xtest_success_with_results(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_success():
    xtest_success(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_several_stages():
    xtest_several_stages(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_stop():
    xtest_stop(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_reload():
    xtest_reload(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_zzzz241a():
    xtest_zzzz241a(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_zzzz241a_once():
    xtest_zzzz241a_once(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_25975():
    xtest_25975(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_27166():
    xtest_27166(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_userhost():
    xtest_userhost(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_run_with_directory():
    xtest_run_with_directory(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_override_output_dir():
    xtest_override_output_dir(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
def test_error_output_dir():
    xtest_error_output_dir(ENGINE)

@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def test_submission_failure1(tmpdir):
    """Test for salome runner with submission failure 1"""
    rc1 = _setup_run_case(tmpdir, 0)
    expected_results = rc1.results()

    # default engine is Engine.Salome
    runner = runner_factory(case=rc1, unittest=True)
    assert_that(runner.result_state(expected_results[0]) & SO.Waiting)

    # force an error by changing the server configuration on the fly!
    params = _parameters(ENGINE)
    params['server'] = 'unknown'
    assert_that(calling(runner.start).with_args(params),
                raises(RunnerError))
    assert_that(runner.result_state(expected_results[0]) & SO.Error)

    # test for init of salomelauncher job
    job = rc1.stages[0].result.job
    job.dump_string = "<xml/>"
    runner._init_job(job)

    time.sleep(0.25)
    runner.cleanup()


@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def test_submission_failure2(tmpdir):
    """Test for salome runner with submission failure 2"""
    rc1 = _setup_run_case(tmpdir, 0)
    expected_results = rc1.results()

    runner = runner_factory(ENGINE, case=rc1, unittest=True)
    assert_that(runner.result_state(expected_results[0]) & SO.Waiting)

    # force an error by changing the server configuration on the fly!
    params = _parameters(ENGINE)
    params['server'] = 'unknown'
    class FakeDef:
        applipath = "/fake/appli"
        working_directory = "/fake/tmp"

    runner._infos._cfg['unknown'] = {'rc_definition': FakeDef()}
    assert_that(calling(runner.start).with_args(params),
                raises(RunnerError))
    assert_that(runner.result_state(expected_results[0]) & SO.Error)

    time.sleep(0.25)

    # ensure it does nothing and not fails because the job is unknown
    runner.get_job_results(expected_results[0].job)
    runner.cleanup()


@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def test_remote_utils(tmpdir):
    """Test for utilities for remote executions"""
    infos = serverinfos_factory(ENGINE)
    assert_that(infos.available_servers, has_item('localhost'))
    rc = _setup_run_case(tmpdir, 0)
    stage = rc[0]

    dirname = osp.join('Result-' + stage.name, 'base-stage1')
    assert_that(database_path(stage, infos, 'localhost'),
                equal_to(osp.join(tmpdir, rc.name,dirname)))
    # Simulate remote databases
    stage.set_remote('REMOTE')
    remotedir = osp.join('REMOTE', osp.basename(tmpdir),
                         rc.name, 'Result-' + stage.name)
    assert_that(stage.remote_folder, equal_to(remotedir))

    host = infos.server_hostname('localhost')
    user = infos.server_username('localhost')
    user = user + '@' if user else ''
    assert_that(database_path(stage, infos, 'localhost'),
                equal_to(osp.join(user + host + ':' + remotedir,
                                  'base-stage1')))
    # Another time to pass check of equality
    assert_that(calling(stage.set_remote).with_args('ANOTHER_ONE'),
                raises(StudyDirectoryError, 'differ'))


@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def test_remote_copy_utils(tmpdir):
    """Test for remote copy (uses 'ssh localhost')"""
    dest = tempfile.mkdtemp()
    os.rmdir(dest)
    assert_that(osp.exists(dest), equal_to(False))

    rc1 = _setup_run_case(tmpdir, 0)

    infos = serverinfos_factory(ENGINE)
    infos.export_remote_input_files('localhost', [osp.abspath(__file__)], dest, False)
    assert_that(osp.isfile(osp.join(dest, osp.basename(__file__))),
                equal_to(True))
    shutil.rmtree(dest)

    assert_that(calling(remote_file_copy)
                .with_args('', 'localhost', '/zzz', '/xxx', False),
                raises(OSError))

    assert_that(calling(infos.export_remote_input_files)
                .with_args('localhost', ['zzz'], '/xxx', False),
                raises(IOError))


def test_shell():
    assert_that(salome_shell('appli', 'command'),
                equal_to('appli/salome shell -- command'))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
