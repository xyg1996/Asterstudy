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

from asterstudy.datamodel import History

def test_1777():
    history = History()
    cc = history.current_case
    cc.create_stage()

    unit = 20
    file_name = 'some.file'

    #------------------------------------------------------------------------------
    cc[0]('LIRE_MAILLAGE', 'm').init({'UNITE':{unit:file_name}})
    assert_that(cc[0]['m'].active, equal_to(True))
    assert_that(unit, is_in(cc[0].handle2info))

    #------------------------------------------------------------------------------
    cc[0][0].active = False
    assert_that(cc[0]['m'].active, equal_to(False))
    assert_that(unit, not_(is_in(cc[0].handle2info)))

    #------------------------------------------------------------------------------
    rc1 = history.create_run_case().run()
    assert_that(rc1[0]['m'].active, equal_to(False))
    assert_that(unit, not_(is_in(rc1[0].handle2info)))
    assert_that(cc[0]['m'].active, equal_to(False))
    assert_that(unit, not_(is_in(cc[0].handle2info)))

    #------------------------------------------------------------------------------
    rc2 = history.create_run_case().run()
    assert_that(rc1[0]['m'].active, equal_to(False))
    assert_that(unit, not_(is_in(rc1[0].handle2info)))
    assert_that(rc2[0]['m'].active, equal_to(False))
    assert_that(unit, not_(is_in(rc2[0].handle2info)))
    assert_that(cc[0]['m'].active, equal_to(False))
    assert_that(unit, not_(is_in(cc[0].handle2info)))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
