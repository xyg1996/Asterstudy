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

"""Automatic tests for import feature."""


import unittest

from asterstudy.datamodel import abstract_data_model as ADM
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.general import ConversionLevel, Validity
from asterstudy.datamodel.history import History
from hamcrest import *
from testutils import attr
from testutils.tools import check_export, check_import


def test():
    """Test for import of variables"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comment = stage.add_command('_CONVERT_COMMENT')
    comment['EXPR'] = 'Line with a comment'

    command = stage.add_command('DEBUT')
    ADM.add_parent(command, comment)

    command['CODE']['NIV_PUB_WEB'] = 'INTERNET'
    command['DEBUG']['SDVERI'] = 'OUI'
    command.check()

    command = stage.add_variable('var', 'pi')
    assert_that(command.expression, equal_to('pi'))

    from math import pi
    assert_that(command.update('2.*pi'), equal_to(2.*pi))

    command = stage.add_command('FIN')

    text = \
"""
# Line with a comment
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

var = 2. * pi

FIN()
"""
    assert_that(check_import(text))
    assert_that(check_export(stage, text))


def test_simplified_27170():
    history = History()
    case = history.current_case

    stage1 = case.create_stage(':1:')
    text1 = \
"""
absc = 'ABSC'
one = 1.
two = 2.
info = 2
"""
    comm2study(text1, stage1)
    assert_that(stage1, has_length(4))

    stage2 = case.create_stage(':2:')
    text2 = \
"""
f1 = DEFI_FONCTION(NOM_PARA=absc, VALE=(one, two), INFO=info)
"""
    comm2study(text2, stage2, strict=ConversionLevel.Any)
    assert_that(stage2, has_length(1))


def test_27170():
    history = History()
    case = history.current_case

    stage1 = case.create_stage(':1:')
    text1 = \
"""
Ncouche = 2

mesh = LIRE_MAILLAGE(UNITE=20)

MOD_MECA = AFFE_MODELE(AFFE=_F(MODELISATION=('3D', ),
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=mesh)

elemprop = AFFE_CARA_ELEM(COQUE=_F(COQUE_NCOU=Ncouche,
                                   EPAIS=0.012,
                                   GROUP_MA=('jupeFaces', ),
                                   VECTEUR=(0.0, 0.0, 1.0)),
                          MODELE=MOD_MECA,
                          POUTRE=_F(CARA=('R', 'EP'),
                                    GROUP_MA=('visEdges', ),
                                    SECTION='CERCLE',
                                    VALE=(0.03, 0.03)))
"""
    comm2study(text1, stage1)
    assert_that(stage1, has_length(4))

    stage2 = case.create_stage(':2:')
    text2 = \
"""
elemp2 = AFFE_CARA_ELEM(
  COQUE=_F(
    COQUE_NCOU=Ncouche,
    EPAIS=0.012,
    GROUP_MA=('jupeFaces', ),
    VECTEUR=(0.0, 0.0, 1.0)
  ),
  MODELE=MOD_MECA,
  POUTRE=_F(
    CARA=('R', 'EP'),
    GROUP_MA=('visEdges', ),
    SECTION='CERCLE',
    VALE=(0.03, 0.03)
  )
) """
    comm2study(text2, stage2, strict=ConversionLevel.Any)
    assert_that(stage2, has_length(1))


def test_var_comment():
    # check that comment are ignored
    history = History()
    case = history.current_case

    stage = case.create_stage(':1:')
    text = """var = 1. # 5%"""
    comm2study(text, stage, strict=ConversionLevel.Any)
    assert_that(stage, has_length(1))
    var = stage['var']
    assert_that(var.evaluation, equal_to(1.))
    assert_that(var.expression, equal_to("1."))


def test_comment():
    """Test for multilines comments"""
    from asterstudy.datamodel.aster_parser import is_empty_comment

    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
# .
# Line with a comment
# -------------------------------------------------

# comment continues here
# another line
# end of comment
# **++--**//--==//**$$
DEBUT()
"""
    expected_text = \
"""
# .
# Line with a comment
# -------------------------------------------------
# comment continues here
# another line
# end of comment
# **++--**//--==//**$$
DEBUT()
"""
    # not currently plugged in the parser
    null = [i for i in text.splitlines() if is_empty_comment(i)]
    assert_that(null, has_length(3))

    comm2study(text, stage)
    assert_that(stage, has_length(2))

    assert_that(check_export(stage, expected_text))


def test_type():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    a = stage.add_variable('a', '2')
    b = stage.add_variable('b', '2.5')
    c = stage.add_variable('c', '(2 * b)')

    cmd = stage.add_command('DEFI_LIST_REEL')
    cmd.init({'DEBUT': 0.0, 'INTERVALLE': {'JUSQU_A': 10, 'NOMBRE': a}})
    assert_that(cmd.check(), equal_to(Validity.Nothing))

    cmd.init({'DEBUT': 0.0, 'INTERVALLE': {'JUSQU_A': 10.0, 'NOMBRE': b}})
    assert_that(cmd.check(), equal_to(Validity.Syntaxic))

    cmd.init({'DEBUT': 0.0, 'INTERVALLE': {'JUSQU_A': 10.0, 'NOMBRE': c}})
    assert_that(cmd.check(), equal_to(Validity.Nothing))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
