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


import os
import os.path as osp
import time
import unittest

from asterstudy.common.remote_utils import remote_exec
from asterstudy.datamodel import History
from asterstudy.datamodel.engine import (Engine, runner_factory,
                                         serverinfos_factory)
from asterstudy.datamodel.engine.engine_utils import (
    _convert_launcher_state, code_aster_exit_code, convert_state_from_message,
    database_path, default_parameters, from_asrun_params, has_asrun,
    parse_server_config, remote_file_copy)
from asterstudy.datamodel.engine.salome_runner import (SalomeInfos,
                                                       create_command_job,
                                                       has_salome)
from asterstudy.datamodel.result import Job
from asterstudy.datamodel.result import StateOptions as SO
from engine_testcases import _setup_run_case
from hamcrest import *
from testutils import attr, tempdir


@unittest.skipIf(not has_asrun(), "asrun is required")
@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def test_console_mode(tmpdir):
    from asrun import create_profil

    infos = serverinfos_factory(Engine.Salome)
    assert_that(infos.available_servers, has_item('localhost'))
    rc = _setup_run_case(tmpdir, 0)
    stage = rc[0]

    cfg = infos.server_config('localhost')
    params = default_parameters()
    params['mode'] = Job.ConsoleText

    prof = create_profil()

    os.makedirs(stage.folder)

    sjob = create_command_job(cfg, params, prof, stage)
    assert_that(sjob.job_type, equal_to("command_salome"))


@unittest.skipIf(not has_asrun(), "asrun is required")
def test_parse():
    from asrun import create_profil

    output = remote_exec("", "", "as_run --info")
    cfg = parse_server_config(output)
    assert_that(cfg, has_key("vers"))
    assert_that("stable", is_in(cfg["vers"]))

    prof = create_profil()
    prof['server'] = "localhost"
    prof['memory_limit'] = 1024
    prof['time_time'] = 60
    prof['version'] = "testing"
    prof['mpi_nbcpu'] = 16
    prof['mpi_nbnoeud'] = 2
    prof['ncpus'] = 8
    params = from_asrun_params(prof)
    assert_that("memory", is_in(params))
    assert_that("version", is_in(params))
    assert_that("threads", is_in(params))
    assert_that(params["memory"], equal_to(1024))
    assert_that(params["version"], equal_to("testing"))
    assert_that(params["threads"], equal_to(8))


def test_timeout():
    tini = time.time()
    assert_that(calling(remote_exec)
                .with_args("", "",
                           "echo 'starting...' ; sleep 60 ; echo 'ended'",
                           timeout=2),
                raises(OSError, "Command not finished"))
    assert_that(time.time() - tini, less_than(3.))


def test_0():
    history = History()
    case = history.current_case
    stage = case.create_stage('s1')

    assert_that(calling(runner_factory).with_args(case=case),
                raises((TypeError, AttributeError)))
    assert_that(serverinfos_factory(), instance_of(SalomeInfos))

    infos = serverinfos_factory(Engine.Simulator)
    stage.result.has_remote = True
    assert_that(stage.database_path, equal_to("Result-s1/base-stage1"))
    path = database_path(stage, infos, 'localhost')
    assert_that(path, equal_to("localhost:Result-s1/base-stage1"))


@tempdir
def test_1(tmpdir):
    filename = osp.join(tmpdir, 'message')

    with open(filename, "w") as fmess:
        fmess.write("EXECUTION_CODE_ASTER_EXIT_0123456789=0\n")
    assert_that(code_aster_exit_code(filename), equal_to(SO.Success))

    with open(filename, "w") as fmess:
        fmess.write("EXECUTION_CODE_ASTER_EXIT_0123456789=139\n")
        fmess.write("--- DIAGNOSTIC JOB : <F>_ERROR\n")

    assert_that(_convert_launcher_state("FINISHED", full=True),
                equal_to(SO.Success))
    # 'message' files do not contain diagnostic, only 'logs/output*' do.
    # error is detected from exit code.
    assert_that(convert_state_from_message("FINISHED", filename),
                equal_to(SO.Success))
    assert_that(code_aster_exit_code(filename), equal_to(SO.Error))

    dest = osp.join(tmpdir, "destdir", "out")
    log = remote_file_copy("", "", filename, dest, isdir=False)
    assert_that(log, equal_to(""))
    assert_that(osp.isfile(dest), equal_to(True))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
