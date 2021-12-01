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


from math import sqrt, pi
import unittest
import re
from hamcrest import *

from asterstudy.common import ConversionError
from asterstudy.datamodel.history import History
from asterstudy.datamodel.catalogs import CATA
from asterstudy.datamodel.general import ConversionLevel


def comm2study(content, stage):
    from asterstudy.datamodel.comm2study import comm2study as engine
    return engine(content, stage, strict=ConversionLevel.Syntaxic)

cata = \
"""
MACRO(
    nom="FAKECMD",
    op=None,
    sd_prod=None,

    TYPE=SIMP(statut='f', typ='TXM', into=("TYPE1", "TYPE2"), defaut="TYPE1"),
    OPTION=SIMP(statut='f', typ='TXM', into=("OPT1", "OPT2")),

    FACTKW0=FACT(statut='f',
        INKW0=SIMP(statut='f', typ='I'),
    ),

    FACTKW0A=FACT(statut='f',
        INKW0A=SIMP(statut='o', typ='I'),
    ),

    b_type1=BLOC(condition='TYPE == "TYPE1"',
        INKW1=SIMP(statut='f', typ='I'),
        FACTKW1=FACT(statut='f',
            b_option=BLOC(condition='OPTION == "OPT1"',
                NB=SIMP(statut='f', typ='I', defaut=10),
            ),
        ),
    ),

    b_type2=BLOC(condition='TYPE == "TYPE2"',
        INKW2=SIMP(statut='o', typ='I'),
        FACTKW2=FACT(statut='f',
            NMAX_FREQ=SIMP(statut='f', typ='I', val_min=0),
        ),
    ),

    VALE=SIMP(statut='f', typ='R', val_min=0., val_max=1.),
    VALD=SIMP(statut='f', typ='R', defaut=9, validators=NotEqualTo(12.34)),
    INST=SIMP(statut='f', typ='R', min=2, max=3),
    VALC=SIMP(statut='f', typ='C'),

    FACTKW0B=FACT(statut='f',
        b_type1=BLOC(condition='TYPE == "TYPE1"',
            INKW0B1=SIMP(statut='f', typ='R'),
            b_opt1=BLOC(condition='OPTION == "OPT1"',
                INKW0B2=SIMP(statut='f', typ='TXM', into=("OUI", "NON"), defaut="OUI"),
            ),
        ),
    ),

    KVAL=SIMP(statut='f', typ='TXM', validators=(NoRepeat(), LongStr(1, 16))),
    KVALA=SIMP(statut='f', typ='TXM', validators=AndVal(LongStr(1, 8), LongStr(4, 12))),
    KVALO=SIMP(statut='f', typ='TXM', validators=OrVal(Compulsory(['a', 'b']), Compulsory(['b', 'c']))),
    KVALS=SIMP(statut='f', typ='I', validators=OrdList()),
    KVALD=SIMP(statut='f', typ='I', validators=OrdList(reverse=True)),
    KVALT=SIMP(statut='f', typ='TXM', validators=Together(['a', 'b'])),
    KVALB=SIMP(statut='f', typ='TXM', validators=Absent(['a', 'b'])),
    KVALC=SIMP(statut='f', typ='TXM', validators=Compulsory(['a', 'b'])),

    VMAX=SIMP(statut='f', typ='I', max='**'),
)
"""

def _setup():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    # hack the catalog a test command
    syn = CATA.package("Syntax")
    fakecmd = eval(cata, syn.__dict__)
    CATA._catalogs["FAKECMD"] = fakecmd
    return stage


#------------------------------------------------------------------------------
# test_bXX: on block and optional/mandatory
def test_b01():
    """Test for optional keywords"""
    text = \
"""
FAKECMD()
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['OPTION'].value, none())
    cmd.check(safe=False)
    # TODO: is it normal that the value is not init to default?
    assert_that(cmd['VALD'].value, none())
    # assert_that(cmd['VALD'].value, equal_to(9))

def test_b02():
    """Test for optional under a factor keyword"""
    text = \
"""
FAKECMD(FACTKW0=_F(INKW0=0))
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['FACTKW0']['INKW0'].value, equal_to(0))
    cmd.check(safe=False)

