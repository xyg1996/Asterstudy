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

"""Automatic tests for export feature."""


import unittest
from hamcrest import *

import os
import os.path as osp

from testutils import attr

from asterstudy.common import CFG

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study

from testutils.tools import check_export, check_import, check_translation


def test():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    command = stage.add_command('DEBUT')

    command = stage.add_command('LIRE_MAILLAGE', 'mesh')
    command['UNITE'] = 11

    command = stage.add_command('MODI_MAILLAGE', 'mesh')
    command['MAILLAGE'] = stage['mesh']

    factor = command['ORIE_PEAU_3D']
    factor['GROUP_MA'] = 'group'

    assert_that(command.need_reuse(), equal_to(True))

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT()

mesh = LIRE_MAILLAGE(UNITE=11)

mesh = MODI_MAILLAGE(reuse=mesh,
                     MAILLAGE=mesh,
                     ORIE_PEAU_3D=_F(GROUP_MA='group'))
"""
    import pickle
    blob = pickle.dumps(history)
    history2 = pickle.loads(blob)

    case = history2.current_case
    stage2 = case[':memory:']

    assert(check_import(text))
    assert(check_translation(stage, text))


def test_reuse_condition():
    """Test for usage of reuse in conditions"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comm = osp.join(os.getenv('ASTERSTUDYDIR'),
                    'data', 'comm2study', 'zzzz191a.comm')
    with open(comm, "rb") as commfile:
        text = commfile.read()

    comm2study(text, stage)
    assert_that(stage.check(), equal_to(Validity.Nothing))


def test_meca_statique():
    text = \
"""
MO = modele_sdaster()

CLIM = char_meca()

RESUSTA=MECA_STATIQUE(MODELE=MO,
                      EXCIT=_F(CHARGE=CLIM,),);

RESUSTA=MECA_STATIQUE(reuse =RESUSTA,
                      MODELE=MO,
                      EXCIT=_F(CHARGE=CLIM,),);
"""
    history = History()
    case = history.current_case
    stage = case.create_stage('part1')
    comm2study(text, stage)
    assert_that(stage[2].name, equal_to('RESUSTA'))
    assert_that('RESULTAT', not_(is_in(stage[2].storage)))
    assert_that(stage[3].name, equal_to('RESUSTA'))
    assert_that('RESULTAT', is_in(stage[3].storage))

def test_macr_elem_stat():
    text = \
"""
model = modele_sdaster()

S_1 = MACR_ELEM_STAT(
    DEFINITION=_F(MODELE=model),
    EXTERIEUR=_F(GROUP_NO=('GRNM13', ), NOEUD=('N1', 'N4', 'N7', 'N10'))
)

S_1 = MACR_ELEM_STAT(
    reuse=S_1,
    CAS_CHARGE=_F(NOM_CAS='CHF1'),
    RIGI_MECA=_F()
)
"""
    history = History()
    case = history.current_case
    stage = case.create_stage('part1')
    comm2study(text, stage)
    assert_that(stage[1].name, equal_to('S_1'))
    assert_that('MACR_ELEM', not_(is_in(stage[1].storage)))
    assert_that(stage[2].name, equal_to('S_1'))
    assert_that('MACR_ELEM', is_in(stage[2].storage))


def test_macro_elas_mult():
    text = \
"""
model = modele_sdaster()

charg1 = char_meca()

statique=MACRO_ELAS_MULT(MODELE=model,
                         CAS_CHARGE=_F(NOM_CAS = 'CHARGE NUMERO 1',
                                       CHAR_MECA = charg1,),)

statique=MACRO_ELAS_MULT(reuse=statique,
                         MODELE=model,
                         CAS_CHARGE=_F(NOM_CAS = 'CHARGE NUMERO 2',
                                        CHAR_MECA = charg1,),)
"""
    history = History()
    case = history.current_case
    stage = case.create_stage('part1')
    comm2study(text, stage)
    assert_that(stage[2].name, equal_to('statique'))
    assert_that('RESULTAT', not_(is_in(stage[2].storage)))
    assert_that(stage[3].name, equal_to('statique'))
    assert_that('RESULTAT', is_in(stage[3].storage))


def test_defi_domaine_reduit():
    text = \
"""
mesh = maillage_sdaster()

base_p = mode_empi()

base_d = mode_empi()

mesh = DEFI_DOMAINE_REDUIT(
    reuse=mesh,
    BASE_DUAL=base_d,
    BASE_PRIMAL=base_p,
    NOM_DOMAINE='RID',
    NOM_INTERFACE='INF'
)
"""
    history = History()
    case = history.current_case
    stage = case.create_stage('part1')
    comm2study(text, stage)
    assert_that('MAILLAGE', is_in(stage['mesh'].storage))


def test_crea_resu():
    text = \
"""
MOTHER = modele_sdaster()

TEMPE = evol_ther()

CHTEMP0 = CREA_CHAMP(
    AFFE=_F(NOM_CMP='TEMP', TOUT='OUI', VALE=0.0),
    MODELE=MOTHER,
    OPERATION='AFFE',
    TYPE_CHAM='NOEU_TEMP_R'
)

TEMPE = CREA_RESU(
    reuse=TEMPE,
    AFFE=_F(CHAM_GD=CHTEMP0, INST=-1.0),
    NOM_CHAM='TEMP',
    OPERATION='AFFE',
    TYPE_RESU='EVOL_THER'
)
"""
    history = History()
    case = history.current_case
    stage = case.create_stage('part1')
    comm2study(text, stage)
    assert_that('RESULTAT', not_(is_in(stage['CHTEMP0'].storage)))
    assert_that('RESULTAT', is_in(stage['TEMPE'].storage))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
