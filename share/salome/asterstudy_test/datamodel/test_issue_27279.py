# -*- coding: utf-8 -*-

# Copyright 2018 EDF R&D
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

"""Automatic tests for export feature."""


import re
import unittest

from asterstudy.common import ConversionError
from asterstudy.datamodel import History, Validity
from hamcrest import *
from testutils import attr


def test_27279():
    """Test for issue27279"""
    history = History()
    case = history.current_case
    stage = case.create_stage('test_27279')

    cmd = stage("LIRE_MAILLAGE", "mesh")
    cmd.init({'UNITE': 20})

    cmd = stage('AFFE_MATERIAU', 'fieldmat')
    cmd.init({'MAILLAGE': stage['mesh'],
              'AFFE': {'TOUT': 'OUI'}}) # 'mater': stage['mat']
    assert_that(cmd.check(), equal_to(Validity.Syntaxic))

    cmd.init({'MAILLAGE': stage['mesh'], 'AFFE': ()})
    assert_that(cmd.check(), equal_to(Validity.Syntaxic))

    cmd = stage('DEFI_MATERIAU', 'mat')
    cmd.init({'ELAS': {'E': 30000.0, 'NU': 0.2}})
    assert_that(cmd.check(), equal_to(Validity.Nothing))

    expr_ok = re.compile("DEFI_MATERIAU.*AFFE_MATERIAU", re.DOTALL)
    expr_nook = re.compile("AFFE_MATERIAU.*DEFI_MATERIAU", re.DOTALL)

    text = stage.get_text(sort=True, pretty_text=False)
    assert_that(text, is_not(matches_regexp(expr_ok)))
    assert_that(text, matches_regexp(expr_nook))

    # ensure that the commands are reordered after change
    cmd = stage['fieldmat']

    # the gui should ask for reordering (through astergui.update)
    cmd.init({'MAILLAGE': stage['mesh'],
              'AFFE': {'TOUT': 'OUI', 'MATER': stage['mat']}})
    assert_that(cmd.check(), equal_to(Validity.Nothing))

    text = stage.get_text(sort=True, pretty_text=False)
    assert_that(text, matches_regexp(expr_ok))
    assert_that(text, is_not(matches_regexp(expr_nook)))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