def test_b03():
    """Test for empty factor keyword"""
    text = \
"""
FAKECMD(FACTKW0=_F())
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['FACTKW0'].undefined(), equal_to(False))
    assert_that(cmd['FACTKW0'].keys(), has_length(0))
    # TODO: command.KeysMixing._getitem should init Factor._storage to None
    # assert_that(cmd['FACTKW0A'].undefined(), equal_to(True))
    cmd.check(safe=False)

def test_b04():
    """Test for mandatory keywords under a factor keyword"""
    text = \
"""
FAKECMD(FACTKW0A=_F())
"""
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "KeyError.*INKW0A is mandatory"))

def test_b05():
    """Test for block enabled by a default value"""
    text = \
"""
FAKECMD(INKW1=5)
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['INKW1'].value, equal_to(5))

def test_b06():
    """Test for disabled block"""
    text = \
"""
FAKECMD(INKW2=5)
"""
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError,
                       "INKW2.*Unauthorized keyword.*INKW2"))
    assert_that(stage, has_length(0))

def test_b07():
    """Test for mandatory keyword under a block"""
    text = \
"""
FAKECMD(TYPE="TYPE2")
"""
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "KeyError.*INKW2 is mandatory"))
    assert_that(stage, has_length(0))

def test_b08():
    """Test for available keyword under a block"""
    text = \
"""
FAKECMD(TYPE="TYPE2", INKW2=5)
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['TYPE'].value, equal_to("TYPE2"))
    assert_that(cmd['INKW2'].value, equal_to(5))

def test_b09():
    """Test for available keyword under a block with nested conditions"""
    text = \
"""
FAKECMD(TYPE="TYPE1", OPTION="OPT1",
        FACTKW1=_F(NB=5))
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['TYPE'].value, equal_to("TYPE1"))
    assert_that(cmd['FACTKW1'].keys(), has_length(1))
    assert_that(cmd['FACTKW1']['NB'], equal_to(5))

def test_b10():
    """Test for available keyword under two consecutive nested blocks"""
    text = \
"""
FAKECMD(TYPE="TYPE1", OPTION="OPT1",
        FACTKW0B=_F(INKW0B1=0., INKW0B2="OUI"))
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['TYPE'].value, equal_to("TYPE1"))
    assert_that(cmd['FACTKW0B'].keys(), has_length(2))
    assert_that(cmd['FACTKW0B']['INKW0B1'], equal_to(0))
    assert_that(cmd['FACTKW0B']['INKW0B2'], equal_to("OUI"))

#------------------------------------------------------------------------------
# test_aXX: on attributes
def test_a20():
    """Test for into ok"""
    text = \
"""
FAKECMD(TYPE="TYPE1")
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['TYPE'].value, equal_to("TYPE1"))
    cmd.check(safe=False)

def test_a21():
    """Test for into nook"""
    text = \
"""
FAKECMD(TYPE="TYPE3")
"""
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "TYPE.*TYPE1.*TYPE2"))
    assert_that(stage, has_length(0))

def test_a22():
    """Test for val_min ok"""
    text = \
"""
FAKECMD(VALE=0.)
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['VALE'].value, equal_to(0.))
    cmd.check(safe=False)

def test_a23():
    """Test for val_max ok"""
    text = \
"""
FAKECMD(VALE=1.)
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['VALE'].value, equal_to(1.))
    cmd.check(safe=False)

def test_a24():
    """Test for val_min nook"""
    text = \
"""
FAKECMD(VALE=-0.5)
"""
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError,
                       "VALE.*Value must be bigger than 0"))
    assert_that(stage, has_length(0))

def test_a25():
    """Test for val_max nook"""
    text = \
"""
FAKECMD(VALE=100.)
"""
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError,
                       "VALE.*Value must be smaller than 1"))
    assert_that(stage, has_length(0))

