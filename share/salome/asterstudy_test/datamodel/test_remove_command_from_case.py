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
    stage0 = case.create_stage(':0:')

    text0 = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE()
"""

    comm2study(text0, stage0)
    assert_that(stage0, has_length(2))

    #--------------------------------------------------------------------------
    stage1 = case.create_stage(':1:')

    text1 = \
"""
MATER = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
    ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER, TOUT='OUI'), MAILLAGE=MAIL_Q)
"""

    comm2study(text1, stage1)
    assert_that(stage1, has_length(2))

    #--------------------------------------------------------------------------
    stage2 = case.create_stage(':2:')

    text2 = \
"""
MODELUPG = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MODELUPQ = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MODELUPL = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UP', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=MAIL_Q
)

MATMUPG = CALC_MATR_ELEM(
    CHAM_MATER=CHMAT_Q, MODELE=MODELUPG, OPTION='MASS_MECA'
)

FIN()
"""
    comm2study(text2, stage2)
    assert_that(stage2, has_length(5))

    #--------------------------------------------------------------------------
    assert_that(stage2['MODELUPG'].check(), equal_to(Validity.Nothing))

    assert_that(stage0.check(), equal_to(Validity.Nothing))
    assert_that(stage1.check(), equal_to(Validity.Nothing))
    assert_that(stage2.check(), equal_to(Validity.Nothing))
    assert_that(case.check(), equal_to(Validity.Nothing))

    #--------------------------------------------------------------------------
    del stage0['MAIL_Q']

    text0 = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))
"""

    assert(check_export(stage0, text0, validity=False))

    text1 = \
"""
MATER = DEFI_MATERIAU(ECRO_LINE=_F(D_SIGM_EPSI=-1950.0,
                                   SY=3.0),
                      ELAS=_F(E=30000.0,
                              NU=0.2,
                              RHO=2764.0))

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER,
                                TOUT='OUI'),
                        MAILLAGE=MAIL_Q)
"""

    assert(check_export(stage1, text1, validity=False))

    text2 = \
"""
MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)

MODELUPQ = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)

MODELUPL = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UP',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)

MATMUPG = CALC_MATR_ELEM(CHAM_MATER=CHMAT_Q,
                         MODELE=MODELUPG,
                         OPTION='MASS_MECA')

FIN()
"""
    assert(check_export(stage2, text2, validity=False))

    # dependencies are still ok (because removed) but syntactically invalid
    assert_that(stage2['MODELUPG'].check(), equal_to(Validity.Dependency))

    assert_that(stage0.check(), equal_to(Validity.Nothing))
    assert_that(stage1.check(), equal_to(Validity.Dependency))
    assert_that(stage2.check(), equal_to(Validity.Dependency))
    assert_that(case.check(), equal_to(Validity.Dependency))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
