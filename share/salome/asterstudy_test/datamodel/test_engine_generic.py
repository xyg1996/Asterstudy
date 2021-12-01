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

"""Automatic tests for running services."""


import os
import os.path as osp
import re
import subprocess as SP
import tempfile
import unittest
import warnings
import xml.etree.ElementTree as ET
from unittest.mock import Mock

from asterstudy.common import RunnerError
from asterstudy.datamodel.engine import Engine, version_ismpi
from asterstudy.datamodel.engine.engine_utils import (
    asrun_diag, convert_asrun_state, convert_launcher_state,
    create_profil_for_current, export_comm, kill_aster)
from asterstudy.datamodel.general import FileAttr
from asterstudy.datamodel.history import History
from asterstudy.datamodel.result import StateOptions as SO
from engine_testcases import DEFAULT_PARAMS, _setup_history
from hamcrest import *
from testutils import tempdir


def test_diagnostic_asrun():
    """Test for diagnostic conversion for AsRun"""
    states = ('_', 'PEND', 'SUSPENDED', 'RUN', 'ENDED')
    diags = (
        'OK', 'NOOK_TEST_RESU', 'NO_TEST_RESU', '<A>_ALARM',
        '<S>_ERROR', '<S>_CPU_LIMIT', '<S>_MEMORY_ERROR', '<S>_NO_CONVERGENCE',
        '<S>_CONTACT_ERROR',
        '<F>_ERROR', '<F>_SYNTAX_ERROR', '<F>_ABNORMAL_ABORT',
        '<F>_SUPERVISOR',
    )
    # loop on all possibilities
    for state in states:
        for diag in diags:
            ret = convert_asrun_state(state, diag)
            if state == 'RUN':
                assert_that(ret & SO.Finished, equal_to(0))
                assert_that(ret & SO.NotFinished)
                assert_that(ret & SO.Running)
                assert_that(ret & SO.Warn, equal_to(0))
                assert_that(ret & SO.CpuLimit, equal_to(0))
            elif state != 'ENDED':
                assert_that(ret & SO.Finished, equal_to(0))
                assert_that(ret & SO.NotFinished)
                assert_that(ret & SO.Pending)
                assert_that(ret & SO.Warn, equal_to(0))
                assert_that(ret & SO.CpuLimit, equal_to(0))
            else:
                assert_that(ret & SO.Finished)
                assert_that(ret & SO.NotFinished, equal_to(0))
                if '<A>' in diag:
                    assert_that(ret & SO.Warn)
                if '<S>' in diag:
                    assert_that(ret & SO.Interrupted)
                if '<F>' in diag:
                    assert_that(ret & SO.Error)
                if diag in ('NOOK_TEST_RESU', 'NO_TEST_RESU'):
                    assert_that(ret & SO.Nook)
    # test common combinaisons
    ret = convert_asrun_state('ENDED', '<A>_ALARM')
    assert_that(ret & SO.Finished)
    assert_that(ret & SO.Success)
    assert_that(ret & SO.Warn)

    ret = convert_asrun_state('ENDED', '<S>_CPU_LIMIT')
    assert_that(ret & SO.Finished)
    assert_that(ret & SO.Interrupted)
    assert_that(ret & SO.CpuLimit)

    ret = convert_asrun_state('ENDED', '<F>_ERROR')
    assert_that(ret & SO.Finished)
    assert_that(ret & SO.Error)
    assert_that(ret & SO.Warn, equal_to(0))

    ret = SO.Intermediate
    assert_that(ret & SO.Finished)
    assert_that(ret & SO.Error, equal_to(0))


