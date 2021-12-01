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

"""Automatic tests for export feature."""


import os
import unittest
from hamcrest import *

from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.general import ConversionLevel
from asterstudy.datamodel.history import History


def test_26683():
    """Test for issue26683: """
    history = History()
    case = history.current_case
    stage0 = case.create_stage('test_26683')

    commfile = os.path.join(os.getenv('ASTERSTUDYDIR'),
                            'data', 'export', 'traction_aggregats_direct.comm')
    with open(commfile, "rb") as file:
        text = file.read()

    strict = ConversionLevel.Any | ConversionLevel.Partial
    comm2study(text, stage0, strict)
    assert_that(case, has_length(2))

    # first run
    run1 = history.create_run_case(reusable_stages=[0, 1])

    stage1 = history.current_case[1]
    text1 = "POURSUITE(PAR_LOT='NON')\n\n" + stage1.get_text()
    stage1.set_text(text1)
    # run2 needs copy of the second stage
    run2 = history.create_run_case(reusable_stages=[0, 1])


def test_nonetype():
    """Test for sd_prod returning NoneType"""
    from asterstudy.datamodel.undo_redo import UndoRedo

    history = History()
    undo = UndoRedo(history)
    case = history.current_case
    stage = case.create_stage(':mem:')
    cmd = stage('CALC_CHAMP')
    assert_that(calling(cmd.gettype), raises(TypeError))
    undo.commit()


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
