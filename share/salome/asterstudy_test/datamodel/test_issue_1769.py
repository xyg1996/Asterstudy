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

from asterstudy.datamodel import History, Validity


def test_formule_param():
    """Test for FORMULE initialization"""
    history = History()
    stage = history.current_case.create_stage()

    # add empty FORMULE
    f = stage.add_command('FORMULE', 'f')
    assert_that(f['VALE'].value, none())
    assert_that(f['NOM_PARA'].value, none())

    # init NOM_PARA with simple string
    f.init({'NOM_PARA':'inst', 'VALE':'10*inst'})
    assert_that(f['VALE'].value, equal_to('10*inst'))
    assert_that(f['NOM_PARA'].value, equal_to('inst'))
    assert_that(f.check(), equal_to(Validity.Nothing))

    # init NOM_PARA with one-item tuple
    f.init({'NOM_PARA': ('inst', ), 'VALE': '10*inst'})
    assert_that(f['VALE'].value, equal_to('10*inst'))
    assert_that(f['NOM_PARA'].value, equal_to(('inst',)))
    assert_that(f.check(), equal_to(Validity.Nothing))

    # init NOM_PARA with two-items tuple
    f.init({'NOM_PARA': ('inst', 'aaa'), 'VALE': '10*inst'})
    assert_that(f['VALE'].value, equal_to('10*inst'))
    assert_that(f['NOM_PARA'].value, equal_to(('inst', 'aaa')))
    assert_that(f.check(), equal_to(Validity.Nothing))

    # init NOM_PARA with None
    f.init({'NOM_PARA': None, 'VALE': '10'})
    assert_that(f['VALE'].value, equal_to('10'))
    assert_that(f['NOM_PARA'].value, none())
    assert_that(f.check(), equal_to(Validity.Syntaxic))

    # init NOM_PARA with tuple containing only None
    f.init({'NOM_PARA': (None, ), 'VALE': '10'})
    assert_that(f['VALE'].value, equal_to('10'))
    assert_that(f['NOM_PARA'].value, contains(none()))
    assert_that(f.check(), equal_to(Validity.Syntaxic))

    # init NOM_PARA with tuple containing None
    f.init({'NOM_PARA': ('inst', None), 'VALE': '10*inst'})
    assert_that(f['VALE'].value, equal_to('10*inst'))
    assert_that(f['NOM_PARA'].value, equal_to(('inst', None)))
    assert_that(f.check(), equal_to(Validity.Syntaxic))

def test_optional():
    history = History()
    stage = history.current_case.create_stage()

    # add empty DEFI_CONSTANTE
    c = stage.add_command('DEFI_CONSTANTE', 'c')
    assert_that(c['VALE'].value, none())
    assert_that(c['NOM_RESU'].value, none())
    assert_that(c.check(), equal_to(Validity.Syntaxic))

    # init only mandatory keywords
    c.init({'VALE': 10})
    assert_that(c['VALE'].value, equal_to(10))
    assert_that(c['NOM_RESU'].value, none())
    assert_that(c.check(), equal_to(Validity.Nothing))

    # init with optional keywords to None
    c.init({'VALE': 10, 'NOM_RESU': None, 'TITRE': None})
    assert_that(c['VALE'].value, equal_to(10))
    assert_that(c['NOM_RESU'].value, none())
    assert_that(c.check(), equal_to(Validity.Nothing))

def test_optional_max():
    history = History()
    stage = history.current_case.create_stage()

    # with typ='TXM' and max='**'
    deb = stage.add_command('DEBUT')
    assert_that(deb.check(), equal_to(Validity.Nothing))

    # init with optional keywords to None
    deb.init({'IGNORE_ALARM': None})
    assert_that(deb.check(), equal_to(Validity.Nothing))

    deb.init({'IGNORE_ALARM': (None, )})
    assert_that(deb.check(), equal_to(Validity.Nothing))

    deb.init({'IGNORE_ALARM': ('MESSAGE_1', None)})
    assert_that(deb.check(), equal_to(Validity.Syntaxic))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
