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

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History

from asterstudy.datamodel.comm2study import comm2study
from testutils.tools import check_export

#------------------------------------------------------------------------------
def test():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage1 = case.create_stage(':1:')

    text1 = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE()

M = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
    ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)

CHM = AFFE_MATERIAU(AFFE=_F(MATER=M, TOUT='OUI'), MAILLAGE=MAIL_Q)
"""

    assert_that(stage1, has_length(0))
    stage1.use_text_mode()
    stage1.set_text(text1)

    stage1.use_graphical_mode()
    assert_that(stage1, has_length(4))

    #--------------------------------------------------------------------------
    stage2 = case.create_stage(':2:')

    text2 = \
"""
MODELUPG = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MATR = CALC_MATR_ELEM(CHAM_MATER=CHM, MODELE=MODELUPG, OPTION='MASS_MECA')

FIN()
"""
    stage2.use_text_mode()
    stage2.set_text(text2)

    stage2.use_graphical_mode()
    assert_that(stage2, has_length(3))

    assert_that(case.check(), equal_to(Validity.Nothing))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
