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

"""Automatic tests for validity status management for variables (issue 1815)."""


from hamcrest import *

from testutils import attr

from asterstudy.datamodel import History, Validity

#------------------------------------------------------------------------------
@attr('fixit')
def test_variables_validity():
    """Test for issue 1815"""
    history = History()
    s1 = history.current_case.create_stage()
    assert_that(s1.check(), equal_to(Validity.Nothing))
    text = """
a = 1
a = 2
"""
    s1.paste(text)
    assert_that(s1.check(), equal_to(Validity.Naming))    # naming conflict: OK
    assert_that(s1[0].check(), equal_to(Validity.Naming)) # ??? previously was Nothing, is current behavior OK?
    assert_that(s1[1].check(), equal_to(Validity.Naming)) # naming conflict: OK

    s1[1].rename('c')
    assert_that(s1.check(), equal_to(Validity.Nothing))    # !!! NOOK: no naming conflict
    assert_that(s1[0].check(), equal_to(Validity.Nothing)) # !!! NOOK: no naming conflict
    assert_that(s1[1].check(), equal_to(Validity.Nothing)) # no naming conflict: OK

    s1[1].rename('a')
    assert_that(s1.check(), equal_to(Validity.Naming))    # naming conflict: OK
    assert_that(s1[0].check(), equal_to(Validity.Naming)) # ??? previously was Nothing, is current behavior OK?
    assert_that(s1[1].check(), equal_to(Validity.Naming)) # naming conflict: OK

    s2 = history.current_case.create_stage()
    text = """
b = a * 2
"""
    s2.paste(text)
    assert_that(s2[0].evaluation, equal_to(4))             # OK
    assert_that(s2.check(), equal_to(Validity.Nothing))    # ??? previously was Naming, is current behavior OK?
    assert_that(s2[0].check(), equal_to(Validity.Nothing)) # ??? previously was Naming, is current behavior OK?

    s1[1].delete()
    assert_that(s1.check(), equal_to(Validity.Nothing))    # !!! NOOK: no naming conflict
    assert_that(s1[0].check(), equal_to(Validity.Nothing)) # !!! NOOK: no naming conflict
    assert_that(s2[0].evaluation, equal_to(2))              # OK
    assert_that(s2.check(), equal_to(Validity.Nothing))     # no naming conflict: OK
    assert_that(s2[0].check(), equal_to(Validity.Nothing))  # no naming conflict: OK

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
