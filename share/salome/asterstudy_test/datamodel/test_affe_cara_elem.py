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

"""Automatic tests for some AFFE_CARA_ELEM checkings."""


import unittest

from hamcrest import *

from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.history import History
from testutils import attr


def test_sdnv112a():
    """Test for command from sdnv112a"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

model = AFFE_MODELE(
    AFFE=_F(GROUP_MA='LIG12', MODELISATION='2D_DIS_T', PHENOMENE='MECANIQUE'),
    MAILLAGE=mesh
)

caraelem = AFFE_CARA_ELEM(
    POUTRE=(
        _F(
            GROUP_MA='POU1',
            SECTION='RECTANGLE',
            CARA=('HY','HZ',),
            VALE=(0.15,0.325,),),
        _F(
            GROUP_MA='COL1',
            SECTION='RECTANGLE',
            CARA='H',
            VALE=0.2,),
    ),
    MODELE=model
)
"""
    comm2study(text, stage)
    assert_that(stage, has_length(3))
    cara = stage[2]
    # import os
    # os.environ['DEBUG'] = '2'
    assert_that(cara.check(safe=False), equal_to(Validity.Nothing))


def test_ssns111a():
    """Test for command from ssns111a"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    text = \
"""
MAILTOT = LIRE_MAILLAGE(UNITE=20)

LEMOD=AFFE_MODELE(
   MAILLAGE=MAILTOT,

   AFFE=(
      _F(GROUP_MA=('ACPLUS','ACMOINS',), PHENOMENE='MECANIQUE', MODELISATION='GRILLE_EXCENTRE',),
      _F(GROUP_MA=('DALLE','B0X','B1X'), PHENOMENE='MECANIQUE', MODELISATION='DKT',),),
)

Epdalle = 25.0E-02;NbCouche=5

LACAR=AFFE_CARA_ELEM(
   MODELE=LEMOD,
   COQUE=_F(GROUP_MA=('DALLE',), EPAIS=Epdalle, COQUE_NCOU=NbCouche, ANGL_REP=(0.0,0.0,),),
   GRILLE=(
      _F(GROUP_MA='ACPLUS',  SECTION=  9.0478E-04, ANGL_REP_1=(0,0,), EXCENTREMENT= 0.10,),
      _F(GROUP_MA='ACMOINS', SECTION= 39.2700E-04, ANGL_REP_1=(0,0,), EXCENTREMENT=-0.10,),
   ),
)
"""
    comm2study(text, stage)
    assert_that(stage, has_length(5))
    cara = stage[-1]
    assert_that(cara.check(safe=False), equal_to(Validity.Nothing))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