def test_diagnostic_salome():
    """Test for diagnostic conversion for Salome"""
    states = ('CREATED', 'IN_PROCESS', 'QUEUED', 'RUNNING', 'PAUSED',
              'FINISHED', 'FAILED')
    diags = (
        'OK', 'NOOK_TEST_RESU', 'NO_TEST_RESU', '<A>_ALARM',
        '<S>_ERROR', '<S>_CPU_LIMIT', '<S>_MEMORY_ERROR', '<S>_NO_CONVERGENCE',
        '<S>_CONTACT_ERROR',
        '<F>_ERROR', '<F>_SYNTAX_ERROR', '<F>_ABNORMAL_ABORT',
        '<F>_SUPERVISOR',
    )
    # loop on all possibilities
    for state in states:
        for diag in diags:
            ret = convert_launcher_state(state, diag)
            if state == 'RUNNING':
                assert_that(ret & SO.Finished, equal_to(0))
                assert_that(ret & SO.NotFinished)
                assert_that(ret & SO.Running)
                assert_that(ret & SO.Warn, equal_to(0))
                assert_that(ret & SO.CpuLimit, equal_to(0))
            elif state not in ('FINISHED', 'FAILED'):
                assert_that(ret & SO.Finished, equal_to(0))
                assert_that(ret & SO.NotFinished)
                assert_that(ret & SO.Pending)
                assert_that(ret & SO.Warn, equal_to(0))
                assert_that(ret & SO.CpuLimit, equal_to(0))
            else:
                assert_that(ret & SO.Finished)
                assert_that(ret & SO.NotFinished, equal_to(0))
                if '<A>' in diag:
                    assert_that(ret & SO.Warn)
                if '<S>' in diag:
                    assert_that(ret & SO.Interrupted)
                if '<F>' in diag:
                    assert_that(ret & SO.Error)
                if diag in ('NOOK_TEST_RESU', 'NO_TEST_RESU'):
                    assert_that(ret & SO.Nook)
    # test common combinaisons
    ret = convert_launcher_state('FINISHED', '<A>_ALARM')
    assert_that(ret & SO.Finished)
    assert_that(ret & SO.Success)
    assert_that(ret & SO.Warn)

    ret = convert_launcher_state('FINISHED', '<S>_CPU_LIMIT')
    assert_that(ret & SO.Finished)
    assert_that(ret & SO.Interrupted)
    assert_that(ret & SO.CpuLimit)

    ret = convert_launcher_state('FINISHED', '<F>_ERROR')
    assert_that(ret & SO.Finished)
    assert_that(ret & SO.Error)
    assert_that(ret & SO.Warn, equal_to(0))

    ret = convert_launcher_state('FAILED')
    assert_that(ret & SO.Finished)
    assert_that(ret & SO.Error)
    assert_that(ret & SO.Warn, equal_to(0))

    # check cputime limit error
    output = "CPU time limit exceeded"
    filename = tempfile.mkstemp(prefix='diag')[1]
    with open(filename, "w") as fobj:
        fobj.write(output)
    diag = asrun_diag(filename)
    assert_that(diag, equal_to('<F>_CPU_LIMIT'))
    os.remove(filename)


def test_state_name():
    """Test for StateOptions names"""
    main = {
        SO.Waiting: "Waiting",
        SO.Pending: "Pending",
        SO.Running: "Running",
        SO.Pausing: "Pausing",
        SO.Success: "Success",
        SO.Error: "Error",
        SO.Interrupted: "Interrupted",
        SO.Intermediate: "Intermediate",
    }
    errors = {
        SO.Nook: "Nook",
        SO.CpuLimit: "CpuLimit",
        SO.NoConvergence: "NoConvergence",
        SO.Memory: "Memory",
    }
    for state, name in main.items():
        assert_that(SO.name(state), equal_to(name))
        state = state | SO.Intermediate
        if name != "Intermediate":
            assert_that(SO.name(state), equal_to(name + "+Intermediate"))
        else:
            assert_that(SO.name(state), equal_to(name))

    state = SO.Success | SO.Warn
    assert_that(SO.name(state), equal_to("Success+Warn"))

    state = SO.Error
    for add, name in errors.items():
        assert_that(SO.name(state | add), equal_to("Error+" + name))
        add = add | SO.Intermediate
        assert_that(SO.name(state | add),
                    equal_to("Error+" + name + "+Intermediate"))


