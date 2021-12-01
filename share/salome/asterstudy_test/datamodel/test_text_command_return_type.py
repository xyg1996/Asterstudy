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

"""Miscellaneous test cases"""


import unittest
from hamcrest import *
from testutils import attr

from asterstudy.datamodel.history import History

#------------------------------------------------------------------------------
def test():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE()

MATER = DEFI_MATERIAU(
     ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
     ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER, TOUT='OUI'), MAILLAGE=MAIL_Q) """

    stage = case.text2stage(text)

    assert_that(stage.is_graphical_mode(), equal_to(True))

    command = stage[0]
    assert_that(command.type, none())

    command = stage['MAIL_Q']
    assert_that(command.type, not_none())

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
