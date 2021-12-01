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

"""Automatic tests for general services."""


import os
import unittest
from hamcrest import *

from asterstudy.common import CFG
from testutils import attr

from asterstudy.datamodel.history import History
from asterstudy.datamodel.result import RunOptions, StateOptions

from asterstudy.datamodel.comm2study import comm2study

Skip = RunOptions.Skip
Reuse = RunOptions.Reuse
Execute = RunOptions.Execute

Waiting = StateOptions.Waiting
Success = StateOptions.Success

#------------------------------------------------------------------------------
def test():
    #--------------------------------------------------------------------------
    history = History()
    cc = history.current_case

    filename = os.path.join(os.getenv('ASTERSTUDYDIR'),
                            'data', 'comm2study', 'asterstudy01b.comm')
    assert_that(os.path.isfile(filename), equal_to(True))

    stage_name = os.path.basename(filename)
    assert_that(stage_name, equal_to('asterstudy01b.comm'))
    stage = cc.create_stage(stage_name)

    with open(filename) as file:
        comm2study(file.read(), stage)
    assert_that(stage.is_graphical_mode(), equal_to(True))

    assert_that(cc.run_options(stage), equal_to(Skip | Execute))

    #--------------------------------------------------------------------------
    assert_that(stage['Mesh']['MAILLAGE'].value, same_instance(stage[0]))

    #--------------------------------------------------------------------------
    rc1 = history.create_run_case().run()
    assert_that(rc1.name, equal_to('RunCase_1'))

    assert_that(stage['Mesh']['MAILLAGE'].value, same_instance(stage[0]))
    assert_that(rc1[stage_name]['Mesh']['MAILLAGE'].value, same_instance(rc1[stage_name][0]))

    #--------------------------------------------------------------------------
    rc2 = history.create_run_case().run()
    assert_that(rc2.name, equal_to('RunCase_2'))

    assert_that(stage['Mesh']['MAILLAGE'].value, same_instance(stage[0]))
    assert_that(rc2[stage_name]['Mesh']['MAILLAGE'].value, same_instance(rc2[stage_name][0]))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
    #--------------------------------------------------------------------------
    pass