@tempdir
def test_export_with_intermediate(tmpdir):
    """Test for creation of export with intermediate stages"""
    infos = Mock()
    infos.server_versions = Mock(return_value={})

    history = _setup_history(tmpdir)
    case = history.current_case
    params = DEFAULT_PARAMS.copy()
    # add a data file in stage s3
    info = case[2].handle2info[33]
    info.filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                             'data', 'export', 'forma13a.23')
    info.attr = FileAttr.In

    # check files in/out attribute
    assert_that(case[0].handle2info[44].first_attr,
                equal_to(FileAttr.Out))
    assert_that(case[1].handle2info[38].first_attr,
                equal_to(FileAttr.In))
    assert_that(case[2].handle2info[38].first_attr,
                equal_to(FileAttr.In))
    assert_that(case[2].handle2info[44].first_attr,
                equal_to(FileAttr.In))
    assert_that(case[2].handle2info[39].first_attr,
                equal_to(FileAttr.Out))
    assert_that(case[2].handle2info[33].first_attr,
                equal_to(FileAttr.No))
    assert_that(case[3].handle2info[38].first_attr,
                equal_to(FileAttr.In))
    assert_that(case[3].handle2info[44].first_attr,
                equal_to(FileAttr.In))
    assert_that(case[3].handle2info[39].first_attr,
                equal_to(FileAttr.Out))
    assert_that(info.first_attr, equal_to(FileAttr.No))

    prof = create_profil_for_current(None, case, case.stages,
                                     'test_inter', params, infos)

    data = [osp.basename(i.path) for i in prof.get_data()]
    result = [osp.basename(i.path) for i in prof.get_result()]
    for i in range(4):
        if i == 0:
            i = 'm'
        assert_that(data, has_item('test_inter.com{0}'.format(i)))
    assert_that(data, has_item('fileB.38'))
    assert_that(data, is_not(has_item('forma13a.23')))
    assert_that(data, has_length(5))
    assert_that(result, has_item('fileA.44'))
    assert_that(result, has_item('fileB.38'))
    assert_that(result, has_item('fileC.39'))
    assert_that(result, has_item('message'))
    assert_that(result, has_item('base-stage4'))
    assert_that(result, has_length(5))


@tempdir
def test_with_error(tmpdir):
    # same as xtest_run_with_error without execution
    umesh = 20
    unotexists = 34

    history = History()
    history.folder = tmpdir
    case = history.current_case
    case.name = 'c2'
    stage = case.create_stage('s1')
    stage('LIRE_MAILLAGE').init({'UNITE': umesh})
    stage('LIRE_MAILLAGE').init({'UNITE': unotexists})

    # add mesh file
    info20 = stage.handle2info[umesh]
    info20.filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                               'data', 'export', 'forma13a.20')
    assert_that(stage.handle2file(umesh), is_not(None))
    assert_that(info20.exists, equal_to(True))
    assert_that(info20.attr, equal_to(FileAttr.In))
    assert_that(info20.isreference, equal_to(False))
    assert_that(info20.first_attr, equal_to(FileAttr.In))

    # test for not existent data that references a mesh object
    info34 = stage.handle2info[unotexists]
    info34.filename = '0:1:8:9'
    info34.attr = FileAttr.In
    assert_that(info34.exists, equal_to(False))
    assert_that(info34.attr, equal_to(FileAttr.In))
    assert_that(info34.isreference, equal_to(True))
    assert_that(info34.first_attr, equal_to(FileAttr.In))

    infos = Mock()
    infos.server_versions = Mock(return_value={})
    params = DEFAULT_PARAMS.copy()

    assert_that(calling(create_profil_for_current)
                        .with_args(None, case, [stage],
                                   'test_files', params, infos),
                raises(RunnerError, "mesh object does not exist"))

    # check that export succeeds without the inexistent mesh object
    import shutil
    shutil.rmtree(case.folder)

    del stage[1]
    assert_that(info34.first_attr, equal_to(FileAttr.No))

    prof = create_profil_for_current(None, case, [stage],
                                     'test_files', params, infos)
    types = [data.type for data in prof.get_data()]
    assert_that(types, contains_inanyorder('comm', 'libr'))
    types = [data.type for data in prof.get_result()]
    assert_that(types, contains_inanyorder('mess', 'base'))

    # check that export fails with undefined output file
    import shutil
    shutil.rmtree(case.folder)

    info34 = stage.handle2info[unotexists]
    info34.attr = FileAttr.Out
    assert_that(calling(create_profil_for_current)
                        .with_args(None, case, [stage],
                                   'test_files', params, infos),
                raises(RunnerError, "filename not defined for unit 34"))


