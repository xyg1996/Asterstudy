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


import os.path as osp
import unittest
from hamcrest import *

from testutils import tempdir

from asterstudy.datamodel import History
from asterstudy.datamodel.general import ConversionLevel
from asterstudy.datamodel.parametric import output_commands


def test_of_input_data():
    """Test for issue #1609 - OpenTurns widget, input data"""
    h = History()
    cc = h.current_case
    s1 = cc.create_stage('s1')
    s2 = cc.create_stage('s2')

    s1.add_variable('a').update('100')
    s1.add_variable('b').update('200')
    s1.add_variable('c').update('300')
    assert_that('a', is_in(cc.variables))
    assert_that('b', is_in(cc.variables))
    assert_that('c', is_in(cc.variables))
    assert_that(cc.variables, has_length(3))

    c1 = s1('IMPR_TABLE')
    assert_that(c1, is_not(is_in(output_commands(cc))))
    c1.init({'FORMAT':'NUMPY',})
    assert_that(c1, is_not(is_in(output_commands(cc))))
    c1.init({'NOM_PARA':'param',})
    assert_that(c1, is_not(is_in(output_commands(cc))))
    c1.init({'UNITE':{20:'aaa.txt'},})
    assert_that(c1, is_not(is_in(output_commands(cc))))
    c1.init({'FORMAT':'NUMPY', 'NOM_PARA':'param', 'UNITE': 20,})
    assert_that(c1, is_in(output_commands(cc)))
    c1.init({'FORMAT':'NUMPY', 'NOM_PARA':'param', 'UNITE': {20: 'aaa.txt'}})
    assert_that(c1, is_in(output_commands(cc)))
    assert_that(output_commands(cc), has_length(1))

    s2.add_variable('x').update('1')
    s2.add_variable('y').update('2')
    s2.add_variable('z').update('3')
    assert_that(cc.variables, has_length(6))
    assert_that('x', is_in(cc.variables))
    assert_that('y', is_in(cc.variables))
    assert_that('z', is_in(cc.variables))

    c2 = s2('IMPR_TABLE')
    c2.init({'FORMAT':'NUMPY', 'NOM_PARA':('aaa', 'bbb', 'ccc'),
             'UNITE':{30:'bbb.txt'}})
    assert_that(c2, is_in(output_commands(cc)))
    assert_that(output_commands(cc), has_length(2))


@tempdir
def test_of_output_data(tmpdir):
    """Test for issue #1609 - OpenTurns widget, output data"""
    h1 = History()
    cc = h1.current_case
    s1 = cc.create_stage('s1')

    assert_that(cc.ot_data, has_length(2))
    assert_that(cc.ot_data[0], equal_to(()))
    assert_that(cc.ot_data[1], none())

    cc.set_ot_data('a', 10)
    assert_that(cc.ot_data, has_length(2))
    assert_that(cc.ot_data[0], equal_to(('a',)))
    assert_that(cc.ot_data[1], 10)

    cc.set_ot_data(('a', 'b', 'c',), 20)
    assert_that(cc.ot_data, has_length(2))
    assert_that(cc.ot_data[0], equal_to(('a', 'b', 'c')))
    assert_that(cc.ot_data[1], 20)

    filename = osp.join(tmpdir, 'study.ajs')
    History.save(h1, filename)

    h2 = History.load(filename, strict=ConversionLevel.NoFail)
    cc = h2.current_case
    assert_that(cc.ot_data, has_length(2))
    assert_that(cc.ot_data[0], equal_to(('a', 'b', 'c')))
    assert_that(cc.ot_data[1], 20)



if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
