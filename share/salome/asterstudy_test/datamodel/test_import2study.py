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

from asterstudy.datamodel.history import History

from testutils.tools import check_export, check_import

from hamcrest import *

#------------------------------------------------------------------------------
def test():
    """Test for import of COMM file to study"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    command = stage.add_command('DEBUT')

    assert('CODE' in command.rkeys())
    factor = command['CODE']

    assert_that(calling(command.__setitem__).
                with_args('NIV_PUB_WEB', 'INTERNET'),
                raises(KeyError))

    assert('NIV_PUB_WEB' in factor.rkeys())
    simple = factor['NIV_PUB_WEB']

    simple.value = 'INTERNET'
    assert(simple.value == 'INTERNET')

    assert('DEBUG' in command.rkeys())
    factor = command['DEBUG']
    simple = factor['SDVERI']

    factor['SDVERI'] = 'OUI'
    assert(simple.value == 'OUI')

    #--------------------------------------------------------------------------
    command2 = stage('DEBUT')({'DEBUG': {'SDVERI': 'OUI'},
                               'CODE': {'NIV_PUB_WEB': 'INTERNET'}})

    assert_that(command * command2, none())

    #--------------------------------------------------------------------------
    command2.init(command.storage)

    assert_that(command * command2, none())

    #--------------------------------------------------------------------------
    del stage[command2]

    #--------------------------------------------------------------------------
    command = stage.add_command('LIRE_MAILLAGE', 'MAYA')
    command['UNITE'] = 22

    assert('FORMAT' in command.rkeys())
    simple = command['FORMAT']

    command['FORMAT'] = 'MED'
    assert(simple.value == 'MED')

    #--------------------------------------------------------------------------
    command = stage.add_command('AFFE_MODELE', 'MODELE')

    assert('AFFE' in command.rkeys())
    sequence = command['AFFE']

    #--------------------------------------------------------------------------
    item = sequence.append()

    assert('GROUP_MA' in item.rkeys())
    simple = item['GROUP_MA']

    item['GROUP_MA'] = 'EFLUIDE'
    assert(simple.value == 'EFLUIDE')
    assert(item['GROUP_MA'].value == 'EFLUIDE')

    #--------------------------------------------------------------------------
    assert('PHENOMENE' in item.rkeys())
    simple = item['PHENOMENE']

    item['PHENOMENE'] = 'MECANIQUE'
    assert(simple.value == 'MECANIQUE')
    assert(item['PHENOMENE'].value == 'MECANIQUE')

    #--------------------------------------------------------------------------
    assert('MODELISATION' in item.rkeys())
    simple = item['MODELISATION']

    item['MODELISATION'] = '2D_FLUIDE'
    assert(simple.value == '2D_FLUIDE')
    assert(item['MODELISATION'].value == '2D_FLUIDE')

    #--------------------------------------------------------------------------
    item = sequence.append()

    item['GROUP_MA'] = ('EFS_P_IN', 'EFS_PIST', 'EFS_P_OU')
    item['MODELISATION'] = '2D_FLUI_STRU'
    item['PHENOMENE'] = 'MECANIQUE'

    #--------------------------------------------------------------------------
    item = sequence.append()

    item['GROUP_MA'] = ('E_PISTON', 'E_P_IN', 'ES_P_IN', 'E_P_OU')
    item['MODELISATION'] = 'D_PLAN'
    item['PHENOMENE'] = 'MECANIQUE'

    #--------------------------------------------------------------------------
    item = sequence.append()

    item['GROUP_MA'] = 'AMORPONC'
    item['MODELISATION'] = '2D_DIS_T'
    item['PHENOMENE'] = 'MECANIQUE'

    #--------------------------------------------------------------------------
    item = sequence.append()

    item['GROUP_MA'] = ('MASSPONC',)
    item['MODELISATION'] = '2D_DIS_T'
    item['PHENOMENE'] = 'MECANIQUE'

    #--------------------------------------------------------------------------
    command['INFO'] = 2

    command['MAILLAGE'] = stage['MAYA']

    #--------------------------------------------------------------------------
    command = stage.add_command('FIN')

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

MAYA = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=22)

MODELE = AFFE_MODELE(AFFE=(_F(GROUP_MA='EFLUIDE',
                              MODELISATION='2D_FLUIDE',
                              PHENOMENE='MECANIQUE'),
                           _F(GROUP_MA=('EFS_P_IN', 'EFS_PIST', 'EFS_P_OU'),
                              MODELISATION='2D_FLUI_STRU',
                              PHENOMENE='MECANIQUE'),
                           _F(GROUP_MA=('E_PISTON', 'E_P_IN', 'ES_P_IN', 'E_P_OU'),
                              MODELISATION='D_PLAN',
                              PHENOMENE='MECANIQUE'),
                           _F(GROUP_MA='AMORPONC',
                              MODELISATION='2D_DIS_T',
                              PHENOMENE='MECANIQUE'),
                           _F(GROUP_MA=('MASSPONC', ),
                              MODELISATION='2D_DIS_T',
                              PHENOMENE='MECANIQUE')),
                     INFO=2,
                     MAILLAGE=MAYA)

FIN()
"""
    assert(check_export(stage, text))

    assert(check_import(text))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
