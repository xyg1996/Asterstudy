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

"""Automatic tests for formulas."""

import unittest

from asterstudy.datamodel import History, Validity, comm2study, study2comm
from asterstudy.datamodel.command.formula import external_objects
from hamcrest import *
from testutils.tools import check_import


def test_formula_utils():
    expr = '2. * a * sin(OMEGA * INST) * coef(OMEGA)'
    needed = external_objects([], expr)
    assert_that(needed, contains_inanyorder('INST', 'a', 'OMEGA', 'coef'))

    needed = external_objects(['INST'], expr)
    assert_that(needed, contains_inanyorder('a', 'OMEGA', 'coef'))

    needed = external_objects(['INST', 'OMEGA'], expr)
    assert_that(needed, contains_inanyorder('a', 'coef'))


def test_formula_deps():
    history = History()
    case = history.current_case
    # to use a variable from a previous stage
    stag0 = case.create_stage(':0:')
    var_a = stag0.add_variable('a', '3.')

    stage = case.create_stage(':1:')

    form = stage.add_command('FORMULE')
    form.init({'NOM_PARA': 'INST',
               'VALE': '2. * a * sin(OMEGA * INST) * coef(OMEGA)'})
    assert_that(form.external_deps, contains_inanyorder('a', 'OMEGA', 'coef'))

    # depends on its dataset and a
    assert_that(form.parent_nodes, has_length(2))
    assert_that(var_a, is_in(form.parent_nodes))
    assert_that(form.missing_deps, contains_inanyorder('OMEGA', 'coef'))
    assert_that(form.check(), equal_to(Validity.Dependency))

    coef = stage.add_command('DEFI_FONCTION', 'coef')
    # the formula must be edited to update its dependency
    form.submit()
    assert_that(var_a, is_in(form.parent_nodes))
    assert_that(coef, is_in(form.parent_nodes))

    omega = stag0.add_variable('OMEGA', 'pi / 2.')
    form.submit()
    assert_that(omega, is_in(form.parent_nodes))
    assert_that(form.missing_deps, empty())


def test_formula_export():
    history = History()
    case = history.current_case

    stage = case.create_stage(':1:')
    text = \
"""
a = 3.

OMEGA = pi / 2.

coef = DEFI_FONCTION(NOM_PARA='INST',
                     VALE=(0.0, 0.0, 1.0, 1.0))

form = FORMULE(NOM_PARA='INST',
               VALE='2. * a * sin(OMEGA * INST) * coef(OMEGA)',
               OMEGA=OMEGA,
               a=a,
               coef=coef)
"""
    comm2study(text, stage)
    assert_that(stage, has_length(4))
    assert_that(check_import(text))


def test_formula_with_missing_args():
    history = History()
    case = history.current_case

    stage = case.create_stage(':1:')
    text = \
"""
OMEGA = pi / 2.

coef = DEFI_FONCTION(NOM_PARA='INST',
                     VALE=(0.0, 0.0, 1.0, 1.0))

form = FORMULE(NOM_PARA='INST',
               VALE='2. * a * sin(OMEGA * INST) * coef(OMEGA)',
               OMEGA=OMEGA,
               coef=coef)
"""
    comm2study(text, stage)
    assert_that(stage, has_length(3))
    assert_that(stage.check(), equal_to(Validity.Dependency))
    text2 = study2comm(stage)
    assert_that(text2.strip(), equal_to(text.strip()))


def test_error_formula():
    history = History()
    case = history.current_case
    stage = case.create_stage(':1:')

    form = stage.add_command('FORMULE')
    # missing parenthesis to fail in external_objects
    form.init({'NOM_PARA': 'INST',
               'VALE': 'cos(2. * pi '})


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
