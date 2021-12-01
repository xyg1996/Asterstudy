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

"""Automatic tests for conversion functions."""


import os
import os.path as osp
import unittest
from hamcrest import *

from testutils import attr

from asterstudy.common import CFG, ConversionError
from asterstudy.common.conversion import ConversionReport
from asterstudy.datamodel.history import History
from asterstudy.datamodel.catalogs import CATA
from asterstudy.datamodel.command import Variable
from asterstudy.datamodel.comm2study import comm2study, CommandBuilder
from asterstudy.datamodel.general import ConversionLevel
from asterstudy.datamodel.study2comm import study2comm
from testutils.tools import check_export, check_import, check_text_diff


# valid command files
VALID = {
    "test1": """
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

maya = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)

modele = AFFE_MODELE(AFFE=(_F(GROUP_MA='EFLUIDE',
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
                           _F(GROUP_MA='MASSPONC',
                              MODELISATION='2D_DIS_T',
                              PHENOMENE='MECANIQUE')),
                     INFO=2,
                     MAILLAGE=maya)

FIN()
""",
    "test2": r"""
long_expr = cos(pi / 3.) + \
            sin(pi / 3.)
""",
    "test3": """
x = cos(pi / 3.)

func = DEFI_FONCTION(NOM_PARA='INST',
                     VALE=(0.0, x))
""",
    "test4": """
vitesse = 1.e-5

t_0 = 5.e-2 / (8.0 * vitesse)

# liste d'archivage
c1 = DEFI_CONSTANTE(VALE=t_0)

# temps_ar=DEFI_LIST_REEL( VALE =[t_0*i for i in range(9)],)
""",
    "test5": """
vitesse = 1.e-5

t_0 = 625.0
""",
    # expected errors
    "error1": """
DEBUT(CODE=xx(NIV_PUB_WEB='INTERNET'))
""",
    "error2": """
func = DEFI_FONCTION(NOM_PARA='INST', VALE=(0., cos(pi/3)))
""",
    # Tests error3 & error4:
    # The results that are not stored in a simple Python variable are
    # only named when they are passed to another Command as arguments.
    # setitem/getitem would be necessary to walks in a Variable...
    # But storing results in non simple variables (list, dict, or more complex
    # objects...) is not supported.
    "error3": """
DEBUT()

mesh = [None]

mesh[0] = LIRE_MAILLAGE()

mod = AFFE_MODELE(
    AFFE=_F(PHENOMENE='MECANIQUE', MODELISATION='3D', TOUT='OUI'),
    MAILLAGE=mesh[0]
)

FIN()
""",
    "error4": """
DEBUT()

mesh = [None]

mesh[0] = LIRE_MAILLAGE()

mod = AFFE_MODELE(
    AFFE=_F(PHENOMENE='MECANIQUE', MODELISATION='3D', TOUT='OUI'),
    MAILLAGE=[mesh[0],]
)

FIN()
""",
}


def _clean_text(text):
    return text.replace(" ", "").replace("\n", "").replace("\\", "")

def _setup():
    """Common setup"""
    history = History()
    case = history.current_case
    return case.create_stage(':memory:')

def _test_conversion(testcase, strict_diff=True):
    """Import text, export newly created stage, compare text outputs."""
    stage = _setup()
    comm2study(VALID[testcase], stage)

    text = study2comm(stage)
    assert_that(check_import(text), equal_to(True))

    if strict_diff:
        assert_that(check_export(stage, VALID[testcase]), equal_to(True))
    else:
        assert_that(_clean_text(text), equal_to(_clean_text(VALID[testcase])))

    return stage

def test_command_test1():
    """Test for comm2study object on simple case"""
    _test_conversion("test1")

def test_conversion_error0():
    """Test for comm2study checkings"""
    stage = _setup()
    stage.use_text_mode()
    report = ConversionReport()
    assert_that(calling(CommandBuilder).with_args(stage, report),
                raises(TypeError, "must be in graphical mode"))
    assert_that(report.get_errors(), empty())

def test_conversion_error1():
    """Test for comm2study with errors"""
    stage = _setup()
    report = ConversionReport()
    builder = CommandBuilder(stage, report)
    assert_that(calling(builder.convert).with_args(VALID["error1"]),
                raises(ConversionError, "NameError.*xx"))
    assert_that(report.get_errors(), empty())

def test_conversion_test2():
    """Test for comm2study with a long expression"""
    _test_conversion("test2", strict_diff=False)

