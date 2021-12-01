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
import os.path as osp
import random
import shutil
import unittest

from asterstudy.api import ParametricCalculation
from asterstudy.common import debug_message, debug_mode
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.engine import Engine, runner_factory
from asterstudy.datamodel.engine.engine_utils import ExportCase
from asterstudy.datamodel.engine.salome_runner import has_salome
from asterstudy.datamodel.history import History
from asterstudy.datamodel.parametric import (export_to_openturns,
                                             output_commands)
from asterstudy.datamodel.result import StateOptions as SO
from asterstudy.datamodel.study2comm import study2comm
from engine_testcases import _parameters, monitor_refresh
from hamcrest import *
from testutils import attr, tempdir

_multiprocess_can_split_ = False


def _setup_nominal(tmpdir):
    history = History()
    if not history.support.parametric:
        return None

    history.folder = tmpdir
    case = history.current_case
    case.name = 'beam'

    # first stage
    stage1 = case.create_stage('deflection')
    cmd_file = osp.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'export', 'parametric_beam.comm')
    with open(cmd_file) as comm:
        comm2study(comm.read(), stage1)

    info = stage1.handle2info[20]
    info.filename = osp.join(os.getenv('ASTERSTUDYDIR'),
                             'data', 'export', 'sslv159b.mail')

    # second stage containing IMPR_TABLE
    stage2 = case.create_stage('output')
    cmd_file = osp.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'export', 'parametric_beam.com1')
    with open(cmd_file) as comm:
        comm2study(comm.read(), stage2)

    info = stage2.handle2info[10]
    info.filename = osp.join(tmpdir, 'result_file.npy')

    # third stage containing unnecessary commands
    stage3 = case.create_stage('ignored')
    cmd_file = osp.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'export', 'parametric_beam.com2')
    with open(cmd_file) as comm:
        comm2study(comm.read(), stage3)

    # not called by open_openturns!
    param_case = history.create_parametric_case()
    return param_case

def _setup_and_check_ot(case, tmpdir, mem_limit=None, run=True):
    # inputs for the widget
    varnames = case.variables.keys()
    outcmd = output_commands(case)

    # outputs of the widget: user's selection : 'input_vars' & 'command'
    input_vars = ["E", "F"]
    assert_that(varnames, has_items(*input_vars))
    assert_that(outcmd, has_length(1))
    command = outcmd[0]

    otdata = export_to_openturns(case, input_vars, command)
    debug_message(("-" * 30 + "\n{0}\n" + "-" * 30).format(otdata.code))
    debug_message("Input files and directories:\n{0}".format(otdata.files))
    debug_message("Job parameters:\n{0}".format(otdata.parameters))
    assert_that(otdata.code.strip(), contains_string("def _exec("))
    assert_that(otdata.code,
                contains_string("ParametricCalculation("))

    export = osp.join(tmpdir, "ParamCase_1", "parametric.export")
    with open(export) as fexp:
        content = fexp.read()
    assert_that(content, contains_string("parametric.comm"))
    assert_that(content, contains_string("parametric.com1"))
    assert_that(content, is_not(contains_string("parametric.com2")))
    # check that parameters are taken from the previous execution
    assert_that(content, contains_string("memory_limit %s" % (mem_limit or 2048)))

    if not run:
        return

    # next steps are done in OpenTurns
    # check with F = twice the nominal value
    context = {}
    # run silently in unittest
    code = otdata.code.replace("if True:", "if False:")
    exec(code, context)

    # executed by salome launcher in a working directory
    # copy input files
    prev = os.getcwd()
    wrkdir = osp.join(tmpdir, 'wrkdir')
    os.makedirs(wrkdir)
    os.chdir(wrkdir)
    for infile in ("parametric.comm", "parametric.com1", "parametric.export",
                   "sslv159b.mail"):
        shutil.copyfile(osp.join(tmpdir, "ParamCase_1", infile),
                        osp.join(wrkdir, infile))
    try:
        results = context['_exec'](2.e11, -1000.)
    finally:
        os.chdir(prev)

    assert_that(results, has_length(3))
    assert_that(results[0], equal_to(0.5))
    assert_that(results[1], equal_to(0.))
    assert_that(round(results[2], 6), equal_to(-0.005373))

    # check that files are deleted in case of success and not in debug mode
    # it will fail in debug mode: useful to keep temporary files
    assert_that(osp.exists(osp.join(wrkdir, ".run_param0001")),
                equal_to(bool(debug_mode())))


