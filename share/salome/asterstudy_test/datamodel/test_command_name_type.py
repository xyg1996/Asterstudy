# -*- coding: utf-8 -*-

# Copyright 2016-2018 EDF R&D
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


import unittest
from hamcrest import *

from asterstudy.datamodel import CATA, History
from asterstudy.datamodel.command import CO, Command, Hidden
from asterstudy.datamodel.general import ConversionLevel
from asterstudy.datamodel.comm2study import comm2study

from testutils import attr


def dump(c):
    print()
    print('--------------------------------')
    print(c)
    print(c.name)
    print(c.type)
    print(c.safe_type())
    print(c.gettype(ConversionLevel.NoFail))
    print(c.printable_type)


@attr('fixit')
def test_name_type():
    """Test for printable_type"""
    history = History()
    stage = history.current_case.create_stage()

    stage.add_command('ASSEMBLAGE')

    assert_that(stage[0].name, equal_to('unnamed'))
    # the following check does not work: result may be different (depending on what?)
    assert_that(stage[0].type, is_not(none()))
    assert_that(stage[0].safe_type(), is_not(none()))
    assert_that(stage[0].gettype(ConversionLevel.NoFail), is_not(none()))
    # the following check does not work: result may be different (depending on what?)
    assert_that(stage[0].printable_type, equal_to('nume_ddl_sdaster')) # what typename should be here?


def test_orphan_hidden():
    # there is no difference before and after conversion
    history = History()
    stage = history.current_case.create_stage()

    stage.add_command('ASSEMBLAGE').init({'NUME_DDL':CO('aaa')})

    assert_that(stage, has_length(2))
    assert_that(stage.get_text().strip(), equal_to("ASSEMBLAGE(NUME_DDL=CO('aaa'))"))
    assert_that(stage[1].name, equal_to('aaa'))
    assert_that(stage[1], is_(Hidden))
    assert_that(stage[1].name, equal_to('aaa'))

    stage.use_text_mode()
    stage.use_graphical_mode(strict=ConversionLevel.Partial)

    assert_that(history.current_case, has_length(1))
    assert_that(history.current_case[0], is_(stage))

    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage, has_length(2))
    assert_that(stage[0].title, equal_to('ASSEMBLAGE'))
    assert_that(stage[1], is_(Hidden))
    assert_that(stage[1].name, equal_to('aaa'))
    assert_that(stage.get_text().strip(), equal_to("ASSEMBLAGE(NUME_DDL=CO('aaa'))"))


def test_partial_conversion():
    """Test for partial conversion"""
    # use case 1
    history1 = History()
    stage = history1.current_case.create_stage()
    text = """
ASSEMBLAGE(NUME_DDL=CO('aaa'))
"""
    # in GUI, there's a warning; answering 'Yes' creates one stage
    comm2study(text, stage, strict=ConversionLevel.Partial)
    assert_that(history1.current_case, has_length(1))

    # use case 2

    history2 = History()
    stage = history2.current_case.create_stage()
    text = """
ASSEMBLAGE(NUME_DDL=CO('aaa'),
           VECT_ASSE=_F(OPTION='',
                        VECTEUR=CO(u'bbb')))
"""
    # in GUI, there's a warning; answering 'Yes' creates one stage
    comm2study(text, stage, strict=ConversionLevel.Partial)
    assert_that(history2.current_case, has_length(1))