def test_conversion_error2():
    """Test for error because of an inlined expression"""
    # expression must be assigned to a variable
    assert_that(calling(_test_conversion).with_args("error2", False),
                raises(AssertionError, "0.0,0.5"))

def test_conversion_test3():
    """Test for comm2study with variable as keyword's value in list"""
    _test_conversion("test3")

def test_conversion_test4():
    """Test for comm2study with variable as keyword's value"""
    _test_conversion("test4")

def test_conversion_test5():
    """Test for comm2study with variables"""
    _test_conversion("test5")

def test_conversion_error3():
    """Test for processing a list of result"""
    assert_that(calling(_test_conversion).with_args("error3", False),
                raises(ConversionError, "NotImplementedError.*List of "))

def test_conversion_error4():
    """Test for processing a list of result"""
    assert_that(calling(_test_conversion).with_args("error4", False),
                raises(ConversionError, "NotImplementedError.*List of "))

def test_unicode():
    comm = osp.join(os.getenv('ASTERSTUDYDIR'),
                    'data', 'comm2study', 'unicode_strings.comm')
    with open(comm, 'rb') as file:
        textin = file.read()
    assert_that(check_import(textin), equal_to(True))

def test_unicode_8():
    comm = osp.join(os.getenv('ASTERSTUDYDIR'),
                    'data', 'comm2study', 'unicode_strings_utf8.comm')
    with open(comm, 'rb') as file:
        textin = file.read()
    assert_that(check_import(textin), equal_to(True))

def test_logical_unit():
    """Test conversion of UNITE keywords"""
    text = """
mesh = LIRE_MAILLAGE()

mesh21 = LIRE_MAILLAGE(UNITE=21)

mat = DEFI_MATERIAU(ELAS=_F(E=1.0, NU=0.3))

compo = DEFI_COMPOSITE(COUCHE=_F(EPAIS=0.1, MATER=mat))

EXEC_LOGICIEL(MAILLAGE=_F(FORMAT='SALOME'))
"""
    # default value in LIRE_MAILLAGE must be added [mesh] if not set [mesh21].
    # do not add keyword if default value is unauthorized [compo].
    # keyword under a factor keyword [EXEC_LOGICIEL].
    expected_output = """
mesh = LIRE_MAILLAGE(UNITE=20)

mesh21 = LIRE_MAILLAGE(UNITE=21)

mat = DEFI_MATERIAU(ELAS=_F(E=1.0,
                            NU=0.3))

compo = DEFI_COMPOSITE(COUCHE=_F(EPAIS=0.1,
                                 MATER=mat))

EXEC_LOGICIEL(MAILLAGE=_F(FORMAT='SALOME',
                          UNITE_GEOM=16))
"""
    stage = _setup()

    comm2study(text, stage)
    assert_that(check_export(stage, expected_output), equal_to(True))


def test_sdprod():
    """Test for conversion with sdprod using 0 key"""
    # see SyntaxUtils.{enable_0key,disable_0key} for details
    history = History()
    case = history.current_case
    stage = case.create_stage('part1')
    strict = ConversionLevel.Any

    # sdprod of CALC_FONCTION uses FFT[0].
    # Without enable_0key the conversion fails.
    text = \
"""
f1 = DEFI_FONCTION(NOM_PARA='ABSC', VALE=(0.0, 0.0, 1.0, 1.0))

fft2 = CALC_FONCTION(FRACTILE=_F(FONCTION=(f1, ), FRACT=1.))
"""
    comm2study(text, stage, strict)
    assert_that(stage, has_length(2))


def test_unnamed_reuse():
    """Test conversion of unnamed reuse"""
    # issue26725
    text = \
"""
Mail=LIRE_MAILLAGE()

MODI_MAILLAGE(reuse=Mail,
                   MAILLAGE=Mail,
                   ORIE_PEAU_2D=_F(GROUP_MA=('Group_2',),),)
"""
    expected_output = \
"""
Mail = LIRE_MAILLAGE(UNITE=20)

Mail = MODI_MAILLAGE(reuse=Mail,
                     MAILLAGE=Mail,
                     ORIE_PEAU_2D=_F(GROUP_MA=('Group_2', )))
"""
    stage = _setup()

    comm2study(text, stage)
    assert_that(stage, has_length(2))
    modi = stage[1]
    assert_that(modi.name, equal_to("Mail"))
    assert_that(check_export(stage, expected_output), equal_to(True))


def test_var_dble():
    """Test for conversion of variables"""
    # issue26725
    text = \
