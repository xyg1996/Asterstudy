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

"""Automatic tests for unit registering and unregistering."""


import unittest

from asterstudy.datamodel.history import History
from asterstudy.datamodel.command.helper import unregister_unit
from hamcrest import *

def _setup_test():
    """Creates stage with valid LIRE_MAILLAGE command"""
    hist = History()
    cc = hist.current_case
    st = cc.create_stage(':a:')
    mesh = st("LIRE_MAILLAGE")
    # First call to Command.init with a *dict*
    thefile = "some_file.mail"
    theunit = 20
    mesh.init({"FORMAT":"ASTER", "UNITE": {theunit: thefile}})
    # Check the value of the file: OK
    assert_that(mesh["UNITE"].filename, equal_to(thefile))
    assert_that(st.handle2file(theunit), equal_to(thefile))
    return mesh, theunit, st, thefile

def _setup_test_macro():
    """Creates stage with macro that uses a file: issue 28325"""
    mesh, theunit, st, thefile = _setup_test()
    outmesh = st("IMPR_RESU")
    outfile = "some_out.med"
    outunit = 80
    outmesh.init({"FORMAT": "MED",
                  "RESU"  : {"MAILLAGE": mesh},
                  "UNITE" : {outunit: outfile},})
    return outmesh, outunit, st, outfile

def test_issue_27446():
    "Test bugged use case in issue27446"
    mesh, theunit, st, thefile = _setup_test()

    # Now init with only the unit as value
    mesh.init({"FORMAT": "ASTER", "UNITE": theunit})

    # The checks should be the same: KO before issue27446, OK after
    assert_that(mesh["UNITE"].filename, equal_to(thefile))
    assert_that(st.handle2file(theunit), equal_to(thefile))

def test_unregister_unit_1():
    "Test unused units are removed after changing the unit"
    mesh, theunit, st, _ = _setup_test()

    # Now init with *None* value
    otherfile = "other_file.mail"
    otherunit = 21

    mesh.init({"FORMAT": "ASTER", "UNITE": {otherunit: otherfile}})

    # The unit should be available again
    assert_that(theunit, is_not(is_in(st.handle2info)))
    assert_that(otherunit, is_in(st.handle2info))

def test_unregister_unit_2():
    "Test unused units are removed after None unit"
    mesh, theunit, st, _ = _setup_test()

    # Now init with None
    mesh.init({"FORMAT": "ASTER", "UNITE": None})

    # The unit should be available again
    assert_that(theunit, is_not(is_in(st.handle2info)))

def test_unregister_unit_3():
    "Test unused units are removed after invalid unit"
    mesh, theunit, st, thefile = _setup_test()

    # Now init with empty dict
    mesh.init({"FORMAT": "ASTER", "UNITE": {}})

    # The unit should be available again
    assert_that(theunit, is_not(is_in(st.handle2info)))

    # Now init with invalid unit
    mesh.init({"FORMAT": "ASTER", "UNITE": {theunit: thefile}})
    assert_that(theunit, is_in(st.handle2info))
    mesh.init({"FORMAT": "ASTER", "UNITE": {None: thefile}})
    assert_that(theunit, is_not(is_in(st.handle2info)))

    # Even a filepath to None (undefined) has the same behaviour
    mesh.init({"FORMAT": "ASTER", "UNITE": {theunit: thefile}})
    assert_that(theunit, is_in(st.handle2info))
    mesh.init({"FORMAT": "ASTER", "UNITE": {theunit: None}})
    assert_that(theunit, is_not(is_in(st.handle2info)))

def test_unused_units():
    "Test scenario with unused units"
    mesh, theunit, st, thefile = _setup_test()

    # Delete the command
    mesh.delete()

    # check unit has been deleted
    assert_that(theunit, is_not(is_in(st.handle2info)))

    # restore command, add unused file and convert to text
    mesh = st("LIRE_MAILLAGE")
    mesh.init({"FORMAT": "ASTER", "UNITE": {theunit: thefile}})
    unused_unit = 21
    st.handle2info[unused_unit].filename = "unused"
    st.use_text_mode()

    # check file entry is still there, but not unused one
    assert_that(theunit, is_in(st.handle2info))
    assert_that(unused_unit, is_not(is_in(st.handle2info)))

    # put unused unit manually, then convert back to graphical
    unused_unit = 21
    st.handle2info[unused_unit].filename = "unused"
    st.use_graphical_mode()

    # check everything is OK with the file, and unused has been cleared
    assert_that(theunit, is_in(st.handle2info))
    assert_that(st.handle2file(theunit), equal_to(thefile))
    assert_that(unused_unit, is_not(is_in(st.handle2info)))

def test_unused_units_macro():
    """Test file objects when converting to and from text mode: issue28325"""
    outmesh, outunit, st, outfile = _setup_test_macro()

    # unused unit
    unused_unit = 21
    st.handle2info[unused_unit].filename = "unused"

    # convert to text mode
    st.use_text_mode()
    assert_that(outunit, is_in(st.handle2info))
    assert_that(st.handle2file(outunit), equal_to(outfile))
    assert_that(unused_unit, is_not(is_in(st.handle2info)))

    # convert to graphical mode
    st.use_graphical_mode()
    assert_that(outunit, is_in(st.handle2info))
    assert_that(st.handle2file(outunit), equal_to(outfile))
    assert_that(unused_unit, is_not(is_in(st.handle2info)))



def test_issue_1770():
    hist = History()
    cc = hist.current_case
    st = cc.create_stage(':a:')
    mesh = st("LIRE_MAILLAGE")

    thefile = "some_file.mail"
    theunit = 20
    mesh.init({"FORMAT": "ASTER", "UNITE": {theunit: thefile}})

    assert_that(theunit, is_in(st.handle2info))

    st.use_text_mode()

    assert_that(theunit, is_in(st.handle2info))

    mesh.delete()

    assert_that(theunit, is_in(st.handle2info))

if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
