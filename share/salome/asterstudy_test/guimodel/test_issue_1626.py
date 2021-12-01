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

"""Automatic tests for the issue 1626
(Properly arrange concepts produced by macro-command)."""


import unittest

import testutils.gui_utils
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.history import History
from asterstudy.gui import HistoryProxy
from asterstudy.gui.datasettings import create_data_settings_model
from common_test_gui import HistoryHolder
from hamcrest import *


def test_macro_commands():
    """Test for macro-commands"""

    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),DEBUG=_F(SDVERI='OUI'))

MAIL=LIRE_MAILLAGE(FORMAT='MED',);

MODELE=AFFE_MODELE(MAILLAGE=MAIL,
                   AFFE=_F(TOUT='OUI',
                           PHENOMENE='MECANIQUE',
                           MODELISATION='3D',),);

MAT=DEFI_MATERIAU(ELAS=_F(E=204000000000.0,
                          NU=0.3,
                          RHO=7800.0,),);

CHMAT=AFFE_MATERIAU(MAILLAGE=MAIL,
                    AFFE=_F(TOUT='OUI',
                            MATER=MAT,),);

BLOCAGE=AFFE_CHAR_MECA(MODELE=MODELE,
                       DDL_IMPO=_F(GROUP_MA='BASE',
                                   DX=0.0,
                                   DY=0.0,
                                   DZ=0.0,),);

ASSEMBLAGE(MODELE=MODELE,
                CHAM_MATER=CHMAT,
                CHARGE=BLOCAGE,
                NUME_DDL=CO('NUMEDDL'),
                MATR_ASSE=(_F(MATRICE=CO('RIGIDITE'),
                              OPTION='RIGI_MECA',),
                           _F(MATRICE=CO('MASSE'),
                              OPTION='MASS_MECA',),),);

MODES=CALC_MODES(MATR_RIGI=RIGIDITE,
                 OPTION='PLUS_PETITE',
                 CALC_FREQ=_F(NMAX_FREQ=10,
                              ),
                 MATR_MASS=MASSE,
                 )

IMPR_RESU(FORMAT='MED',
          RESU=_F(MAILLAGE=MAIL,
                  RESULTAT=MODES,
                  NOM_CHAM='DEPL',),);

FIN();
"""

    history = History()
    stage = history.current_case.create_stage('Stage')

    comm2study(text, stage)

    cmodel = create_data_settings_model(HistoryHolder(history))
    cmodel.update()

    categories = cmodel.get_stage_children(stage)

    category_pre_analysis = categories[5]
    assert_that(category_pre_analysis.name, equal_to('Pre Analysis'))

    command_assemblage = category_pre_analysis.child_nodes[0]
    assert_that(command_assemblage.name, equal_to('_'))
    assert_that(command_assemblage.title, equal_to('ASSEMBLAGE'))

    command_numeddl = command_assemblage.child_nodes[0]
    assert_that(command_numeddl.name, equal_to('NUMEDDL'))
    assert_that(command_numeddl.title, equal_to('_RESULT_OF_MACRO'))

    command_rigidite = command_assemblage.child_nodes[1]
    assert_that(command_rigidite.name, equal_to('RIGIDITE'))
    assert_that(command_rigidite.title, equal_to('_RESULT_OF_MACRO'))

    command_masse = command_assemblage.child_nodes[2]
    assert_that(command_masse.name, equal_to('MASSE'))
    assert_that(command_masse.title, equal_to('_RESULT_OF_MACRO'))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
