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

"""Automatic tests for API calculation objects."""


import os
import os.path as osp
import time
import unittest

from asterstudy.api import Calculation, FileAttr
from asterstudy.common import debug_mode
from asterstudy.datamodel.engine.salome_runner import has_salome
from asterstudy.datamodel.result import StateOptions as SO
from hamcrest import *
from testutils import attr, tempdir

text = """
IMPR_RESU(RESU=_F(RESULTAT=result),
          UNITE=2)

import os
assert os.path.exists('./REPE_IN/input_file')

DEFI_FICHIER(ACTION='ASSOCIER', UNITE=3, FICHIER='./REPE_OUT/output_file')
IMPR_TABLE(TABLE=table, UNITE=3)
"""


def exec_case(folder, server=None, version=None):
    src = osp.join(os.getenv("ASTERSTUDYDIR"), "data", "export")

    calc = Calculation(folder)
    calc.add_stage_from_file(osp.join(src, "zoom01.comm"))
    calc.add_stage_from_file(osp.join(src, "zoom03.comm"))
    calc.add_stage_from_file(osp.join(src, "zoom04.comm"))
    calc.add_stage_from_string(text)
    assert_that(calc.nb_stages, equal_to(4))

    calc.add_file(osp.join(src, "zoom00.med"), 20, FileAttr.In)
    calc.add_file(osp.join(src, "zoom80.txt"), 80, FileAttr.In)
    calc.add_file(osp.join(folder, "zoom_results.rmed"), 2, FileAttr.Out)

    in_dir = osp.join(folder, "repe.in")
    os.makedirs(in_dir)
    calc.set_input_dir(in_dir)
    with open(osp.join(in_dir, "input_file"), "w") as fobj:
        fobj.write("test")

    calc.set_output_dir(osp.join(folder, "repe.out"))

    if server:
        calc.set("server", server)
    if version:
        calc.set("version", version)

    calc.set("no_database", True)
    calc.set_logger(print if debug_mode() else lambda _: None)

    assert_that(calc.timeout, equal_to(4500)) # 5 * 15 min by default
    calc.set("time", 10)
    assert_that(calc.timeout, equal_to(50))
    calc.run()

    assert_that(calc.state, equal_to(SO.Success | SO.Warn))
    assert_that(calc.state_name, equal_to("Success+Warn"))

    logs = calc.logfiles()
    assert_that(logs, has_length(1))

    paths = calc.results_paths()
    assert_that(paths, has_length(1))
    assert_that(paths[0], equal_to(osp.join(folder, "zoom_results.rmed")))

    assert_that(osp.isfile(osp.join(folder, "repe.out", "output_file")))

    return calc


@unittest.skipIf(not has_salome(), "salome is required")
@tempdir
def test_api(tmpdir):
    calc = exec_case(tmpdir)
    # re-run
    calc.timeout = 0.001
    calc.run()
    time.sleep(1)
    assert_that(calc.state, equal_to(SO.Success | SO.Warn))
    assert_that(calc.is_successful(), equal_to(True))

    calc.delete_files()


@tempdir
def test_named_files(tmpdir):
    calc = Calculation(tmpdir)

    # checking errors
    assert_that(calc.state, equal_to(SO.Waiting))
    assert_that(calc.is_finished(), equal_to(False))
    assert_that(calling(calc.start), raises(AssertionError, "no stage"))

    calc.add_stage_from_string("")
    calc.add_file("/tmp/yyy", 88, FileAttr.In | FileAttr.Named)
    calc.add_file("/tmp/zzz", 0, FileAttr.Out)
    calc.timeout = "01:00:00"
    assert_that(calc.timeout, equal_to(3600))

    stg = calc._case[0]
    assert_that(stg.handle2info.keys(), contains_inanyorder("yyy", "zzz"))
    assert_that(stg.handle2info["yyy"].attr & (FileAttr.In | FileAttr.Named))
    assert_that(stg.handle2info["zzz"].attr & (FileAttr.Out | FileAttr.Named))


@tempdir
def test_refresh(tmpdir):
    calc = Calculation(tmpdir)
    calc.set("time", 10.)
    watch = calc._watcher

    watch._t_init = time.time()
    assert_that(watch._t_refr, none())
    assert_that(watch._do_refresh(), equal_to(True))
    watch._t_refr = time.time()
    assert_that(watch._do_refresh(), equal_to(False))
    time.sleep(3)
    assert_that(watch._do_refresh(), equal_to(True))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
