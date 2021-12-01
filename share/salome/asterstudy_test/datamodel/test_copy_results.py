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


import os.path as osp
import unittest

from asterstudy.datamodel import History, comm2study
from asterstudy.datamodel.engine import Engine, runner_factory
from asterstudy.datamodel.engine.salome_runner import has_salome
from asterstudy.datamodel.result import StateOptions as SO
from engine_testcases import _parameters, monitor_refresh
from hamcrest import *
from testutils import attr, tempdir


@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def test_results(tmpdir):
    history = History()
    history.folder = tmpdir

    text1 = """
cste = DEFI_CONSTANTE(VALE=1.0)

IMPR_FONCTION(COURBE=_F(FONCTION=cste),
              FORMAT='TABLEAU',
              UNITE=8)
"""
    text2 = """
other = DEFI_CONSTANTE(VALE=2.0)
"""
    case = history.current_case
    stg1 = case.create_stage('stg1')
    comm2study(text1, stg1)
    info = stg1.handle2info[8]
    info.filename = osp.join(tmpdir, 'cste.txt')
    assert_that(osp.isfile(osp.join(tmpdir, 'cste.txt')), equal_to(False))

    stg2 = case.create_stage('stg2')
    comm2study(text2, stg2)

    runcase = history.create_run_case(name='rc2')

    expected_results = runcase.results()
    assert_that(expected_results, has_length(2))

    runner = runner_factory(Engine.Salome, case=case)

    params = _parameters(Engine.Salome)
    runner.start(params)
    monitor_refresh(runner, estimated_time=5.)

    assert_that(osp.isfile(osp.join(tmpdir, 'cste.txt')), equal_to(True))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
