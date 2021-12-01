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

from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.history import History

from testutils.tools import check_export, check_import


#------------------------------------------------------------------------------
def test_maille_none():
    """Test for fdlv102b.comm: no default in export"""
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    stage('DEBUT')

    #--------------------------------------------------------------------------
    command = stage('LIRE_MAILLAGE', 'mesh')
    command['FORMAT'] = 'MED'
    command['UNITE'] = 20

    #--------------------------------------------------------------------------
    command = stage('AFFE_MODELE', 'model')
    command['MAILLAGE'] = stage['mesh']

    factor = command['AFFE']
    factor['GROUP_MA'] = 'LIG12'
    factor['PHENOMENE'] = 'MECANIQUE'
    factor['MODELISATION'] = '2D_DIS_T'

    #--------------------------------------------------------------------------
    command = stage('AFFE_CARA_ELEM', 'caraelem')
    command['MODELE'] = stage['model']

    factor = command['DISCRET_2D'].append()
    factor['GROUP_MA'] = 'LIG12'
    factor['SYME'] = 'OUI'
    factor['CARA'] = 'K_T_D_L'
    factor['VALE'] = (1., 100.e6)

    factor = command['DISCRET_2D'].append()
    factor['GROUP_MA'] = 'LIG12'
    factor['SYME'] = 'OUI'
    factor['CARA'] = 'M_T_L'
    factor['VALE'] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    #--------------------------------------------------------------------------
    stage('FIN')

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT()

mesh = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)

model = AFFE_MODELE(AFFE=_F(GROUP_MA='LIG12',
                            MODELISATION='2D_DIS_T',
                            PHENOMENE='MECANIQUE'),
                    MAILLAGE=mesh)

caraelem = AFFE_CARA_ELEM(DISCRET_2D=(_F(CARA='K_T_D_L',
                                         GROUP_MA='LIG12',
                                         SYME='OUI',
                                         VALE=(1.0, 100000000.0)),
                                      _F(CARA='M_T_L',
                                         GROUP_MA='LIG12',
                                         SYME='OUI',
                                         VALE=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),
                          MODELE=model)

FIN()
"""
    #--------------------------------------------------------------------------
    assert(check_export(stage, text))

    #--------------------------------------------------------------------------
    assert(check_import(text))


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
