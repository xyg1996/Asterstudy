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

"""Miscellaneous test cases"""


import unittest
from hamcrest import *
from testutils import attr
from testutils.tools import check_text_diff

from asterstudy import common
from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.history import History

from asterstudy.datamodel.comm2study import comm2study

#------------------------------------------------------------------------------
def test_basic_api():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    text = """DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),\n      DEBUG=_F(SDVERI='OUI'))\n"""
    stage.paste(text)

    assert_that(stage[0].text, equal_to(text))

    #--------------------------------------------------------------------------
    text2 = """DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'))\n"""
    assert_that(stage[0].check_text(text2), equal_to(True))
    assert_that(stage[0].text, equal_to(text))

    stage[0].text = text2
    assert_that(stage[0].text, equal_to(text2))

    #--------------------------------------------------------------------------
    text3 = """syntaxic error"""
    assert_that(stage[0].check_text(text3), equal_to(False))
    assert_that(stage[0].text, equal_to(text2))

    try:
        stage[0].text = text3
        assert False
    except common.ConversionError:
        assert_that(stage[0].text, equal_to(text2))
        assert True

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_single_concept_in_stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    text = """DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),\n      DEBUG=_F(SDVERI='OUI'))\n"""
    stage.paste(text)

    concept = stage[0]
    nb_uids = len(concept.model.uids)

    #--------------------------------------------------------------------------
    text2 = """DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'))\n"""
    concept.set_text(text2)
    assert_that(concept.text, equal_to(text2))
    assert_that(concept.model.uids, has_length(nb_uids))

    #--------------------------------------------------------------------------
    text3 = """syntaxic error"""
    assert_that(calling(concept.set_text).with_args(text3), raises(common.ConversionError))
    assert_that(stage[0].text, equal_to(text2))
    assert_that(concept.model.uids, has_length(nb_uids))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_many_concepts_in_stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

mesh = MODI_MAILLAGE(reuse=mesh,
                     MAILLAGE=mesh,
                     ORIE_PEAU_3D=_F(GROUP_MA='group'))

model = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                            PHENOMENE='MECANIQUE',
                            TOUT='OUI'),
                    MAILLAGE=mesh)
"""
    stage.paste(text)
    assert check_text_diff(stage.get_text(), text)
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    concept = stage[1]
    text = concept.text
    nb_uids = len(concept.model.uids)

    #--------------------------------------------------------------------------
    text2 = \
"""
mesh = MODI_MAILLAGE(ORIE_PEAU_3D=_F(GROUP_MA='group'))
"""
    concept.set_text(text2)
    assert check_text_diff(concept.text, text2)
    assert_that(concept.model.uids, has_length(nb_uids))

    text2 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

mesh = MODI_MAILLAGE(ORIE_PEAU_3D=_F(GROUP_MA='group'))

model = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                            PHENOMENE='MECANIQUE',
                            TOUT='OUI'),
                    MAILLAGE=mesh)
"""
    assert check_text_diff(stage.get_text(), text2)

    #--------------------------------------------------------------------------
    text3 = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'))
"""
    assert_that(concept.text2instance(text3).title, is_not(equal_to(concept.title)))
    assert_that(concept.check_text(text3), equal_to(False))
    concept.set_text(text3)
    assert check_text_diff(concept.text, text3)
    assert_that(concept.model.uids, has_length(nb_uids))

    text3 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'))

model = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                            PHENOMENE='MECANIQUE',
                            TOUT='OUI'),
                    MAILLAGE=_)
"""
    assert check_text_diff(stage.get_text(), text3)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_concept_dependencies():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    #--------------------------------------------------------------------------
    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

mesh = MODI_MAILLAGE(reuse=mesh,
                     MAILLAGE=mesh,
                     ORIE_PEAU_3D=_F(GROUP_MA='group'))

mesh = MODI_MAILLAGE(reuse=mesh,
                     MAILLAGE=mesh,
                     ORIE_PEAU_3D=_F(GROUP_MA='group2'))
"""
    stage.paste(text)
    assert check_text_diff(stage.get_text(), text)
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    concept = stage[1]

    #--------------------------------------------------------------------------
    text2 = \
"""
mesh = MODI_MAILLAGE(reuse=mesh,
                     MAILLAGE=mesh,
                     ORIE_PEAU_3D=_F(GROUP_MA='group1'))