"""
Epdalle = 25.0E-02;NbCouche=5
"""
    expected_output = \
"""
Epdalle = 25.0E-02

NbCouche = 5
"""
    stage = _setup()

    comm2study(text, stage)
    assert_that(stage, has_length(2))
    assert_that(stage[0].name, equal_to("Epdalle"))
    assert_that(stage[0], instance_of(Variable))
    assert_that(stage[1].name, equal_to("NbCouche"))
    assert_that(stage[1], instance_of(Variable))
    assert_that(check_export(stage, expected_output), equal_to(True))


def test_limited_value():
    """Test for export with limitation on values"""
    text = \
"""
inst = DEFI_LIST_REEL(VALE=(1., 2., 3., 4.))
"""
    expected_output = {
        0: """
inst = DEFI_LIST_REEL(VALE=(1.0, 2.0, 3.0, 4.0))
""",
        2: """
inst = DEFI_LIST_REEL(VALE=(1.0, 2.0, ...))

# sequences have been limited to the first 2 occurrences.
""",
        4: """
inst = DEFI_LIST_REEL(VALE=(1.0, 2.0, 3.0, 4.0))
""",
    }
    stage = _setup()

    comm2study(text, stage)
    assert_that(stage, has_length(1))
    defi = stage[0]
    assert_that(defi.name, equal_to("inst"))
    defi.check(safe=False)

    for limit, expected in expected_output.items():
        output = study2comm(stage, limit=limit)
        assert_that(check_text_diff(output, expected), equal_to(True))


def test_limited_factor():
    """Test for export with limitation on factor keywords"""
    text = \
"""
DETRUIRE(OBJET=(_F(CHAINE='OB1'), _F(CHAINE='OB2'), _F(CHAINE='OB3'), _F(CHAINE='OB4'), ))
"""
    expected_output = {
        0: """
DETRUIRE(OBJET=(_F(CHAINE='OB1'),
                _F(CHAINE='OB2'),
                _F(CHAINE='OB3'),
                _F(CHAINE='OB4')))
""",
        2: """
DETRUIRE(OBJET=(_F(CHAINE='OB1'),
                _F(CHAINE='OB2'), ...))

# sequences have been limited to the first 2 occurrences.
""",
        4: """
DETRUIRE(OBJET=(_F(CHAINE='OB1'),
                _F(CHAINE='OB2'),
                _F(CHAINE='OB3'),
                _F(CHAINE='OB4')))
""",
    }
    stage = _setup()

    comm2study(text, stage)
    assert_that(stage, has_length(1))
    detr = stage[0]
    assert_that(detr.name, equal_to("_"))
    detr.check(safe=False)

    for limit, expected in expected_output.items():
        output = study2comm(stage, limit=limit)
        assert_that(check_text_diff(output, expected), equal_to(True))


def test_26683():
    """Test for split with unicode strings"""
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comm = osp.join(os.getenv('ASTERSTUDYDIR'),
                              'data', 'export',
                              'traction_aggregats_direct.comm')
    with open(comm, "rb") as file:
        text = file.read()
    strict = ConversionLevel.Any
    assert_that(calling(comm2study).with_args(text, stage, strict),
                raises(ConversionError, "Python.*not be edited"))
    assert_that(stage, has_length(0))

    strict = strict | ConversionLevel.Partial
    comm2study(text, stage, strict)
    assert_that(case, has_length(2))
    assert_that(stage.is_graphical_mode())
    assert_that(stage, has_length(49))


def test_26683_export():
    text = \
"""
v00 = 0
v01 = 1
v02 = 2 * v01 + v00
v03 = 3 * v02
v04 = 4
"""
# v05 = 5
# v06 = 6
# v07 = 7
# v08 = 8
# v09 = 9
# v10 = 10
# v11 = 11
# v12 = 12
# v13 = 13
# v14 = 14
# # v15 = 15
# # v16 = 16
# """
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    strict = ConversionLevel.Any
    comm2study(text, stage, strict)

    stage.use_text_mode()


def test_1316():
    text = \
