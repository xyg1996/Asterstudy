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

from asterstudy.common import ConversionError
from asterstudy.common.conversion import TextProvider
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.command import Comment, Variable
from asterstudy.datamodel.general import ConversionLevel
from asterstudy.datamodel.history import History
from hamcrest import *


def test_syntaxerror():
    """Test for errors during imports"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
tab1 = CREA_TABLE(LISTE=_F(LISTE_R=[0.0, 1.0]
    PARA='DOMMAGE'))
"""
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "invalid syntax.*DOMMAGE"))
    assert_that(case, has_length(1))
    assert_that(stage, has_length(0))

    text = \
"""
tab1 = CREA_TABLE(LISTE=_F(LISTE_R=[0.0,
    PARA='DOMMAGE'))
"""
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "TokenError"))
    assert_that(case, has_length(1))
    assert_that(stage, has_length(0))


def test_partial_conv1():
    """Test for partial conversion with invalid keyword"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':first:')

    text = \
"""
MAIL_Q = LIRE_MAILLAGE()

MATER = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0),
    ELASTICITY=_F(E=30000.0, NU=0.2, RHO=2764.0)
)
"""
    strict = ConversionLevel.Any
    assert_that(calling(comm2study).with_args(text, stage, strict),
                raises(ConversionError, "Unauthorized keyword.*ELASTICITY"))
    assert_that(case, has_length(1))
    assert_that(stage, has_length(0))

    strict = strict | ConversionLevel.Partial
    comm2study(text, stage, strict)
    assert_that(case, has_length(2))
    assert_that(stage.is_graphical_mode())
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("MAIL_Q"))
    assert_that(case[1].name, ":first:_1")
    assert_that(case[1].is_text_mode())


def test_partial_conv2():
    """Test for syntaxerror and partial conversion"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':first:')

    text = \
"""
MAIL_Q = LIRE_MAILLAGE()

# missing comma
MATER = DEFI_MATERIAU(
    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0, SY=3.0)
    ELAS=_F(E=30000.0, NU=0.2, RHO=2764.0)
)
"""
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "invalid syntax.*near.*ELAS"))
    assert_that(case, has_length(1))
    assert_that(stage, has_length(0))

    comm2study(text, stage, strict=ConversionLevel.Partial)
    assert_that(case, has_length(2))
    assert_that(stage.is_graphical_mode())
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("MAIL_Q"))

    assert_that(case[1].name, ":first:_1")
    assert_that(case[1].is_text_mode())


def test_name_error():
    """Test for comp001h.comm: unnamed command"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':first:')
    text = \
"""
DEFI_MATERIAU(
    ECRO_PUIS=_F(A_PUIS=0.1,
                 N_PUIS=10.0,
                 SY=200000000.0, ),
    ELAS=_F(ALPHA=1.18e-05,
            E=2e+11,
            NU=0.3, ), )
"""
    assert_that(calling(comm2study).with_args(text, stage, True),
                raises(ConversionError, "NotImplementedError.*can not name"))
    assert_that(case, has_length(1))
    assert_that(stage, has_length(0))


def test_unauthorized_name():
    """Test for errors on command names"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':first:')
    text = \
"""
CALCUL = DEFI_MATERIAU(
    ECRO_PUIS=_F(A_PUIS=0.1,
                 N_PUIS=10.0,
                 SY=200000000.0, ),
    ELAS=_F(ALPHA=1.18e-05,
            E=2e+11,
            NU=0.3, ), )
"""
    strict = ConversionLevel.Any
    assert_that(calling(comm2study).with_args(text, stage, strict),
                raises(ConversionError, "Unauthorized name.*CALCUL"))
    assert_that(stage, has_length(0))

    strict = strict | ConversionLevel.Partial
    comm2study(text, stage, strict)
    assert_that(case, has_length(1))
    assert_that(stage.is_graphical_mode())
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("_"))


def test_multiple_errors():
    """Test for python and syntax errors"""
    # First, "unsupported Python statement" is detected,
    # then, "E is mandatory"
    # but only two stages should be created.
    history = History()
    case = history.current_case
    stage = case.create_stage(':first:')
    text = \
"""
mesh = LIRE_MAILLAGE()

mat = DEFI_MATERIAU(ELAS=_F(NU=0.3))

if True:
    DEBUG()
bad instruction
"""
    strict = ConversionLevel.Any
    assert_that(calling(comm2study).with_args(text, stage, strict),
                raises(ConversionError, "Python.*not be edited"))
    assert_that(stage, has_length(0))

    strict = strict | ConversionLevel.Partial
    comm2study(text, stage, strict)
    assert_that(case, has_length(2))
    assert_that(stage.is_graphical_mode())
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("mesh"))

    assert_that(case[1].is_text_mode())
    txt = case[1].get_text()
    assert_that(txt, contains_string("DEFI_MATERIAU"))
    assert_that(txt, contains_string("bad instruction"))


def test_issue_27362():
    history = History()
    case = history.current_case
    stage = case.create_stage(':first:')
    text = \
