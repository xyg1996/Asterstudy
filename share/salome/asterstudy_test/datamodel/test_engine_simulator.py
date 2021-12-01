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


import os
import os.path as osp
import time
import unittest
from functools import partial

from asterstudy.common import debug_message
from asterstudy.common.remote_utils import MOUNT
from asterstudy.datamodel.engine import (Engine, default_parameters,
                                         runner_factory, serverinfos_factory)
from asterstudy.datamodel.history import History
from asterstudy.datamodel.result import Job, MsgLevel, MsgType
from asterstudy.datamodel.result import StateOptions as SO
from engine_testcases import xtest_userhost
from hamcrest import *
from testutils import tempdir

# duration of a calculation in Simulator runner
DURATION = 0.1


def test_simulator_infos():
    """Test for servers informations for the simulator"""
    infos = serverinfos_factory(engine=Engine.Simulator)
    assert_that(infos.available_servers, has_item('localhost'))
    assert_that(infos.server_versions('localhost'), has_item('stable'))
    assert_that(infos.exec_modes(), contains(Job.ExecOptimText))
    assert_that(infos.server_modes('localhost'), has_item(Job.InteractiveText))
    assert_that(infos.server_by_host('localhost'), equal_to('localhost'))
    # does nothing
    infos.refresh_once('localhost')

    previously_mounted = set(MOUNT.uri)
    infos.mount_filesystem('XX')
    added = set(MOUNT.uri).difference(previously_mounted)
    time.sleep(1)
    if added:
        MOUNT.unmount(added.pop())

def test_userhost():
    xtest_userhost(Engine.Simulator)


@tempdir
def test_simulator_runner_one(tmpdir):
    """Test for simulator runner with one success"""
    nbs = 1
    rc1 = _setup_run_case(tmpdir, 0)
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))
    assert_that(rc1.is_remote(), equal_to(False))

    params = { 'mode': Job.BatchText }
    # force success for first stage
    params['forced_states'] = { rc1[0]: True }
    runner = runner_factory(case=rc1, engine=Engine.Simulator, unittest=True)

    assert_that(runner.is_started(), equal_to(False))
    assert_that(runner.is_finished(), equal_to(False))
    assert_that(runner.result_state(expected_results[0]), equal_to(SO.Waiting))
    assert_that(rc1.is_running(), equal_to(True))

    runner.start(params)
    assert_that(runner.is_started(), equal_to(True))
    monitor_refresh(runner, estimated_time=nbs * DURATION)

    assert_that(rc1.is_remote(), equal_to(False))
    assert_that(runner.result_state(expected_results[0]), equal_to(SO.Success))
    assert_that(rc1.is_running(), equal_to(False))
    jobid = expected_results[0].job.jobid
    assert_that(jobid.isdigit())
    assert_that(expected_results[0].job.jobid_int, is_not(equal_to(0)))
    assert_that(expected_results[0].job.mode & Job.Batch, equal_to(True))
    assert_that(runner.is_finished(), equal_to(True))

    # simulator adds random messages + a warning on the command
    warn = [msg for msg in expected_results[0].messages \
            if msg.level == MsgLevel.Warn and 'Simulator' in msg.text]
    assert_that(warn, has_length(1))
    warn = warn[0]
    # only one command
    command = rc1[0][0]
    assert_that(warn.source, equal_to(MsgType.Command))
    assert_that(warn.command_num, equal_to(command.uid))


@tempdir
def test_simulator_runner_fail(tmpdir):
    """Test for simulator runner with failure"""
    nbs = 4
    rc1 = _setup_run_case(tmpdir, [0, 3], reusable_stages=[1, 2, 3])
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))

    runner = runner_factory(case=rc1, engine=Engine.Simulator, unittest=True)

    assert_that(runner.result_state(expected_results[0]),
                equal_to(SO.Intermediate | SO.Waiting))

    params = {}
    # force success for the stage two (first is an intermediate one)
    # and failure for the third one
    params['forced_states'] = { rc1[1]: True, rc1[2]: False }
    runner.start(params)
    monitor_refresh(runner, estimated_time=nbs * DURATION)

    assert_that(runner.result_state(expected_results[0]),
                equal_to(SO.Intermediate | SO.Success))
    assert_that(runner.result_state(expected_results[1]), equal_to(SO.Success))
    assert_that(runner.result_state(expected_results[2]), equal_to(SO.Error))
    assert_that(runner.result_state(expected_results[3]),
                equal_to(SO.Waiting))


