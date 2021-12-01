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

"""Bug #1226 - Persistence fails for LIRE_MAILLAGE case"""


import unittest
from hamcrest import *
from testutils import attr

from asterstudy.datamodel.history import History

#------------------------------------------------------------------------------
@attr('fixit')
def test():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage()

    #--------------------------------------------------------------------------
    stage.add_command('LIRE_MAILLAGE')

    #--------------------------------------------------------------------------
    from tempfile import mkstemp
    an_outfile = mkstemp(prefix='asterstudy' + '-', suffix='.ajs')[1]

    History.save(history, an_outfile)
    history2 = History.load(an_outfile)

    assert_that(history.current_case[0][0].keys(), empty())
    assert_that(history.current_case[0][0]['UNITE'].value, none())
    assert_that(history2.current_case[0][0]['UNITE'], equal_to(20))

    assert_that(history * history2, none())

    import os
    os.remove(an_outfile)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