"""
    concept.set_text(text2)
    assert check_text_diff(concept.text, text2)

    text2 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

mesh = MODI_MAILLAGE(reuse=mesh,
                     MAILLAGE=mesh,
                     ORIE_PEAU_3D=_F(GROUP_MA='group1'))

mesh = MODI_MAILLAGE(reuse=mesh,
                     MAILLAGE=mesh,
                     ORIE_PEAU_3D=_F(GROUP_MA='group2'))
"""
    assert check_text_diff(stage.get_text(), text2)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_wrong_args():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    command = stage.add_command('LIRE_MAILLAGE', 'mesh')
    assert_that(command.check_text(''), equal_to(False))
    assert_that(command.check_text('mesh = LIRE_MAILLAGE(UNIT=1)'), equal_to(False))

    #--------------------------------------------------------------------------
    command = stage.add_command('DEFI_OBSTACLE', 'obst')
    assert_that(command.check_text(''), equal_to(False))
    assert_that(command.check_text('obst = DEFI_OBSTACLE(TYPE="CERCLE")'), equal_to(True))
    assert_that(command.check_text('obst = DEFI_OBSTACLE(TYPSE="CERCLE")'), equal_to(False))
    assert_that(command.check_text('obst = DEFI_OBSTACLE(TYPE="CERCLE", VALE=(1.2, 2.3))'), equal_to(True))
    assert_that(command.check_text('obst = DEFI_OBSTACLE(TYPE="CERCLE", VALSE=(1.2, 2.3))'), equal_to(False))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_comments():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    concept = stage.add_command('LIRE_MAILLAGE', 'mesh')

    #--------------------------------------------------------------------------
    text1 = \
"""
# mesh = LIRE_MAILLAGE(UNITE=20)
"""
    assert_that(concept.check_text(text1), equal_to(False))

    #--------------------------------------------------------------------------
    text2 = \
"""
# before
mesh = LIRE_MAILLAGE(UNITE=20)
"""
    assert_that(concept.check_text(text2), equal_to(False))

    #--------------------------------------------------------------------------
    text3 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20) # behind
"""
    assert_that(concept.check_text(text3), equal_to(True))
    concept.set_text(text3)
    assert check_text_diff(concept.text, "mesh = LIRE_MAILLAGE(UNITE=20)")

    #--------------------------------------------------------------------------
    text4 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)
# after
"""
    assert_that(concept.check_text(text4), equal_to(False))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_many_stages():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

mesh = MODI_MAILLAGE(reuse=mesh,
                     MAILLAGE=mesh,
                     ORIE_PEAU_3D=_F(GROUP_MA='group'))
"""
    stage1 = case.create_stage(':1:')
    stage1.paste(text)

    #--------------------------------------------------------------------------
    text = \
"""
mesh = MODI_MAILLAGE(reuse=mesh,
                     MAILLAGE=mesh,
                     ORIE_PEAU_3D=_F(GROUP_MA='group2'))
"""
    stage2 = case.create_stage(':2:')
    stage2.paste(text)

    #--------------------------------------------------------------------------
    concept = stage1[1]

    #--------------------------------------------------------------------------
    text2 = \
"""
mesh1 = MODI_MAILLAGE(MAILLAGE=mesh,
                      ORIE_PEAU_3D=_F(GROUP_MA='group1'))
"""
    concept.set_text(text2)
    assert check_text_diff(concept.text, text2)

    text2 = \
"""
mesh = MODI_MAILLAGE(MAILLAGE=mesh1,
                     ORIE_PEAU_3D=_F(GROUP_MA='group2'))
"""
    assert check_text_diff(stage2.get_text(), text2)

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_many_concepts():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    concept = stage.add_command('LIRE_MAILLAGE', 'mesh')

    #--------------------------------------------------------------------------
    text1 = \
"""
mesh1 = LIRE_MAILLAGE(UNITE=20)
mesh2 = LIRE_MAILLAGE(UNITE=20)
"""
    assert_that(concept.check_text(text1), equal_to(False))

    #--------------------------------------------------------------------------
    pass

if __name__ == "__main__":
    #--------------------------------------------------------------------------
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