def test_a26():
    """Test for val_min with a variable"""
    text = \
"""
value = 0.3

FAKECMD(VALE=value)
"""
    stage = _setup()
    # at conversion, value/type of variable can not be checked...
    comm2study(text, stage)
    assert_that(stage, has_length(2))
    cmd = stage[1]
    var = cmd['VALE'].value
    assert_that(var.evaluation, equal_to(0.3))
    # ... but it can be checked now!
    cmd.check(safe=False)

def test_a27():
    """Test for val_min with an invalid variable"""
    text = \
"""
value = "bad type"

FAKECMD(VALE=value)
"""
    stage = _setup()
    # at conversion, value/type of variable can not be checked...
    comm2study(text, stage)
    assert_that(stage, has_length(2))
    cmd = stage[1]
    var = cmd['VALE'].value
    assert_that(var.evaluation, equal_to("bad type"))
    # ... but it can be checked now!
    CH = CATA.package("SyntaxChecker")
    try:
        cmd.check(safe=False)
    except CH.CheckerError as exc:
        assert_that(re.search("Unexpected type.*str.*float", exc.msg),
                    is_not(none()))
    assert_that(calling(cmd.check).with_args(safe=False),
                raises(CH.CheckerError))

def test_a28():
    """Test for min/max ok"""
    text = \
"""
FAKECMD(INST=(0., 1.))
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['INST'].value, contains(0., 1.))
    # ... but it can be checked now!
    cmd.check(safe=False)

def test_a29():
    """Test for min nook"""
    text = \
"""
FAKECMD(INST=0.)
"""
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "INST.*At least 2 values"))
    assert_that(stage, has_length(0))

def test_a30():
    """Test for max nook"""
    text = \
"""
FAKECMD(INST=[0., 1., 2., 3.])
"""
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "INST.*At most 3 values"))
    assert_that(stage, has_length(0))

def test_a31():
    """Test for typ nook"""
    text = \
"""
FAKECMD(VALE='a')
"""
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError,
                       "Unexpected.*<class 'str'>.*"
                       "expecting.*<class 'int'>"))
    assert_that(stage, has_length(0))

def test_a32():
    """Test for max=**"""
    text = \
"""
FAKECMD(VMAX=(5, 4))