@tempdir
def test_parametric_study2comm(tmpdir):
    """Test generator of parametric command file"""
    case = _setup_nominal(tmpdir)
    if case is None:
        return

    varnames = case.variables.keys()
    assert_that(varnames, contains("F", "E", "nu", "h"))

    stage = case[0]
    text = study2comm(stage, parametric=True)
    assert_that(text, contains_string("E = VARIABLE(NOM_PARA="))
    assert_that(text, contains_string("nu = VARIABLE(NOM_PARA="))
    assert_that(text, contains_string("F = VARIABLE(NOM_PARA="))
    assert_that(text, contains_string("h = VARIABLE(NOM_PARA="))

@tempdir
def test_export_parametric(tmpdir):
    case = _setup_nominal(tmpdir)
    if case is None:
        return

    export_name = osp.join(tmpdir, "parametric.export")
    export = ExportCase.factory(case, export_name, parametric=True)
    files = export.get_input_files()
    assert_that(files, has_length(0))

    params = {'server': 'remote', 'memory': 4096, 'time': '1:00:00',
              'mpicpu': 'x'}
    export.set_parameters(params)
    export.generate()
    files = export.get_input_files()
    assert_that(files, has_length(5))

    with open(export_name) as fexp:
        content = fexp.read()

    assert_that(content, contains_string("server remote"))
    assert_that(content, contains_string("memory_limit 4096"))
    assert_that(content, contains_string("time_limit 3600"))

@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def test_parametric_generator(tmpdir):
    case = _setup_nominal(tmpdir)
    if case is None:
        return

    assert_that(case, has_length(3))

    # add a previous execution
    engine = Engine.Salome
    rc1 = case.model.create_run_case(name='fake')
    result = rc1.results()[2]
    runner = runner_factory(engine, case=rc1, unittest=True)
    params = _parameters(engine)
    params['memory'] = 1234
    runner.start(params)
    monitor_refresh(runner, estimated_time=10.)
    assert_that(runner.result_state(result) & SO.Success)

    _setup_and_check_ot(case, tmpdir, mem_limit=1234)

@tempdir
def test_parametric_generator_wo_run(tmpdir):
    case = _setup_nominal(tmpdir)
    if case is None:
        return

    assert_that(case, has_length(3))

    _setup_and_check_ot(case, tmpdir, run=False)

@tempdir
def test_parametric_coverage(tmpdir):
    # for coverage
    with open(osp.join(tmpdir, "parametric.export"), "w") as fexp:
        fexp.write("P mpi_nbcpu 1\nP mpi_nbnoeud 1\nP ncpus 1\n")
    calc = ParametricCalculation(tmpdir, ["x0"], [1.0, 2.0])
    calc.setup()
    calc._rcname = None
    name = calc.run_case_name()
    assert_that(name, equal_to(".run_param_1.0_2.0"))
    calc.runcdir = osp.join(calc.basedir, calc.run_case_name())

    # test for long paths
    n = 26
    calc = ParametricCalculation(tmpdir,
                                 ["x{0}".format(i) for i in range(n)],
                                 [random.random() for _ in range(n)])
    assert_that(calc.runcdir, has_length(255))

    calc.set_logger(lambda _x: None)
    calc.read_output_file()
    assert_that(calc.output_values(), has_length(0))


@tempdir
def test_direct_runner(tmpdir):
    case = _setup_nominal(tmpdir)
    if case is None:
        return

    assert_that(case, has_length(3))

    engine = Engine.Direct
    rc1 = case.model.create_run_case(name='fake')
    expected_results = rc1.results()
    assert_that(expected_results, has_length(3))

    runner = runner_factory(engine, case=rc1, unittest=True)
    params = _parameters(engine)
    runner.start(params)

    assert_that(runner.is_started(), equal_to(True))
    assert_that(runner.is_finished(), equal_to(True))
    assert_that(runner.result_state(expected_results[0]) & SO.Success)
    assert_that(runner.result_state(expected_results[1]) & SO.Success)
    assert_that(runner.result_state(expected_results[2]) & SO.Success)


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
