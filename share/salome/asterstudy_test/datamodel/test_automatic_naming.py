# -*- coding: utf-8 -*-

# Copyright 2016 - 2018 EDF R&D
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

"""Automatic tests for automatic naming of results."""


import unittest

from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.history import History
from asterstudy.datamodel.catalogs import reusable_keywords

from hamcrest import *


def test_reuse():
    history = History()
    stage = history.current_case.create_stage(':1:')

    cmd = stage.add_command('LIRE_MAILLAGE')
    assert_that(cmd.can_reuse(), equal_to(False))
    required, obj = cmd.reused()
    assert_that(required, equal_to(False))
    assert_that(obj, none())
    mesh = stage['mesh']

    cmd = stage.add_command('DEFI_GROUP')
    assert_that(cmd.name, equal_to("mesh0"))
    assert_that(cmd.can_reuse(), equal_to(True))
    required, obj = cmd.reused()
    assert_that(required, equal_to(True))
    assert_that(obj, none())

    cmd.init({'MAILLAGE': mesh})
    required, obj = cmd.reused()
    assert_that(required, equal_to(True))
    assert_that(obj, equal_to(mesh))
    # automatically renamed
    assert_that(cmd.name, equal_to("mesh"))

    cmd = stage.add_command('DEFI_GLRC', 'mymater')
    assert_that(cmd.name, equal_to("mymater"))
    assert_that(cmd.can_reuse(), equal_to(True))
    required, obj = cmd.reused()
    assert_that(required, equal_to(False))
    assert_that(obj, none())

    mat = stage.add_command('DEFI_MATERIAU', 'mat01')
    cmd.init({'LINER': {'MATER': mat}})
    required, obj = cmd.reused()
    assert_that(required, equal_to(False))
    assert_that(obj, equal_to(mat))
    # unchanged because not necessarly with reuse
    assert_that(cmd.name, equal_to("mymater"))

    # simulate that the user checks the box to reuse an input name + Ok
    cmd.reuse_input_name = True
    cmd.init({'LINER': {'MATER': mat}})
    assert_that(cmd.name, equal_to("mat01"))


def test_reusable():
    # CALC_CHAMP
    req, kwd = reusable_keywords("f:RESULTAT")
    assert_that(req, equal_to(False))
    assert_that(kwd, contains("RESULTAT"))

    # CALC_PRECONT
    req, kwd = reusable_keywords("f:ETAT_INIT:EVOL_NOLI")
    assert_that(req, equal_to(False))
    assert_that(kwd, contains("ETAT_INIT/EVOL_NOLI"))

    # CREA_RESU
    req, kwd = reusable_keywords("f:RESULTAT|RESU_FINAL")
    assert_that(req, equal_to(False))
    assert_that(kwd, contains("RESULTAT", "RESU_FINAL"))

    # DEFI_GLRC
    req, kwd = reusable_keywords("f:BETON|NAPPE|CABLE_PREC|LINER:MATER")
    assert_that(req, equal_to(False))
    assert_that(kwd, contains("BETON/MATER", "NAPPE/MATER",
                              "CABLE_PREC/MATER", "LINER/MATER"))

    # DEFI_GROUP
    req, kwd = reusable_keywords("o:MAILLAGE|GRILLE")
    assert_that(req, equal_to(True))
    assert_that(kwd, contains("MAILLAGE", "GRILLE"))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
