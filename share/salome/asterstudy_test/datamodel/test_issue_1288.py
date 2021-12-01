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

"""Test case for issue #1288"""


import unittest
from hamcrest import *
from testutils import attr

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study

#------------------------------------------------------------------------------
@attr('fixit')
def test_validity_status():
    #--------------------------------------------------------------------------
    text = \
"""
MAIL = LIRE_MAILLAGE(FORMAT='MED', NOM_MED='MeshCoude', UNITE=20)

MAIL = MODI_MAILLAGE(
    reuse=MAIL, MAILLAGE=MAIL, ORIE_PEAU_3D=_F(GROUP_MA=('SURFINT', ))
)

MODTH = AFFE_MODELE(
    AFFE=_F(MODELISATION=('3D', ), PHENOMENE='THERMIQUE', TOUT='OUI'),
    MAILLAGE=MAIL
)

MATER = DEFI_MATERIAU(
    ELAS=_F(ALPHA=1.096e-05, E=2.04e+11, NU=0.3),
    THER=_F(LAMBDA=54.6, RHO_CP=3710000.0)
)

CHMATER = AFFE_MATERIAU(AFFE=_F(MATER=(MATER, ), TOUT='OUI'), MAILLAGE=MAIL)

F_TEMP = DEFI_FONCTION(NOM_PARA='INST', VALE=(0.0, 20.0, 10.0, 70.0))

LINST = DEFI_LIST_REEL(VALE=(0.0, 5.0, 10.0))

F_MULT = DEFI_FONCTION(NOM_PARA='INST', VALE=(0.0, 1.0, 10.0, 1.0))

CHARTH = AFFE_CHAR_THER_F(
    MODELE=MODTH, TEMP_IMPO=_F(GROUP_MA=('SURFINT', ), TEMP=F_TEMP)
)

TEMPE = THER_LINEAIRE(
    CHAM_MATER=CHMATER,
    ETAT_INIT=_F(VALE=20.0),
    EXCIT=_F(CHARGE=CHARTH, FONC_MULT=F_MULT),
    INCREMENT=_F(LIST_INST=LINST),
    MODELE=MODTH
)

IMPR_RESU(FORMAT='MED', RESU=_F(RESULTAT=TEMPE), UNITE=80)
"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    assert_that(stage.check(), equal_to(Validity.Nothing))

    c0 = stage["MODTH"]
    c1 = stage["CHARTH"]
    c2 = stage["TEMPE"]
    assert_that(c1.check(), equal_to(Validity.Nothing))
    assert_that(c2.check(), equal_to(Validity.Nothing))

    c1.init({'MODELE':c0})

    assert_that(c1.check(), is_not(equal_to(Validity.Syntaxic)))
    assert_that(c2.check(), is_not(equal_to(Validity.Syntaxic)))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