@tempdir
def test_comm_files(tmpdir):
    """Test for creation of comm files"""
    def _check_content(filename, starter, nbcmds):
        with open(filename) as file:
            content = file.read()
        assert_that(content, contains_string(starter))
        assert_that(content, contains_string('FIN'))
        assert_that(content.count('='), equal_to(nbcmds))

    text1 = """mesh = MODI_MAILLAGE()"""
    text2 = """model = AFFE_MODELE()"""
    text3 = """resu = MECA_STATIQUE()"""

    history = History()
    history.folder = tmpdir
    case = history.current_case
    case.name = 'c1'
    s1 = case.create_stage('s1')
    s1.use_text_mode()
    s2 = case.create_stage('s2')
    s2.use_text_mode()
    s3 = case.create_stage('s3')
    s3.use_text_mode()
    stages = [s1, s2, s3]

    # should create one commands file
    s1.set_text(text1)
    s2.set_text(text2)
    s3.set_text(text3)
    files = export_comm(stages, 'test1')
    assert_that(files, has_length(1))
    _check_content(files[0], 'DEBUT', 3)

    # force separated stages
    files = export_comm(stages, 'test1bis', separated=True)
    assert_that(files, has_length(3))
    _check_content(files[0], 'DEBUT', 1)
    _check_content(files[1], 'POURSUITE', 1)
    _check_content(files[2], 'POURSUITE', 1)

    # first separated
    s1.set_text(os.linesep.join(["DEBUT()", text1, "FIN()"]))
    files = export_comm(stages, 'test2')
    assert_that(files, has_length(2))
    _check_content(files[0], 'DEBUT', 1)
    _check_content(files[1], 'POURSUITE', 2)

    # all separated because of the second
    s1.set_text(text1)
    s2.set_text(os.linesep.join(["POURSUITE()", text2, "FIN()"]))
    files = export_comm(stages, 'test3')
    assert_that(files, has_length(3))
    _check_content(files[0], 'DEBUT', 1)
    _check_content(files[1], 'POURSUITE', 1)
    _check_content(files[2], 'POURSUITE', 1)

    # last separated
    s2.set_text(text2)
    s3.set_text(os.linesep.join(["POURSUITE()", text3, "FIN()"]))
    files = export_comm(stages, 'test4')
    assert_that(files, has_length(2))
    _check_content(files[0], 'DEBUT', 2)
    _check_content(files[1], 'POURSUITE', 1)


@tempdir
def test_comm_files_error(tmpdir):
    """Test for creation of comm files"""
    history = History()
    history.folder = tmpdir
    case = history.current_case
    case.name = 'c1'
    s1 = case.create_stage('s1')
    s1.use_text_mode()
    invalid = "invalid Python syntax + 1."
    s1.set_text(invalid)
    files = export_comm([s1], 'job')
    assert_that(files, has_length(1))

    # text is unchanged
    with open(files[0]) as comm:
        assert_that(comm.read(), equal_to(invalid))


def test_tail():
    """Test for tail utility"""
    from asterstudy.datamodel.engine.engine_utils import remote_tail
    text = remote_tail("", "localhost", os.path.splitext(__file__)[0] + ".py", 2)
    assert_that(text, contains_string("TextTestRunner"))
    assert_that(text, is_not(contains_string("__main__")))


def test_mpi_version():
    assert_that(version_ismpi('stable'), equal_to(False))
    assert_that(version_ismpi('stable_mpi'), equal_to(True))
    assert_that(version_ismpi('14.0'), equal_to(False))
    assert_that(version_ismpi('14.0_mpi'), equal_to(True))


def test_kill():
    fake_aster = ['python', '-c', 'import time; time.sleep(10)',
                  '--num_job=MYID', '--mode=interactif']
    aster = SP.Popen(fake_aster)
    pid = aster.pid
    with warnings.catch_warnings(record=True) as capw:
        killed = kill_aster("MYID")
        # no warning
        assert len(capw) == 0
    aster.wait()
    assert_that(killed, equal_to(pid))

    aster = SP.Popen(fake_aster)
    killed = kill_aster("MYID", "", "localhost")
    aster.wait()
    assert_that(killed, equal_to(999999))


def test_default():
    from asterstudy.datamodel.engine import init_default_engine
    assert_that(Engine.Default, equal_to(Engine.Salome))
    init_default_engine(Engine.Salome)
    assert_that(Engine.Default, equal_to(Engine.Salome))


@tempdir
def test_params2export(tmpdir):
    infos = Mock()
    infos.server_versions = Mock(return_value={})

    history = _setup_history(tmpdir)
    case = history.current_case
    params = DEFAULT_PARAMS.copy()
    params['time'] = '01:02:03'
    params['args'] = '--max_base=99999'
    params['threads'] = 28 / 3.
    prof = create_profil_for_current(None, case, [case[0], ],
                                     'test_params', params, infos)

    assert_that(prof['time_limit'][0], equal_to(3600 + 2 * 60 + 3))
    assert_that(prof['ncpus'][0], equal_to(9))
    text = str(prof)
    assert_that(text, contains_string("A args --max_base=99999"))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
