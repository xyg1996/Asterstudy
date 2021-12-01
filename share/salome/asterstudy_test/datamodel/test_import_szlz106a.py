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

#------------------------------------------------------------------------------
def test():
    """Test for szlz106a.comm"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    command = stage.add_command('DEBUT')

    command['CODE']['NIV_PUB_WEB'] = 'INTERNET'

    factor = command['DEBUG']
    assert('SDVERI' in factor.rkeys())

    command['DEBUG']['SDVERI'] = 'OUI'

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_FONCTION', 'LOIDOM1')

    command['INTERPOL'] = ('LOG', 'LOG')
    command['NOM_PARA'] = 'SIGM'
    command['PROL_DROITE'] = 'LINEAIRE'
    command['PROL_GAUCHE'] = 'LINEAIRE'
    command['VALE'] = (
        1.0, 312500000000.0, 2.0, 9765625000.0, 5.0, 100000000.0, 25.0, 32000.0,
        30.0, 12860.09, 35.0, 5949.899, 40.0, 3051.76, 45.0, 1693.51, 50.0,
        1000.0, 55.0, 620.921, 60.0, 401.8779, 65.0, 269.329, 70.0, 185.934,
        75.0, 131.6869, 80.0, 95.3674, 85.0, 70.4296, 90.0, 52.9221, 95.0,
        40.3861, 100.0, 31.25, 105.0, 24.4852, 110.0, 19.40379, 115.0, 15.5368,
        120.0, 12.55869, 125.0, 10.23999, 130.0, 8.41653, 135.0, 6.96917, 140.0,
        5.81045, 145.0, 4.8754, 150.0, 4.11523, 155.0, 3.49294, 160.0, 2.98023,
        165.0, 2.55523, 170.0, 2.20093, 175.0, 1.90397, 180.0, 1.65382, 185.0,
        1.44209, 190.0, 1.26207, 195.0, 1.10835, 200.0, 0.976562
    )

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_MATERIAU', 'MAT0')

    factor = command['FATIGUE']
    factor['A_BASQUIN'] = 1.001730939e-14
    factor['BETA_BASQUIN'] = 4.065

    #--------------------------------------------------------------------------
    command = stage.add_command('POST_FATI_ALEA', 'TAB1')

    command['COMPTAGE'] = 'NIVEAU'
    command['DOMMAGE'] = 'WOHLER'
    command['DUREE'] = 1.0
    command['MATER'] = stage['MAT0']
    command['MOMENT_SPEC_0'] = 182.5984664
    command['MOMENT_SPEC_2'] = 96098024.76

    #--------------------------------------------------------------------------
    command = stage.add_command('TEST_TABLE')

    assert('b_values' not in command.rkeys())
    command['REFERENCE'] = 'SOURCE_EXTERNE'
    command['VALE_REFE'] = 3.851827E-07
    assert(command['VALE_REFE'] == 3.851827E-07)

    command['PRECISION'] = 1.5E-05
    command['VALE_CALC'] = 3.8517772476578E-07
    command['NOM_PARA'] = 'DOMMAGE'

    command['TABLE'] = stage['TAB1']
    assert(command['TABLE'] == stage['TAB1'])

    #--------------------------------------------------------------------------
    command = stage.add_command('FIN')

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

MAT0 = DEFI_MATERIAU(FATIGUE=_F(A_BASQUIN=1.001730939e-14,
                                BETA_BASQUIN=4.065))

LOIDOM1 = DEFI_FONCTION(INTERPOL=('LOG', 'LOG'),
                        NOM_PARA='SIGM',
                        PROL_DROITE='LINEAIRE',
                        PROL_GAUCHE='LINEAIRE',
                        VALE=(1.0, 312500000000.0, 2.0, 9765625000.0, 5.0, 100000000.0, 25.0, 32000.0, 30.0, 12860.09, 35.0, 5949.899, 40.0, 3051.76, 45.0, 1693.51, 50.0, 1000.0, 55.0, 620.921, 60.0, 401.8779, 65.0, 269.329, 70.0, 185.934, 75.0, 131.6869, 80.0, 95.3674, 85.0, 70.4296, 90.0, 52.9221, 95.0, 40.3861, 100.0, 31.25, 105.0, 24.4852, 110.0, 19.40379, 115.0, 15.5368, 120.0, 12.55869, 125.0, 10.23999, 130.0, 8.41653, 135.0, 6.96917, 140.0, 5.81045, 145.0, 4.8754, 150.0, 4.11523, 155.0, 3.49294, 160.0, 2.98023, 165.0, 2.55523, 170.0, 2.20093, 175.0, 1.90397, 180.0, 1.65382, 185.0, 1.44209, 190.0, 1.26207, 195.0, 1.10835, 200.0, 0.976562))

TAB1 = POST_FATI_ALEA(COMPTAGE='NIVEAU',
                      DOMMAGE='WOHLER',
                      DUREE=1.0,
                      MATER=MAT0,
                      MOMENT_SPEC_0=182.5984664,
                      MOMENT_SPEC_2=96098024.76)

TEST_TABLE(NOM_PARA='DOMMAGE',
           PRECISION=1.5e-05,
           REFERENCE='SOURCE_EXTERNE',
           TABLE=TAB1,
           VALE_CALC=3.8517772476578e-07,
           VALE_REFE=3.851827e-07)

FIN()
"""
    #--------------------------------------------------------------------------
    assert(check_export(stage, text, sort=True))

    assert(check_import(text, sort=True))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