@tempdir
def test_simulator_runner_success(tmpdir):
    """Test for simulator runner with success"""
    nbs = 2
    rc1 = _setup_run_case(tmpdir, [0, 1], reusable_stages=[0, 1])
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))

    runner = runner_factory(case=rc1, engine=Engine.Simulator, unittest=True)

    assert_that(runner.result_state(expected_results[0]), equal_to(SO.Waiting))

    params = {}
    # force success for first stage, pass in random state for the second
    params['forced_states'] = { rc1[0]: True }
    runner.start(params)
    monitor_refresh(runner, estimated_time=nbs * DURATION)

    assert_that(runner.result_state(expected_results[0]), equal_to(SO.Success))
    assert_that(runner.result_state(expected_results[1]),
                is_in([SO.Success, SO.Error]))

    # check for runcase directory renaming
    prev = rc1.folder
    assert_that(osp.basename(prev), equal_to("rc1"))
    assert_that(osp.isdir(prev), equal_to(True))
    rc1.rename("newdir")
    assert_that(osp.basename(rc1.folder), equal_to("newdir"))
    assert_that(osp.isdir(rc1.folder), equal_to(True))


@tempdir
def test_simulator_runner_pause(tmpdir):
    """Test for pause/resume for simulator runner"""
    nbs = 2
    rc1 = _setup_run_case(tmpdir, [0, 1], reusable_stages=[0, 1])
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))

    runner = runner_factory(case=rc1, engine=Engine.Simulator, unittest=True)

    assert_that(runner.result_state(expected_results[0]), equal_to(SO.Waiting))

    params = {}
    # force success for first stage
    params['forced_states'] = { rc1[0]: True }
    runner.start(params)
    monitor_pause(runner, nbs * DURATION)

    assert_that(runner.result_state(expected_results[0]), equal_to(SO.Error))


@tempdir
def test_simulator_runner_stop(tmpdir):
    """Test for stop for simulator runner"""
    nbs = 2
    rc1 = _setup_run_case(tmpdir, [0, 1], reusable_stages=[0, 1])
    expected_results = rc1.results()
    assert_that(expected_results, has_length(nbs))

    runner = runner_factory(case=rc1, engine=Engine.Simulator, unittest=True)
    assert_that(runner.result_state(expected_results[0]), equal_to(SO.Waiting))

    params = {}
    # force success for first stage
    params['forced_states'] = { rc1[0]: True }
    params['forced_stop'] = [False, True]
    runner.start(params)
    # first stop should not work
    runner.stop()
    assert_that(runner.result_state(expected_results[0]), equal_to(SO.Running))
    runner.stop()
    assert_that(runner.result_state(expected_results[0]), equal_to(SO.Error))
    assert_that(runner.result_state(expected_results[1]), equal_to(SO.Waiting))


