# coding=utf-8

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

"""Implementation of the automatic tests for history."""


import unittest
from hamcrest import *

from testutils import attr
from asterstudy.common import CFG

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.catalogs import CATA

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def test():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    import os
    stagefile = os.path.join(os.getenv('ASTERSTUDYDIR'),
                             'data', 'comm2study', 'zzzz289f.comm')

    stage = case.import_stage(stagefile)
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(case.check(), equal_to(Validity.Nothing))

    stage.use_text_mode()
    assert_that(stage.is_text_mode(), equal_to(True))

    from tempfile import mkstemp
    studyfile = mkstemp(prefix='asterstudy' + '-', suffix='ast')[1]

    try:
        History.save(history, studyfile)
        history2 = History.load(studyfile)

        case2 = history2.current_case
        stage2 = case2['zzzz289f']

        assert_that(stage2.is_text_mode(), equal_to(True))

        stage2.use_graphical_mode()
        assert_that(case2.check(), equal_to(Validity.Nothing))
        assert_that(stage2.is_graphical_mode(), equal_to(True))

    finally:
        os.remove(studyfile)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
