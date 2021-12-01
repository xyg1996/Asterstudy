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
zzzz289f = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE()

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

MATER = DEFI_MATERIAU(ECRO_LINE=_F(D_SIGM_EPSI=-1950.0,
                                   SY=3.0),
                      ELAS=_F(E=30000.0,
                              NU=0.2,
                              RHO=2764.0))

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER,
                                TOUT='OUI'),
                        MAILLAGE=MAIL_Q)

MATMUPG = CALC_MATR_ELEM(CHAM_MATER=CHMAT_Q,
                         MODELE=MODELUPG,
                         OPTION='MASS_MECA')

FIN()
"""
#------------------------------------------------------------------------------

def test():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comm2study(zzzz289f, stage)

    assert_that(stage, has_length(9))

    assert_that(stage['MODELUPG'].check(), equal_to(Validity.Nothing))

    #--------------------------------------------------------------------------
    del stage['MAIL_Q']

    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

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

MATER = DEFI_MATERIAU(ECRO_LINE=_F(D_SIGM_EPSI=-1950.0,
                                   SY=3.0),
                      ELAS=_F(E=30000.0,
                              NU=0.2,
                              RHO=2764.0))

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER,
                                TOUT='OUI'),
                        MAILLAGE=MAIL_Q)

MATMUPG = CALC_MATR_ELEM(CHAM_MATER=CHMAT_Q,
                         MODELE=MODELUPG,
                         OPTION='MASS_MECA')

FIN()
"""
    assert(check_export(stage, text, validity=False))

    # dependencies are ko, MAIL_Q is missing
    assert_that(stage['CHMAT_Q'].check(), equal_to(Validity.Dependency))
    assert_that(stage['MODELUPG'].check(), equal_to(Validity.Dependency))
    assert_that(stage['MATMUPG'].check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_895_duplicate():
    """Batch mode for tst_redmine_895_duplicate"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comm2study(zzzz289f, stage)

    assert_that(stage, has_length(9))
    assert_that(stage.check(), equal_to(Validity.Nothing))

    del stage['MAIL_Q']

    assert_that(stage['CHMAT_Q'].check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

    # can not be repaired
    assert_that(case.repair(), equal_to(Validity.Dependency))

    newmesh = stage('LIRE_MAILLAGE', 'MAIL_Q')
    assert_that(stage['MAIL_Q'].check(), equal_to(Validity.Nothing))

    # dependencies are ko, original MAIL_Q is missing
    assert_that(stage['CHMAT_Q'].check(), equal_to(Validity.Dependency))
    assert_that(stage['MODELUPG'].check(), equal_to(Validity.Dependency))
    assert_that(stage['MATMUPG'].check(), equal_to(Validity.Dependency))
    assert_that(stage.check(), equal_to(Validity.Dependency))

    stage['CHMAT_Q'].reset_validity()
    assert_that(stage['CHMAT_Q'].check(), equal_to(Validity.Dependency))

    # invalid but the export "repairs" the study!
    assert(check_export(stage, zzzz289f, validity=False, sort=True))

    assert_that(stage['CHMAT_Q'].check(), equal_to(Validity.Dependency))

    # repair the case
    assert_that(case.repair(), equal_to(Validity.Nothing))

    assert(check_export(stage, zzzz289f, sort=True))


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