"""
mesh = LIRE_MAILLAGE()

mesh = MODI_MAILLAGE(MAILLAGE=mesh, YYY=XXX=9)
"""
    stage.use_text_mode()
    stage.set_text(text)

    strict = ConversionLevel.Any
    assert_that(calling(stage.use_graphical_mode).with_args(strict),
                raises(ConversionError, "invalid syntax"))

    text = stage.conversion_report.get_errors()
    assert_that(text, contains_string("invalid syntax"))


def test_include_auto():
    # Check automatic import of files with INCLUDE.
    history = History()
    case = history.current_case
    text = \
"""
mesh = LIRE_MAILLAGE()

INCLUDE(UNITE=4)

mat = DEFI_MATERIAU(ELAS=_F(E=young, NU=0.3))
"""
    incl = \
"""
young = 2.1e9
"""
    provider = TextProvider("")
    provider.add('unit:4', incl)

    strict = ConversionLevel.Any
    stage = case.create_stage(':1:')

    remaining = comm2study(text, stage, strict, provider)
    assert_that(case, has_length(3))
    assert_that(remaining, empty())

    stage = case[0]
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("mesh"))

    stage = case[1]
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage, has_length(1))
    assert_that(stage[0], instance_of(Variable))
    assert_that(stage[0].name, equal_to("young"))

    stage = case[2]
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("mat"))


def test_include_error_file():
    # Check automatic import of files with INCLUDE without any additional file.
    history = History()
    case = history.current_case
    text = \
"""
mesh = LIRE_MAILLAGE()

INCLUDE(UNITE=4)

mat = DEFI_MATERIAU(ELAS=_F(E=young, NU=0.3))
"""
    provider = TextProvider("")

    stage = case.create_stage(':1:')
    strict = ConversionLevel.Any
    assert_that(calling(comm2study).with_args(text, stage, strict, provider),
                raises(ConversionError, "KeyError: 'unit:4'"))
    assert_that(stage, has_length(1))
    del case[0]

    stage = case.create_stage(':1:')
    strict = strict | ConversionLevel.Partial
    remaining = comm2study(text, stage, strict, provider)
    assert_that(remaining, empty())
    assert_that(case, has_length(2))

    stage = case[0]
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("mesh"))

    assert_that(case[1].is_text_mode(), equal_to(True))
    last = case[1].get_text()
    assert_that(last, contains_string("INCLUDE(UNITE=4)"))
    assert_that(last, contains_string("DEFI_MATERIAU"))


def test_include_error_syntax_incl():
    # Check INCLUDE with failure in included stage.
    history = History()
    case = history.current_case
    text = \
"""
mesh = LIRE_MAILLAGE()

INCLUDE(UNITE=4)

mat = DEFI_MATERIAU(ELAS=_F(E=young, NU=0.3))
"""
    incl = \
"""
young = DEFI_CONSTANTE()
"""
    provider = TextProvider("")
    provider.add('unit:4', incl)


    stage = case.create_stage(':1:')
    strict = ConversionLevel.Any
    assert_that(calling(comm2study).with_args(text, stage, strict, provider),
                raises(ConversionError, "VALE is mandatory"))
    assert_that(stage, has_length(1))
    del case[0]

    stage = case.create_stage(':1:')
    strict = strict | ConversionLevel.Partial
    remaining = comm2study(text, stage, strict, provider)
    assert_that(remaining, empty())
    assert_that(case, has_length(3))

    stage = case[0]
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("mesh"))

    assert_that(case[1].is_text_mode(), equal_to(True))
    include = case[1].get_text()
    assert_that(include, contains_string("DEFI_CONSTANTE"))
    assert_that(case[2].is_text_mode(), equal_to(True))
    last = case[2].get_text()
    assert_that(last, contains_string("DEFI_MATERIAU"))


def test_include_error_syntax():
    # Check automatic import of files with INCLUDE with failure in third stage.
    history = History()
    case = history.current_case
    text = \
"""
mesh = LIRE_MAILLAGE()

INCLUDE(UNITE=4)

model = AFFE_MODELE(MAILLAGE=mesh,
                    AFFE=_F(TOUT='OUI',
                            PHENOMENE='MECANIQUE',
                            MODELISATION='3D'))

mat = DEFI_MATERIAU(ELAS=_F(E=young, NU=nu))
"""
    incl = \
"""
young = 2.1e9
"""
    provider = TextProvider("")
    provider.add('unit:4', incl)


    stage = case.create_stage(':1:')
    strict = ConversionLevel.Any
    remaining = comm2study(text, stage, strict, provider)
    assert_that(remaining, empty())
    assert_that(case, has_length(4))

    stage = case[0]
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("mesh"))

    stage = case[1]
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("young"))

    stage = case[2]
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage, has_length(1))
    assert_that(stage[0].name, equal_to("model"))

    stage = case[3]
    assert_that(stage.is_text_mode(), equal_to(True))
    last = stage.get_text()
    assert_that(last, contains_string("DEFI_MATERIAU"))


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