"""
vitesse = 1.e-5

t_0 = 5.e-2 / (8.0 * vitesse)

c1 = DEFI_CONSTANTE(VALE=t_0)
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(3))

    case = stage.parent_case
    stage = case.create_stage(':2:')
    text = \
"""
t_2 = t_0 + 375
"""
    comm2study(text, stage)
    assert_that(stage, has_length(1))


def test_remove_identifier():
    text = \
"""
LIRE_MAILLAGE(identifier=123)
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))

    output = study2comm(stage).strip()
    expected = "LIRE_MAILLAGE(UNITE=20)"
    assert_that(check_text_diff(output, expected), equal_to(True))

    output = study2comm(stage, add_ids=True, format_id="{id}:99").strip()
    expected = ("LIRE_MAILLAGE(identifier='0:99',\n"
                "              UNITE=20)\n")
    assert_that(check_text_diff(output, expected), equal_to(True))


def test_hidden_keywords():
    text = \
"""
mesh = LIRE_MAILLAGE()

model = AFFE_MODELE(MAILLAGE=mesh,
                    AFFE=(_F(MAILLE='M14',
                             MODELISATION='3D',
                             PHENOMENE='MECANIQUE')))

mat = DEFI_MATERIAU(ELAS=_F(E=1.0, NU=0.3))

chmat=AFFE_MATERIAU(MAILLAGE=mesh,
                    AFFE=(_F(MAILLE='M1',
                            MATER=mat),
                          _F(MAILLE='M2',
                             MATER=mat)))
"""
    report = ConversionReport()
    stage = _setup()
    comm2study(text, stage, report=report)
    assert_that(stage, has_length(4))

    assert_that(report.get_errors(), empty())
    assert_that(report.get_warnings(),
                contains_string("NOEUD/MAILLE in AFFE_MODELE"))
    warn = [i for i in report.iter_warnings()]
    assert_that(warn, has_length(2))


def test_include_materiau():
    text = """INCLUDE_MATERIAU(FICHIER='efica01a.data')"""
    report = ConversionReport()
    stage = _setup()
    comm2study(text, stage, report=report)
    assert_that(stage, has_length(1))

    assert_that(report.get_errors(), empty())
    assert_that(report.get_warnings(),
                contains_string("INCLUDE_MATERIAU(FICHIER="))
    warn = [i for i in report.iter_warnings()]
    assert_that(warn, has_length(1))


def test_1773():
    stage = _setup()
    stage.add_command('LIRE_MAILLAGE', 'mesh')
    assert_that(stage['mesh'].active, equal_to(True))

    stage['mesh'].active = False
    assert_that(stage['mesh'].active, equal_to(False))

    text = study2comm(stage, pretty=False)

    stage = _setup()
    comm2study(text, stage)
    assert_that(stage['mesh'].active, equal_to(False))


def test_variable_ot():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    comm = osp.join(os.getenv('ASTERSTUDYDIR'), 'data', 'export', 'poutre.comm')
    with open(comm, "rb") as file:
        text = file.read()
    strict = ConversionLevel.Any
    # fails in AFFE_CARA_ELEM sdprod multiplying h and ep
    assert_that(calling(comm2study).with_args(text, stage, strict),
                raises(ConversionError, "unsupported operand type"))
    assert_that(stage, has_length(0))

    strict = strict | ConversionLevel.Partial
    comm2study(text, stage, strict)
    assert_that(case, has_length(2))
    assert_that(stage.is_graphical_mode())
    assert_that(stage, has_length(7))
    stage2 = case[1]
    assert_that(stage2.is_text_mode())

    # remove stages
    stage.delete()
    stage = case.create_stage(':memory:')
    assert_that(case, has_length(1))

    # but GUI (Study.load_ajs) does
    strict = ConversionLevel.Partial
    comm2study(text, stage, strict)
    assert_that(case, has_length(1))
    assert_that(stage.is_graphical_mode())
    assert_that(stage, has_length(17))


def test_forma30b():
    comm = osp.join(os.getenv('ASTERSTUDYDIR'),
                    'data', 'comm2study', 'forma_reuse.comm')
    with open(comm, 'rb') as fobj:
        text = fobj.read()

    report = ConversionReport()
    stage = _setup()
    comm2study(text, stage, report=report)
    crea_resu = stage.sorted_commands[-1]
    assert_that(crea_resu.title, equal_to('CREA_RESU'))

    assert_that(report.get_warnings(),
                contains_string("using the right instance"))
    assert_that(report.get_warnings(),
                contains_string("without setting the result object"))


def test_wizcw():
    comm = osp.join(os.getenv('ASTERSTUDYDIR'),
                    'data', 'comm2study', 'wizcw_reuse.comm')
    with open(comm, 'rb') as fobj:
        text = fobj.read()

    report = ConversionReport()
    stage = _setup()
    comm2study(text, stage, report=report)
    assert_that(report.get_warnings(), empty())


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