FAKECMD(VMAX=9)
"""
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(2))
    cmd = stage[0]
    assert_that(cmd['VMAX'].value, contains(5, 4))
    cmd.check(safe=False)

    cmd = stage[1]
    assert_that(cmd['VMAX'].value, equal_to(9))
    cmd.check(safe=False)


#------------------------------------------------------------------------------
# test_vXX: validators
def test_v01():
    """Test for ok with NoRepeat"""
    text = "FAKECMD(KVAL=('a', 'b'))"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['KVAL'].value, contains("a", "b"))
    cmd.check(safe=False)

def test_v02():
    """Test for nook with NoRepeat"""
    text = "FAKECMD(KVAL=('a', 'b', 'a'))"
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "ValueError.*different"))

def test_v03():
    """Test for nook with LongStr"""
    text = "FAKECMD(KVAL='x' * 17)"
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "ValueError.*String length.*17"))

def test_v04():
    """Test for ok with AndVal"""
    text = "FAKECMD(KVALA='abcdefgh')"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['KVALA'].value, has_length(8))
    cmd.check(safe=False)

def test_v05():
    """Test for nook with AndVal"""
    text = "FAKECMD(KVALA='abc')"
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "ValueError.*String length.*4, 12.*3"))

def test_v06():
    """Test for ok with OrVal"""
    text = "FAKECMD(KVALO=('a', 'b', 'd'))"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['KVALO'].value, has_length(3))
    assert_that(cmd['KVALO'].value, has_items("a", "b"))
    assert_that(cmd['KVALO'].value, is_not(has_items("b", "c")))
    cmd.check(safe=False)

def test_v07():
    """Test for nook with OrVal"""
    text = "FAKECMD(KVALO=('a', 'c'))"
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "ValueError.*"
                       "Validator.*OR.*invalid.*"
                       "Required values.*'a', 'b'.*"
                       "Required values.*'b', 'c'"))

def test_v08():
    """Test for ok with OrdList"""
    text = "FAKECMD(KVALS=(1, 2, 3, 4))"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['KVALS'].value, has_length(4))
    cmd.check(safe=False)

def test_v09():
    """Test for nook with OrdList"""
    text = "FAKECMD(KVALS=(1, 2, 0))"
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "ValueError.*"
                       "not ordered as expected.*2 followed by 0"))

def test_v10():
    """Test for ok with decreasing OrdList"""
    text = "FAKECMD(KVALD=(4, 3, 2, 1))"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['KVALD'].value, has_length(4))
    cmd.check(safe=False)

def test_v11():
    """Test for nook with decreasing OrdList"""
    text = "FAKECMD(KVALD=(1, 2, 0))"
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "ValueError.*"
                       "not ordered as expected.*1 followed by 2"))

def test_v12():
    """Test for ok with Together"""
    text = "FAKECMD(KVALT=('a', 'b', 'c'))"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['KVALT'].value, has_length(3))
    cmd.check(safe=False)

def test_v12b():
    """Test for ok with Together"""
    text = "FAKECMD(KVALT=('c', 'd'))"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['KVALT'].value, has_length(2))
    cmd.check(safe=False)

def test_v13():
    """Test for nook with Together"""
    text = "FAKECMD(KVALT=('a', 'c'))"
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "ValueError.*"
                       "Missing values:.*'b'"))

def test_v14():
    """Test for ok with Absent"""
    text = "FAKECMD(KVALB=('c', 'd', 'e'))"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['KVALB'].value, has_length(3))
    cmd.check(safe=False)

def test_v15():
    """Test for nook with Absent"""
    text = "FAKECMD(KVALB=('a', 'b', 'c'))"
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "ValueError.*"
                       "Unexpected values:.*('a', 'b'|'b', 'a')"))

def test_v16():
    """Test for ok with Compulsory"""
    text = "FAKECMD(KVALC=('a', 'b', 'c'))"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['KVALC'].value, has_length(3))
    cmd.check(safe=False)

def test_v17():
    """Test for nook with Compulsory"""
    text = "FAKECMD(KVALC=('c', 'd'))"
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "ValueError.*"
                       "Required values:.*('a', 'b'|'b', 'a').*"
                       "missing.*('a', 'b'|'b', 'a')"))

def test_v18():
    """Test for ok with NotEqualTo"""
    text = "FAKECMD(VALD=1.)"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['VALD'].value, equal_to(1.))
    cmd.check(safe=False)

def test_v19():
    """Test for nook with NotEqualTo"""
    text = "FAKECMD(VALD=12.34)"
    stage = _setup()
    assert_that(calling(comm2study).with_args(text, stage),
                raises(ConversionError, "ValueError.*"
                       "Unauthorized value:.*12.34"))

def test_v20():
    """Test for complex type"""
    text = "FAKECMD(VALC=sqrt(3) + 1j)"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['VALC'].value.real, close_to(sqrt(3.0), 1.e-8))
    assert_that(cmd['VALC'].value.imag, close_to(1.0, 1.e-8))

def test_v21():
    """Test for complex type (old syntax)"""
    text = "FAKECMD(VALC=('RI', sqrt(3.), 1.))"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['VALC'].value.real, close_to(sqrt(3.0), 1.e-8))
    assert_that(cmd['VALC'].value.imag, close_to(1.0, 1.e-8))

def test_v22():
    """Test for complex type (old syntax)"""
    text = "FAKECMD(VALC=('MP', 2., 30.))"
    stage = _setup()
    comm2study(text, stage)
    assert_that(stage, has_length(1))
    cmd = stage[0]
    assert_that(cmd['VALC'].value.real, close_to(sqrt(3.0), 1.e-8))
    assert_that(cmd['VALC'].value.imag, close_to(1.0, 1.e-8))

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
