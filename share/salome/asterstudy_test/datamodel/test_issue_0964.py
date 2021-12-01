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

"""Automatic tests for export feature."""


import unittest
from hamcrest import *

from asterstudy.datamodel.history import History
from testutils.tools import check_export, check_import

#------------------------------------------------------------------------------
def test():
    #--------------------------------------------------------------------------
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')

    text = \
"""
List_r = DEFI_LIST_REEL(DEBUT=0.0,
                        INTERVALLE=_F(JUSQU_A=1.0,
                                      PAS=1.0))

List_i = DEFI_LIST_INST(DEFI_LIST=_F(LIST_INST=List_r),
                        ECHEC=_F(ACTION='DECOUPE',
                                 EVENEMENT='ERREUR'),
                        METHODE='MANUEL')
"""
    assert(check_import(text))

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