def test_name_type_assemblage():
    """Test for name and type management"""
    history = History()
    stage = history.current_case.create_stage()
    ds = CATA.package('DataStructure')

    stage.add_command('LIRE_MAILLAGE').init({'UNITE':20})
    stage.add_command('AFFE_MODELE').init({'AFFE':(), 'MAILLAGE':stage[0]})
    stage.add_command('ASSEMBLAGE').init({'MODELE':stage[1]})

    assert_that(stage, has_length(3))
    assert_that(stage[2].name, equal_to('_')) # returns nothing
    assert_that(stage[2].type, none())
    assert_that(stage[2].safe_type(), none())
    assert_that(stage[2].gettype(ConversionLevel.NoFail), none())
    assert_that(stage[2].printable_type, equal_to(''))

    assert_that(Command.filterby(stage, getattr(ds, 'nume_ddl_sdaster')), has_length(0))
    assert_that(Command.filterby(stage, getattr(ds, 'matr_asse_pres_c')), has_length(0))
    assert_that(Command.filterby(stage, getattr(ds, 'cham_no_sdaster')), has_length(0))

    # -

    stage[2].init({'MODELE':stage[1],
                   'NUME_DDL':CO('aaa')})

    assert_that(stage, has_length(4))
    assert_that(stage[2].name, equal_to('_')) # returns nothing
    assert_that(stage[2].type, none())
    assert_that(stage[2].safe_type(), none())
    assert_that(stage[2].gettype(ConversionLevel.NoFail), none())
    assert_that(stage[2].printable_type, equal_to(''))

    assert_that(stage[3].name, equal_to('aaa'))
    assert_that(stage[3].type, none()) # ???
    assert_that(stage[3].safe_type(), is_not(none())) # ???
    assert_that(stage[3].gettype(ConversionLevel.NoFail), is_not(none())) # ???
    assert_that(stage[3].printable_type, equal_to('')) # ???!!!

    assert_that(Command.filterby(stage, getattr(ds, 'nume_ddl_sdaster')), has_length(0)) # why ? there should be 1 item
    assert_that(Command.filterby(stage, getattr(ds, 'matr_asse_pres_c')), has_length(0))
    assert_that(Command.filterby(stage, getattr(ds, 'cham_no_sdaster')), has_length(0))

    # -

    stage[2].init({'MODELE':stage[1],
                   'NUME_DDL':CO('aaa'),
                   'VECT_ASSE':{'VECTEUR':CO('bbb'), 'OPTION':'CHAR_MECA',},
                   'MATR_ASSE':{'MATRICE':CO('ccc'), 'OPTION':'AMOR_ACOU',},})

    assert_that(stage, has_length(6))
    assert_that(stage[2].name, equal_to('_')) # returns nothing
    assert_that(stage[2].type, none())
    assert_that(stage[2].safe_type(), none())
    assert_that(stage[2].gettype(ConversionLevel.NoFail), none())
    assert_that(stage[2].printable_type, equal_to(''))

    assert_that(stage[3].name, equal_to('aaa'))
    assert_that(stage[3].type, none()) # ???
    assert_that(stage[3].safe_type(), is_not(none())) # ???
    assert_that(stage[3].gettype(ConversionLevel.NoFail), is_not(none())) # ???
    assert_that(stage[3].printable_type, equal_to('')) # ???!!!
    assert_that(stage[4].name, equal_to('bbb'))
    assert_that(stage[4].type, none()) # ???
    assert_that(stage[4].safe_type(), is_not(none())) # ???
    assert_that(stage[4].gettype(ConversionLevel.NoFail), is_not(none())) # ???
    assert_that(stage[4].printable_type, equal_to('')) # ???!!!
    assert_that(stage[5].name, equal_to('ccc'))
    assert_that(stage[5].type, none()) # ???
    assert_that(stage[5].safe_type(), is_not(none())) # ???
    assert_that(stage[5].gettype(ConversionLevel.NoFail), is_not(none())) # ???
    assert_that(stage[5].printable_type, equal_to('')) # ???!!!

    assert_that(Command.filterby(stage, getattr(ds, 'nume_ddl_sdaster')), has_length(0)) # why ? there should be 1 item
    assert_that(Command.filterby(stage, getattr(ds, 'matr_asse_pres_c')), has_length(1)) # !!!
    assert_that(Command.filterby(stage, getattr(ds, 'matr_asse_pres_c'))[0].name, equal_to('ccc')) # !!!
    assert_that(Command.filterby(stage, getattr(ds, 'cham_no_sdaster')), has_length(1)) # !!!
    assert_that(Command.filterby(stage, getattr(ds, 'cham_no_sdaster'))[0].name, equal_to('bbb')) # !!!

    stage.use_text_mode()
    stage.use_graphical_mode(strict=ConversionLevel.Partial)

    assert_that(history.current_case, has_length(1))
    assert_that(stage, has_length(6))

    return
    # fixit:
    # Problems:
    # - the order of additional results of macro-commands is not stable.
    # - few lines above it should find a nume_ddl.

    assert_that(stage[2].name, equal_to('_')) # ??? why it is '_' now ?
    assert_that(stage[3].name, equal_to('aaa'))
    assert_that(stage[4].name, equal_to('bbb'))
    assert_that(stage[5].name, equal_to('ccc'))

    assert_that(Command.filterby(stage, getattr(ds, 'nume_ddl_sdaster')), has_length(1)) # it is OK now, but why?
    assert_that(Command.filterby(stage, getattr(ds, 'nume_ddl_sdaster'))[0].name, equal_to('aaa')) # !!!
    assert_that(Command.filterby(stage, getattr(ds, 'matr_asse_pres_c')), has_length(1)) # !!!
    assert_that(Command.filterby(stage, getattr(ds, 'matr_asse_pres_c'))[0].name, equal_to('ccc')) # !!!
    assert_that(Command.filterby(stage, getattr(ds, 'cham_no_sdaster')), has_length(1)) # !!!
    assert_that(Command.filterby(stage, getattr(ds, 'cham_no_sdaster'))[0].name, equal_to('bbb')) # !!!


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

################################################################################
#
# Comments to these tests.
#
# 1. test_name_type() gives different typename each time when running.
#    Uncomment last line to see that.
#    I had the following types when running this test several times:
#    1st run: 'nume_ddl_sdaster'
#    2nd run: 'cham_no_sdaster'
#    3rd run: 'matr_asse_depl_c'
#    4th run: 'matr_asse_temp_r'
#    etc...
#
#    Is this normal?
#
#-------------------------------------------------------------------------------
#
# 2. test_orphan_hidden() shows how an orphan Hidden commands may be created
#    => fixed
#
#-------------------------------------------------------------------------------
#
# 3. test_partial_conversion() shows inconsistent behavior of partial conversion.
#    Both cases contain incomplete command's initialization - both these stages
#    show the same warning message in GUI saying that stage is invalid and asking
#    the user either it's necessary to create a graphical stage with valid commands
#    and put other commands into additional text stage.
#    However, first use case creates two stages while second use case creates only
#    one graphical stage (i.e. conversion succeedes!).
#
#    Is this normal?
#
#    => The types can not be defined because some keywords are missing.
#       Now, only one text stage is created with these commands.
#
#-------------------------------------------------------------------------------
#
# 4. test_name_type_assemblage() demonstrates inconsistent and sophisticated
#    control over name and type of the command by data model. As there's no clear
#    understanding what method to use, different elements of GUI use different
#    methods of Command class causing inconsistent and unclear behavior of the
#    application.
#
#    [Additional hint]
#    If in code_aster_version/code_aster/Cata/Commands/assemblage.py, in
#    assemblage_prod() function, first check:
#      if ((not MATR_ASSE) and (not VECT_ASSE)):  raise AsException("Aucun concept a assembler")
#    is moved after NUME_DDL is checked, then
#      Command.filterby(stage, getattr(ds, 'nume_ddl_sdaster'))
#    returns 1 item (as it should be in fact).
#
#-------------------------------------------------------------------------------