@tempdir
def test_simulator_runner_reload(tmpdir):
    """Test for close/reload for simulator runner"""
    ajsfile = osp.join(tmpdir, 'asterstudy-reload.ajs')

    # use separated namespaces
    nbs = 2
    def step1():
        history = History()
        history.folder = tmpdir
        cc = history.current_case
        cc.name = 'c1'
        cc.create_stage('s1')
        cc.create_stage('s2')

        rc1 = history.create_run_case(exec_stages=[0, 1],
                                      reusable_stages=[0, 1], name='rc1')
        expected_results = rc1.results()
        assert_that(expected_results, has_length(nbs))

        runner = runner_factory(case=rc1, engine=Engine.Simulator,
                                unittest=True)

        assert_that(runner.result_state(expected_results[0]),
                                        equal_to(SO.Waiting))

        runner.start({})
        assert_that(runner.result_state(expected_results[0]),
                                        equal_to(SO.Running))
        History.save(history, ajsfile)

    def step2():
        history = History.load(ajsfile)
        history.folder = tmpdir
        assert_that(history.run_cases, has_length(1))
        rc1 = history.run_cases[0]

        expected_results = rc1.results()
        assert_that(expected_results, has_length(nbs))

        runner = runner_factory(case=rc1, engine=Engine.Simulator,
                                unittest=True)
        params = {}
        # force success for first stage
        params['forced_states'] = { rc1[0]: True }
        runner.check_parameters(params)
        assert_that(runner.result_state(expected_results[0]),
                                        equal_to(SO.Running))
        # of course the start time was lost!
        runner._tinit = time.time() - 10.
        runner.refresh()
        assert_that(runner.result_state(expected_results[0]),
                                        equal_to(SO.Success))
    try:
        step1()
        step2()
    finally:
        if osp.exists(ajsfile):
            os.remove(ajsfile)


@tempdir
def test_reusability(tmpdir):
    """Test for reusability of stages"""
    rc1 = _setup_run_case(tmpdir, [0, 2])
    assert_that(rc1[0].state & SO.Intermediate)
    assert_that(rc1[0].state & SO.Waiting)
    assert_that(rc1[1].state & SO.Intermediate)
    assert_that(rc1[1].state & SO.Waiting)
    assert_that(rc1[2].state & SO.Waiting)

    rc2 = _setup_run_case(tmpdir, [0, 2], reusable_stages=[0, 2])
    assert_that(rc2[0].state & SO.Waiting)
    assert_that(rc2[1].state & SO.Intermediate)
    assert_that(rc2[1].state & SO.Waiting)
    assert_that(rc2[2].state & SO.Waiting)

    rc3 = _setup_run_case(tmpdir, exec_stages=None, reusable_stages=3)
    assert_that(rc3[0].state & SO.Intermediate)
    assert_that(rc3[0].state & SO.Waiting)
    assert_that(rc3[1].state & SO.Intermediate)
    assert_that(rc3[1].state & SO.Waiting)
    assert_that(rc3[2].state & SO.Intermediate)
    assert_that(rc3[2].state & SO.Waiting)
    assert_that(rc3[3].state & SO.Waiting)


@tempdir
def test_simulator_reusability(tmpdir):
    """Test for reusability of stages with simulator (issue27166)"""
    rc1 = _setup_run_case(tmpdir, [0, 2], reusable_stages=[2])
    assert_that(rc1[0].is_intermediate(), equal_to(True))
    assert_that(rc1[1].is_intermediate(), equal_to(True))
    assert_that(rc1[2].is_intermediate(), equal_to(False))
    assert_that(rc1[0].is_without_db(), equal_to(True))
    assert_that(rc1[1].is_without_db(), equal_to(True))
    assert_that(rc1[2].is_without_db(), equal_to(False))

    expected_results = rc1.results()
    assert_that(expected_results, has_length(3))

    runner = runner_factory(case=rc1, engine=Engine.Simulator, unittest=True)

    assert_that(runner.result_state(expected_results[0]),
                equal_to(SO.Intermediate | SO.Waiting))
    assert_that(runner.result_state(expected_results[1]),
                equal_to(SO.Intermediate | SO.Waiting))

    params = {}
    # force success for the stage three (first are intermediate ones)
    params['forced_states'] = { rc1[2]: True }
    runner.start(params)
    monitor_refresh(runner, estimated_time=5 * DURATION)

    assert_that(runner.result_state(expected_results[0]),
                equal_to(SO.Intermediate | SO.Success))
    assert_that(runner.result_state(expected_results[1]),
                equal_to(SO.Intermediate | SO.Success))
    assert_that(runner.result_state(expected_results[2]), equal_to(SO.Success))

    history = rc1.model
    rc2 = history.create_run_case(exec_stages=[3, 3],
                                  reusable_stages=[],
                                  name='rc2')
    assert_that(rc2[3].is_intermediate(), equal_to(False))
    assert_that(rc2[3].is_without_db(), equal_to(True))

    expected_results = rc2.results()
    assert_that(expected_results, has_length(4))

    runner = runner_factory(case=rc2, engine=Engine.Simulator, unittest=True)

    assert_that(runner.result_state(expected_results[0]),
                equal_to(SO.Intermediate | SO.Success))
    assert_that(runner.result_state(expected_results[1]),
                equal_to(SO.Intermediate | SO.Success))
    assert_that(runner.result_state(expected_results[2]), equal_to(SO.Success))
    assert_that(runner.result_state(expected_results[3]), equal_to(SO.Waiting))

    params = {}
    # force success
    params['forced_states'] = { rc2[3]: True }
    runner.start(params)
    monitor_refresh(runner, estimated_time=5 * DURATION)

    assert_that(runner.result_state(expected_results[3]), equal_to(SO.Success))

    assert_that(len(history.run_cases), greater_than(0))
    last_params = history.last_params().asdict()
    assert_that(last_params, has_key('mode'))
    assert_that(last_params, has_key('jobid'))

