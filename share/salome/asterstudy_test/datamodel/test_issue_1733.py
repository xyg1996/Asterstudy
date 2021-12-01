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

"""Automatic tests for the issue 1733 (Problem with searcher)."""


import unittest
from hamcrest import *
from testutils import attr

from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study

from asterstudy.gui.datasettings.model import Model, match_keyword

#------------------------------------------------------------------------------
def translate_command(command, keyword):
    return command

Model.translate_command = staticmethod(translate_command)

#------------------------------------------------------------------------------
def test_searcher():
    #--------------------------------------------------------------------------
    # from file "data/comm2study/szlz108b.comm"
    text = \
"""
DEBUT( CODE=_F(NIV_PUB_WEB='INTERNET'),DEBUG=_F(SDVERI='OUI'))

TAUN1=DEFI_FONCTION(   NOM_PARA='INST',
                         VALE=(   0.,           1.,
                                  1.,           1.,
                                  2.,           1.,
                                  3.,           1,

                                    ) )
"""

    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    command = stage.commands[0] # DEBUT
    keyword = "tab"

    state = match_keyword(command, keyword)

    assert_that(state, equal_to(False))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
