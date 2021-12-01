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

"""Data Model tests for Copy & Paste functionality"""


import unittest

from hamcrest import * # pragma pylint: disable=unused-import
from testutils import attr

from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.general import Validity
from asterstudy.datamodel.dataset import DataSet

from testutils.tools import check_text_eq, check_text_ne

#------------------------------------------------------------------------------
def test_paste_into_the_same_stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

F_MANSON = DEFI_FONCTION(
    NOM_PARA='EPSI',
    PROL_DROITE='LINEAIRE',
    PROL_GAUCHE='LINEAIRE',
    TITRE='FONCTION DE MANSON_COFFIN',
    VALE=(0.0, 200000.0, 2.0, 0.0)
)
"""
    stage = case.create_stage(':1:')

    comm2study(text, stage)

    assert_that(stage, has_length(2))
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    snippet = \
"""
F_WOHLER = DEFI_FONCTION(
    NOM_PARA='SIGM',
    PROL_DROITE='LINEAIRE',
    PROL_GAUCHE='LINEAIRE',
    TITRE='FONCTION DE WOHLER',
    VALE=(0.0, 200000.0, 200.0, 0.0)
)
"""
    stage.paste(snippet)

    assert_that(stage, has_length(3))
    assert_that(stage[2].name, equal_to('F_WOHLER'))
    assert_that(stage.check(), equal_to(Validity.Ok))

    assert_that(case, has_length(1))
    assert_that(case.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_paste_into_another_stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

F_MANSON = DEFI_FONCTION(
    NOM_PARA='EPSI',
    PROL_DROITE='LINEAIRE',
    PROL_GAUCHE='LINEAIRE',
    TITRE='FONCTION DE MANSON_COFFIN',
    VALE=(0.0, 200000.0, 2.0, 0.0)
)
"""
    stage = case.create_stage(':1:')

    comm2study(text, stage)

    assert_that(stage, has_length(2))
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    snippet = \
"""
F_WOHLER = DEFI_FONCTION(
    NOM_PARA='SIGM',
    PROL_DROITE='LINEAIRE',
    PROL_GAUCHE='LINEAIRE',
    TITRE='FONCTION DE WOHLER',
    VALE=(0.0, 200000.0, 200.0, 0.0)
)
"""
    stage = case.create_stage(':2:')

    stage.paste(snippet)

    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to('F_WOHLER'))
    assert_that(stage.check(), equal_to(Validity.Ok))

    assert_that(case, has_length(2))
    assert_that(case.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_paste_into_invalid_stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage = case.create_stage(':1:')
    assert_that(stage.check(), equal_to(Validity.Ok))

    stage('AFFE_CARA_ELEM', 'elemprop')
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to('elemprop'))
    assert_that(stage.check(), equal_to(Validity.Syntaxic))

    #--------------------------------------------------------------------------
    stage.use_text_mode()
    stage.use_graphical_mode()

    #--------------------------------------------------------------------------
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to('elemprop'))
    assert_that(stage.check(), equal_to(Validity.Syntaxic))

    #--------------------------------------------------------------------------
    snippet = "model = MODI_MODELE()"

    stage.paste(snippet)

    assert_that(stage, has_length(2))
    assert_that(stage[1].name, equal_to('model'))
    assert_that(stage.check(), equal_to(Validity.Syntaxic))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_paste_invalid_snippet():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

F_MANSON = DEFI_FONCTION(
    NOM_PARA='EPSI',
    PROL_DROITE='LINEAIRE',
    PROL_GAUCHE='LINEAIRE',
    TITRE='FONCTION DE MANSON_COFFIN',
    VALE=(0.0, 200000.0, 2.0, 0.0)
)
"""
    stage = case.create_stage(':1:')

    comm2study(text, stage)

    assert_that(stage, has_length(2))
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    snippet = \
"""
AN INVALID SNIPPET
"""
    assert_that(calling(stage.paste).with_args(snippet), raises(Exception))

    assert_that(stage, has_length(2))
    assert_that(stage.check(), equal_to(Validity.Ok))

    assert_that(case, has_length(1))
    assert_that(case.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    assert_that(stage.mode, equal_to(DataSet.graphicalMode))

    stage.use_text_mode()

    assert_that(stage.mode, equal_to(DataSet.textMode))

    stage.paste(snippet)

    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_paste_into_text_stage():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage = case.create_stage(':1:')
    assert_that(stage, has_length(0))

    stage.use_text_mode()
    assert_that(stage.check(), equal_to(Validity.Ok))

    snippet = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

F_MANSON = DEFI_FONCTION(
    NOM_PARA='EPSI',
    PROL_DROITE='LINEAIRE',
    PROL_GAUCHE='LINEAIRE',
    TITRE='FONCTION DE MANSON_COFFIN',
    VALE=(0.0, 200000.0, 2.0, 0.0)
)"""
    stage.paste(snippet)
    assert_that(stage.check(), equal_to(Validity.Ok))
    assert_that(check_text_eq(snippet, stage.get_text()))

    #--------------------------------------------------------------------------
    snippet = "FIN()"
    stage.paste(snippet)
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

F_MANSON = DEFI_FONCTION(
    NOM_PARA='EPSI',
    PROL_DROITE='LINEAIRE',
    PROL_GAUCHE='LINEAIRE',
    TITRE='FONCTION DE MANSON_COFFIN',
    VALE=(0.0, 200000.0, 2.0, 0.0)
)
FIN()"""
    assert_that(check_text_eq(text, stage.get_text()))
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    snippet = \
"""