@tempdir
def test_simulator_restore_run_cases(tmpdir):
    rc1 = _setup_run_case(tmpdir, [0, 1])
    assert_that(rc1[0].is_intermediate(), equal_to(True))
    assert_that(rc1[1].is_intermediate(), equal_to(False))
    assert_that(rc1[0].state & SO.Waiting)
    assert_that(rc1[1].state & SO.Waiting)

    expected_results = rc1.results()
    assert_that(expected_results, has_length(2))

    runner = runner_factory(case=rc1, engine=Engine.Simulator, unittest=True)

    # done by DashBoard.restore_run_cases at reload
    # result_state must detect the intermediate stage
    assert_that(runner.stages_stack, has_length(0))
    state = runner.result_state(rc1[1].result)
    assert_that(runner.stages_stack, has_length(1))
    assert_that(state, equal_to(SO.Waiting))

# test utilities
def monitor_refresh(runner, estimated_time):
    """Refresh states up to the estimated end of all the computations"""
    delay = estimated_time * 1.20 / 8
    for i in range(8):
        time.sleep(delay)
        current = runner.current
        if current:
            state = runner.result_state(current)
            debug_message("Refresh", (i + 1) * delay, SO.name(state))
            if runner.is_finished():
                break
        else:
            debug_message("Refresh", (i + 1) * delay, "nothing to process")

    runner.cleanup()
    time.sleep(delay)

def monitor_pause(runner, estimated_time):
    """Simulate pause and resume."""
    delay = estimated_time * 1.20 / 4
    idx = range(4)
    result, res1 = runner._queue

    assert_that(runner.result_state(result), equal_to(SO.Running))
    assert_that(runner.result_state(res1), equal_to(SO.Waiting))

    runner.pause()
    assert_that(runner.result_state(result), equal_to(SO.Pausing))

    runner.resume()
    assert_that(runner.result_state(result), equal_to(SO.Running))

    runner.stop()
    assert_that(runner.result_state(result), equal_to(SO.Error))
    assert_that(runner.result_state(res1), equal_to(SO.Waiting))

    runner.cleanup()

def _setup_run_case(tmpdir, exec_stages, reusable_stages=None):
    """Return a new history with a runnable 'current' case."""
    history = History()
    history.folder = tmpdir
    cc = history.current_case
    cc.name = 'c1'
    cc.create_stage('s1')
    cc.create_stage('s2')
    cc.create_stage('s3')
    cc.create_stage('s4')
    # to test messages
    s1 = cc[0]
    s1.use_graphical_mode()
    s1.add_command('LIRE_MAILLAGE', 'mesh')

    run_case = history.create_run_case(exec_stages=exec_stages,
                                       reusable_stages=reusable_stages,
                                       name='rc1')
    return run_case


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
