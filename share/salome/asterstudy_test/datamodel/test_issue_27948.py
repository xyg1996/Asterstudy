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

"""Automatic tests for issue27948."""


import unittest

from asterstudy.common import ConversionError
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.general import ConversionLevel, Validity
from asterstudy.datamodel.history import History
from hamcrest import *


def test_graph_after_text():
    history = History()
    case = history.current_case

    stage0 = case.create_stage(':init:')
    text0 = """tab0 = CREA_TABLE(LISTE=_F(PARA='X', LISTE_R=[0., 1.]))"""
    comm2study(text0, stage0)

    stage1 = case.create_stage(':text:')
    stage1.use_text_mode()
    assert_that(stage1.check(), equal_to(Validity.Ok))

    stage2 = case.create_stage(':graph:')
    stage2.use_text_mode()
    stage2.set_text("""IMPR_TABLE(TABLE=tab0)\nIMPR_TABLE(TABLE=tab1)""")
    assert_that(stage2.check(), equal_to(Validity.Ok))

    # 'tab1' is missing
    assert_that(calling(stage2.use_graphical_mode),
                raises(ConversionError, "tab1.*not defined"))

    # declare that 'tab1' is defined in the text stage
    stage1.update_commands([('tab1', 'CREA_TABLE', 'table_sdaster'), ])
    stage2.use_graphical_mode()
    assert_that(stage2[0].check(safe=False), equal_to(Validity.Ok))
    assert_that(stage2[1].check(safe=False), equal_to(Validity.Ok))
    assert_that(stage2.check(), equal_to(Validity.Ok))

    # declare 'tab0' as removed by the text stage
    stage1.delete_commands(['tab0', ])
    impr0 = stage2[0]
    impr0.reset_validity()
    assert_that(impr0.check(), equal_to(Validity.Dependency))
    assert_that(stage2.check(), equal_to(Validity.Dependency))


def test_graph_after_text2():
    # same with functions (DEFI_FONCTION uses a sdprod function)
    history = History()
    case = history.current_case

    stage0 = case.create_stage(':init:')
    text0 = """func0 = DEFI_FONCTION(NOM_PARA='INST', VALE=(0., 0., 1., 1.))"""
    comm2study(text0, stage0)

    stage1 = case.create_stage(':text:')
    stage1.use_text_mode()
    assert_that(stage1.check(), equal_to(Validity.Ok))

    stage2 = case.create_stage(':graph:')
    stage2.use_text_mode()
    stage2.set_text("IMPR_FONCTION(COURBE=_F(FONCTION=func0))\n"
                    "IMPR_FONCTION(COURBE=_F(FONCTION=func1))")
    assert_that(stage2.check(), equal_to(Validity.Ok))

    # 'func1' is missing
    assert_that(calling(stage2.use_graphical_mode),
                raises(ConversionError, "func1.*not defined"))

    # declare that 'func1' is defined in the text stage
    stage1.update_commands([('func1', 'DEFI_FONCTION', 'fonction_sdaster'), ])
    stage2.use_graphical_mode()
    assert_that(stage2[0].check(safe=False), equal_to(Validity.Ok))
    assert_that(stage2[1].check(safe=False), equal_to(Validity.Ok))
    assert_that(stage2.check(), equal_to(Validity.Ok))

    # declare 'tab0' as removed by the text stage
    stage1.delete_commands(['func0', ])
    impr0 = stage2[0]
    impr0.reset_validity()
    assert_that(impr0.check(), equal_to(Validity.Dependency))
    assert_that(stage2.check(), equal_to(Validity.Dependency))


def test_text():
    history = History()
    case = history.current_case
    stage = case.create_stage(':text:')
    stage.use_text_mode()
    stage.update_commands([
        ('resu1', 'STAT_NON_LINE', 'evol_noli'),
        ('resu2', 'STAT_NON_LINE', 'resultat_sdaster'),
        ('resu3', 'CALC_CHAMP', 'evol_noli'),
        ('resu4', 'CALC_CHAMP', 'resultat_sdaster'),
        ('resu5', 'CALC_CHAMP', 'maillage_sdaster'),
    ])
    assert_that(stage.commands, has_length(3))
    names = [i.name for i in stage.commands]
    assert_that(names, contains_inanyorder('resu1', 'resu3', 'resu4'))


def test_28018():
    history = History()
    case = history.current_case

    stage0 = case.create_stage(':init:')
    text0 = """mesh = LIRE_MAILLAGE()"""
    comm2study(text0, stage0)

    stage1 = case.create_stage(':text:')
    text1 = """model = AFFE_MODELE(AFFE=_F(MODELISATION=('3D', ),
                                   PHENOMENE='MECANIQUE',
                                   TOUT='OUI'),
                                   MAILLAGE=mesh)"""
    comm2study(text1, stage1)
    assert_that(stage1.check(), equal_to(Validity.Ok))
    stage1.use_text_mode()
    stage1.update_commands([
        ('model', 'AFFE_MODELE', 'modele_sdaster'),
        ('model2', 'AFFE_MODELE', 'modele_sdaster'), ])
    assert_that(stage1.commands, has_length(2))

    model = stage1["model"]
    model2 = stage1["model2"]
    # model is fully valid because it has all the required keywords
    # model2 is syntaxicly invalid because it has no keyword
    # => check() must skip Syntaxic validation

    stage2 = case.create_stage(':graph:')
    load = stage2.add_command('AFFE_CHAR_MECA', 'load')
    load.init({"DDL_IMPO": {"GROUP_MA": "ABC", "LIAISON": "ENCASTRE"},
               "MODELE": model})

    load2 = stage2.add_command('AFFE_CHAR_MECA', 'load2')
    load2.init({"DDL_IMPO": {"GROUP_MA": "ABC", "LIAISON": "ENCASTRE"},
                "MODELE": model2})

    assert_that(load.check(), equal_to(Validity.Ok))
    assert_that(load2.check(), equal_to(Validity.Ok))
    assert_that(stage2.check(), equal_to(Validity.Ok))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