"""
    stage.paste(snippet)
    assert_that(stage.check(), equal_to(Validity.Ok))
    assert_that(check_text_eq(text, stage.get_text()))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_paste_in_between_graphical_stages():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))
"""
    stage = case.create_stage(':1:')

    comm2study(text, stage)

    assert_that(stage, has_length(1))
    assert_that(stage.check(), equal_to(Validity.Ok))
    assert_that(stage.mode, equal_to(DataSet.graphicalMode))

    #--------------------------------------------------------------------------
    snippet = \
"""
F_WOHLER = DEFI_FONCTION(
    NOM_PARA='SIGM',
    PROL_DROITE='LINEAIRE',
    PROL_GAUCHE='LINEAIRE',
    TITRE='FONCTION DE WOHLER',
    VALE=(0.0, 200000.0, 200.0, 0.0)
)
"""
    stage = case.create_stage(':2:')

    stage.paste(snippet)

    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to('F_WOHLER'))
    assert_that(stage.check(), equal_to(Validity.Ok))
    assert_that(stage.mode, equal_to(DataSet.graphicalMode))

    assert_that(case, has_length(2))
    assert_that(case.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    snippet = \
"""
F_MANSON = DEFI_FONCTION(
    NOM_PARA='EPSI',
    PROL_DROITE='LINEAIRE',
    PROL_GAUCHE='LINEAIRE',
    TITRE='FONCTION DE MANSON_COFFIN',
    VALE=(0.0, 200000.0, 2.0, 0.0)
)
"""
    stage = case[':1:']

    stage.paste(snippet)

    assert_that(stage, has_length(2))
    assert_that(stage[1].name, equal_to('F_MANSON'))
    assert_that(stage.check(), equal_to(Validity.Ok))
    assert_that(stage.mode, equal_to(DataSet.graphicalMode))

    assert_that(case, has_length(2))
    assert_that(case.check(), equal_to(Validity.Ok))
    assert_that(case[':2:'].mode, equal_to(DataSet.graphicalMode))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
def test_copy_paste():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

F_MANSON = DEFI_FONCTION(
    NOM_PARA='EPSI',
    PROL_DROITE='LINEAIRE',
    PROL_GAUCHE='LINEAIRE',
    TITRE='FONCTION DE MANSON_COFFIN',
    VALE=(0.0, 200000.0, 2.0, 0.0)
)
"""
    stage = case.create_stage(':1:')

    comm2study(text, stage)

    assert_that(stage, has_length(2))
    assert_that(stage[1].name, equal_to('F_MANSON'))
    assert_that(stage.check(), equal_to(Validity.Ok))

    #--------------------------------------------------------------------------
    snippet = stage.copy2str(1)

    stage = case.create_stage(':2:')
    stage.paste(snippet)

    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to('F_MANSON'))
    assert_that(stage.check(), equal_to(Validity.Naming))

    assert_that(case, has_length(2))
    assert_that(case.check(), equal_to(Validity.Naming))


def test_paste_invalid_name():
    from asterstudy.common import ConversionError
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    snippet = \
"""
AFFE_MODELE = AFFE_MODELE()
"""
    assert_that(calling(stage.paste).with_args(snippet),
                raises(ConversionError, "Unauthorized name"))
    stage.paste("model = AFFE_MODELE()")
    assert_that(stage, has_length(1))



@attr('fixit')
def test_paste_invalid_command_1():
    # See issue #1238
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage = case.create_stage(':1:')
    text = \
"""
table = LIRE_TABLE(UNITE=1)
recu = RECU_FONCTION(TABLE=table)
"""
    comm2study(text, stage)

    assert_that(stage, has_length(2))
    assert_that(stage[0].name, equal_to('table'))
    assert_that(stage[1].name, equal_to('recu'))

    #--------------------------------------------------------------------------
    stage['table'].delete()

    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to('recu'))

    content = str(stage['recu'])
    stage.paste(content)

    assert_that(stage, has_length(2))
    assert_that(stage[0].name, equal_to('recu'))
    assert_that(stage[1].name, equal_to('recu'))
    assert_that(stage[0] * stage[1], none())

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
@attr('fixit')
def test_paste_invalid_command_2():
    # See issue #1238
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage1 = case.create_stage(':1:')
    stage2 = case.create_stage(':2:')
    text = \
"""
table = LIRE_TABLE(UNITE=1)
recu = RECU_FONCTION(TABLE=table)
"""
    comm2study(text, stage2)

    assert_that(stage1, has_length(0))
    assert_that(stage2, has_length(2))
    assert_that(stage2[0].name, equal_to('table'))
    assert_that(stage2[1].name, equal_to('recu'))

    #--------------------------------------------------------------------------
    content = str(stage2['recu'])
    stage1.paste(content)

    assert_that(stage1, has_length(1))
    assert_that(stage2, has_length(2))
    assert_that(stage1[0].name, equal_to('recu'))
    assert_that(stage2[0].name, equal_to('table'))
    assert_that(stage2[1].name, equal_to('recu'))
    assert_that(stage2[0] * stage[1], raises(AssertionError))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
@attr('fixit')
def test_paste_invalid_command_3():
    # See issue #1238
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case

    #--------------------------------------------------------------------------
    stage = case.create_stage(':1:')
    text = \
"""
recu = RECU_FONCTION(TABLE=table)
"""
    stage.paste(text)

    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to('recu'))

    #--------------------------------------------------------------------------
    pass

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
