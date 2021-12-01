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

from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study

from asterstudy.gui.datasettings.model import match_concept

#------------------------------------------------------------------------------
def _match_state(text, command_states, pattern):
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(":memory:")

    comm2study(text, stage)

    for command_name, expected_state in command_states.items():
        command = stage[command_name]
        storage = command.storage_nocopy
        state = match_concept(command, pattern)
        assert_that(state, equal_to(expected_state))

#------------------------------------------------------------------------------
def test_match_state_1():
    #--------------------------------------------------------------------------
    # from file "data/comm2study/szlz106a.comm"
    text = \
"""
MAT0=DEFI_MATERIAU(   FATIGUE=_F(  A_BASQUIN = 1.001730939E-14,
                                  BETA_BASQUIN = 4.065)  )

TAB1=POST_FATI_ALEA(    MOMENT_SPEC_0=182.5984664,
                          MOMENT_SPEC_2=96098024.76,
                               COMPTAGE='NIVEAU',
                                  DUREE=1.,
                                DOMMAGE='WOHLER',
                                  MATER=MAT0          )
"""
    #--------------------------------------------------------------------------
    pattern = "MAT0"
    command_states = {
        "MAT0": True,
        "TAB1": True
        }
    _match_state(text, command_states, pattern)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_match_state_2():
    #--------------------------------------------------------------------------
    # from file "data/comm2study/szlz108b.comm"
    text = \
"""
TAUN1=DEFI_FONCTION(   NOM_PARA='INST',
                         VALE=(   0.,           1.,
                                  1.,           1.,
                                  2.,           1.,
                                  3.,           1,

                                    ) )

F_EPS=DEFI_FONCTION(       NOM_PARA='SIGM',
                           PROL_DROITE='LINEAIRE',
                          PROL_GAUCHE='LINEAIRE',
                                 VALE=(    0.,    0.,
                                        1000.,   10.,   ),
                                TITRE='FONCTION DE TAHERI'  )

F_EPSMAX=DEFI_NAPPE(          NOM_PARA='X',
                               PROL_DROITE='LINEAIRE',
                              PROL_GAUCHE='LINEAIRE',
                                     PARA=(  0.5,   1., ),
                            NOM_PARA_FONC='EPSI',DEFI_FONCTION=(
                            _F(  PROL_DROITE = 'LINEAIRE',
                                            PROL_GAUCHE = 'LINEAIRE',
                                            VALE = (  0.,   25.,
                                                            10.,  525., )),
                                          _F(  PROL_DROITE = 'LINEAIRE',
                                            PROL_GAUCHE = 'LINEAIRE',
                                            VALE = ( 0.,    50.,
                                                           10.,   550., ))),
                                   TITRE='NAPPE DE TAHERI' )

F_MANSON=DEFI_FONCTION(      NOM_PARA='EPSI',
                              PROL_DROITE='LINEAIRE',
                             PROL_GAUCHE='LINEAIRE',
                                    VALE=(       0.,   200000.,
                                                 2.,        0.,    ),
                                   TITRE='FONCTION DE MANSON_COFFIN')

F_WOHLER=DEFI_FONCTION(      NOM_PARA='SIGM',
                              PROL_DROITE='LINEAIRE',
                             PROL_GAUCHE='LINEAIRE',
                                    VALE=(
                                                  0.,   200000.,
                                                200.,        0.,
                                         ),
                                   TITRE='FONCTION DE WOHLER')

MAT0=DEFI_MATERIAU(
          FATIGUE=_F(   WOHLER = F_WOHLER,
                     MANSON_COFFIN = F_MANSON) )

TAB_1=POST_FATIGUE(        CHARGEMENT='UNIAXIAL',
                             HISTOIRE=_F(  EPSI = TAUN1),
                             COMPTAGE='RAINFLOW',
                              DOMMAGE='TAHERI_MANSON',
                          TAHERI_FONC=F_EPS,
                         TAHERI_NAPPE=F_EPSMAX,
                                MATER=MAT0,
                                CUMUL='LINEAIRE',
                                 INFO=2                   )
"""
    #--------------------------------------------------------------------------
    pattern = "TAUN1"
    command_states = {
        "TAUN1": True,
        "F_EPS": False,
        "F_EPSMAX": False,
        "F_MANSON": False,
        "F_WOHLER": False,
        "MAT0": False,
        "TAB_1": True
        }
    _match_state(text, command_states, pattern)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_issue_1809():
    #--------------------------------------------------------------------------
    text = \
"""
MAIL = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)

MODE = AFFE_MODELE(AFFE=_F(MODELISATION='C_PLAN',
                           PHENOMENE='MECANIQUE',
                           TOUT='OUI'),
                   MAILLAGE=MAIL)

MATE1 = DEFI_MATERIAU(ELAS=_F(E=200000.0,
                              NU=0.3))

MATE = AFFE_MATERIAU(AFFE=_F(MATER=(MATE1, MATE1),
                             TOUT='OUI'),
                     MAILLAGE=MAIL)
"""
    #--------------------------------------------------------------------------
    pattern = "MATE1"
    command_states = {
        "MAIL": False,
        "MODE": False,
        "MATE1": True,
        "MATE": True
        }
    _match_state(text, command_states, pattern)

    #--------------------------------------------------------------------------
    pass

def test_issue_1849():
    #--------------------------------------------------------------------------
    text = \
"""
MAIL = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)

MODELE = AFFE_MODELE(AFFE=_F(MODELISATION='3D',
                             PHENOMENE='MECANIQUE',
                             TOUT='OUI'),
                     MAILLAGE=MAIL)

MAT = DEFI_MATERIAU(ELAS=_F(E=2.04e+11,
                            NU=0.3,
                            RHO=7800.0))

CHMAT = AFFE_MATERIAU(AFFE=_F(MATER=MAT,
                              TOUT='OUI'),
                      MAILLAGE=MAIL)

BLOCAGE = AFFE_CHAR_MECA(DDL_IMPO=_F(DX=0.0,
                                     DY=0.0,
                                     DZ=0.0,
                                     GROUP_MA='BASE'),
                         MODELE=MODELE)

ASSEMBLAGE(CHAM_MATER=CHMAT,
           CHARGE=BLOCAGE,
           MATR_ASSE=(_F(MATRICE=CO('RIGIDITE'),
                         OPTION='RIGI_MECA'),
                      _F(MATRICE=CO('MASSE'),
                         OPTION='MASS_MECA')),
           MODELE=MODELE,
           NUME_DDL=CO('NUMEDDL'))

MODES = CALC_MODES(CALC_FREQ=_F(NMAX_FREQ=10),
                   MATR_MASS=MASSE,
                   MATR_RIGI=RIGIDITE,
                   OPTION='PLUS_PETITE')
"""
    #--------------------------------------------------------------------------
    pattern = "RIGID"
    command_states = {
        "MAIL": False,
        "MODELE": False,
        "MAT": False,
        "CHMAT": False,
        "BLOCAGE": False,
        "_": True,                # for ASSEMBLAGE which is unnamed command!
        "RIGIDITE": True,
        "MASSE": False,
        "NUMEDDL": False,
        "MODES": True,
        }
    _match_state(text, command_states, pattern)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
