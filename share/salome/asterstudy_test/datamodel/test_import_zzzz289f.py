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


import os
import unittest

from hamcrest import *
from testutils import attr
from asterstudy.common import CFG

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.study2comm import study2comm

from testutils.tools import check_export, check_import

#------------------------------------------------------------------------------
def test():
    """Test for zzzz289f.comm"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    command = stage.add_command('DEBUT')

    command['CODE']['NIV_PUB_WEB'] = 'INTERNET'
    command['DEBUG']['SDVERI'] = 'OUI'

    #--------------------------------------------------------------------------
    command = stage.add_command('LIRE_MAILLAGE', 'MAIL_Q')
    command['UNITE'] = 22

    #--------------------------------------------------------------------------
    command = stage.add_command('AFFE_MODELE', 'MODELUPG')

    factor = command['AFFE']
    factor['MODELISATION'] = 'AXIS_INCO_UPG'
    factor['PHENOMENE'] = 'MECANIQUE'
    factor['TOUT'] = 'OUI'

    command['MAILLAGE'] = stage['MAIL_Q']

    #--------------------------------------------------------------------------
    command = stage.add_command('AFFE_MODELE', 'MODELUPQ')

    factor = command['AFFE']
    factor['MODELISATION'] = 'AXIS_INCO_UPG'
    factor['PHENOMENE'] = 'MECANIQUE'
    factor['TOUT'] = 'OUI'

    command['MAILLAGE'] = stage['MAIL_Q']

    #--------------------------------------------------------------------------
    command = stage.add_command('AFFE_MODELE', 'MODELUPL')

    factor = command['AFFE']
    factor['MODELISATION'] = 'AXIS_INCO_UP'
    factor['PHENOMENE'] = 'MECANIQUE'
    factor['TOUT'] = 'OUI'

    command['MAILLAGE'] = stage['MAIL_Q']

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_MATERIAU', 'MATER')

    factor = command['ECRO_LINE']
    factor['D_SIGM_EPSI'] = -1950.0
    factor['SY'] = 3.0

    factor = command['ELAS']
    factor['E'] = 30000.0
    factor['NU'] = 0.2
    factor['RHO'] = 2764.0

    #--------------------------------------------------------------------------
    command = stage.add_command('AFFE_MATERIAU', 'CHMAT_Q')

    sequence = command['AFFE']
    assert('MATER' in sequence.rkeys())

    sequence['MATER'] = stage['MATER']
    assert(sequence['MATER'].value == stage['MATER'])

    sequence['TOUT'] = 'OUI'

    command['MAILLAGE'] = stage['MAIL_Q']

    #--------------------------------------------------------------------------
    command = stage.add_command('CALC_MATR_ELEM', 'MATMUPG')

    command['CHAM_MATER'] = stage['CHMAT_Q']
    command['MODELE'] = stage['MODELUPG']
    command['OPTION'] = 'MASS_MECA'

    #--------------------------------------------------------------------------
    command = stage.add_command('FIN')

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE(UNITE=22)

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
    assert(check_export(stage, text))

    assert(check_import(text))

    #--------------------------------------------------------------------------
    pass


def test_zzzz289f():
    """Test for import/export zzzz289f"""
    comm = os.path.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'comm2study', 'zzzz289f.comm')

    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    with open(comm, 'rb') as file:
        text = file.read()
    comm2study(text, stage)

    from asterstudy.datamodel.catalogs import CATA

    # conversion from text keeps order of commands in the stage
    refs = ['MAIL_Q','MODELUPG', 'MODELUPQ', 'MODELUPL', 'MATER', 'CHMAT_Q',
            'MATMUPG', 'MATMUPQ', 'MATMUPL', 'MATRUPG', 'MATRUPQ', 'MATRUPL',
            'NUMEUPG', 'NUMEUPQ', 'NUMEUPL', 'MAMASUPG', 'MAMASUPQ',
            'MAMASUPL', 'MARASUPG', 'MARASUPQ', 'MARASUPL']
    cmds = stage.commands
    names = [i.name for i in cmds if i.name != "_"]
    assert_that(names, contains(*refs))

    titles = [i.title for i in cmds]
    refn = ['_CONVERT_COMMENT', 'DEBUT', 'LIRE_MAILLAGE', 'AFFE_MODELE',
            'AFFE_MODELE', 'AFFE_MODELE','DEFI_MATERIAU','AFFE_MATERIAU',
            '_CONVERT_COMMENT', 'CALC_MATR_ELEM', '_CONVERT_COMMENT',
            'CALC_MATR_ELEM', '_CONVERT_COMMENT', 'CALC_MATR_ELEM',
            '_CONVERT_COMMENT', 'CALC_MATR_ELEM', '_CONVERT_COMMENT',
            'CALC_MATR_ELEM', '_CONVERT_COMMENT', 'CALC_MATR_ELEM', 'NUME_DDL',
            'NUME_DDL', 'NUME_DDL', 'ASSE_MATRICE', 'ASSE_MATRICE',
            'ASSE_MATRICE', '_CONVERT_COMMENT', 'ASSE_MATRICE',
            '_CONVERT_COMMENT', 'ASSE_MATRICE', '_CONVERT_COMMENT',
            'ASSE_MATRICE', '_CONVERT_COMMENT', 'TEST_RESU', 'TEST_RESU',
            'TEST_RESU', 'TEST_RESU', 'TEST_RESU', 'TEST_RESU', 'FIN']
    assert_that(titles, contains(*refn))

    cmds = stage.sorted_commands
    names = [i.name for i in cmds if i.name != "_"]
    assert_that(names, contains(*refs))

    titles = [i.title for i in cmds]
    assert_that(titles, contains(*refn))

    text2 = study2comm(stage)

    case2 = history.create_case("Case 2")
    stage2 = case2.create_stage(":2:")
    comm2study(text2, stage2)
    assert_that(stage2.check(), equal_to(Validity.Nothing))


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
