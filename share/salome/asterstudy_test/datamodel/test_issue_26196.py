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

"""Bug #1233 - filterby fails with non-finished commands"""


import unittest
from hamcrest import *
from testutils import attr

from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study

def test_issue26196_1():
    """Test file2unit multi-stage behavior"""

    hist = History()
    cc = hist.current_case
    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')
    st3 = cc.create_stage('st3')

    text1 = """
mesh=LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

mesh2=CREA_MAILLAGE(MAILLAGE=mesh, LINE_QUAD=_F(TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=82, RESU=_F(MAILLAGE=mesh2))
"""
    text2 = """
mesh=DEFI_GROUP(reuse=mesh, MAILLAGE=mesh, CREA_GROUP_MA=_F(NOM='TOUT', TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=81, RESU=_F(MAILLAGE=mesh))
"""
    text3 = """
mesh3=LIRE_MAILLAGE(UNITE=21, FORMAT='MED')

mesh3=CREA_MAILLAGE(MAILLAGE=mesh3, LINE_QUAD=_F(TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=80, RESU=_F(MAILLAGE=mesh3))
"""
    comm2study(text1, st1)
    comm2study(text2, st2)
    comm2study(text3, st3)

    st1['mesh']['UNITE'].value = {2: '/dummy/file/A'}
    st1[2]['UNITE'].value = {7: '/dummy/file/B'}

    st2[1]['UNITE'].value = {4: '/dummy/file/C'}

    st3[0]['UNITE'].value = {3: '/dummy/file/D'}
    st3[2]['UNITE'].value = {5: '/dummy/file/E'}

    # when in `st2`, check files in `st1` and `st3` are found
    assert_that(st2.file2unit('/dummy/file/A'), equal_to(2))
    assert_that(st2.file2unit('/dummy/file/A', umin=1, umax=99), equal_to(2))

    assert_that(st2.file2unit('/dummy/file/D'), equal_to(3))
    assert_that(st2.file2unit('/dummy/file/D', udefault=20, umin=1, umax=99), equal_to(3))

    # check that the used logical units are never proposed for a new file
    assert_that(st2.file2unit('/dummy/file/F'), is_not(is_in([2, 3, 4, 5, 7])))
    assert_that(st2.file2unit('/dummy/file/F', umin=1, umax=99), is_not(is_in([2, 3, 4, 5, 7])))
    assert_that(st2.file2unit('/dummy/file/F', udefault=20, umin=1, umax=99), is_not(is_in([2, 3, 4, 5, 7])))

def test_issue26196_2():
    """Test looking for a repeated file across stages."""
    hist = History()
    cc = hist.current_case
    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')

    # empty stage to test it is well treated by the recursion
    st3 = cc.create_stage('st3')

    text1 = """
mesh=LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

mesh2=CREA_MAILLAGE(MAILLAGE=mesh, LINE_QUAD=_F(TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=82, RESU=_F(MAILLAGE=mesh2))
"""
    text2 = """
mesh=DEFI_GROUP(reuse=mesh, MAILLAGE=mesh, CREA_GROUP_MA=_F(NOM='TOUT', TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=20, RESU=_F(MAILLAGE=mesh))

mesh3=LIRE_MAILLAGE(UNITE=21, FORMAT='ASTER')
"""
    comm2study(text1, st1)
    comm2study(text2, st2)

    st1['mesh']['UNITE'].value = {2: '/dummy/file/A'}
    st1[2]['UNITE'].value = {7: '/dummy/file/B'}

    st2[1]['UNITE'].value = {2: '/dummy/file/A'}
    st2['mesh3']['UNITE'].value = {3: '/dummy/file/C'}

    info = st1.handle2info[2]
    assert_that(info.is_repeated(st1), equal_to(True))

    info = st2.handle2info[2]
    assert_that(info.is_repeated(st2), equal_to(True))

    info = st1.handle2info[7]
    assert_that(info.is_repeated(st1), equal_to(False))

    info = st2.handle2info[3]
    assert_that(info.is_repeated(st2), equal_to(False))

def test_issue26196_3():
    """
    Test looking for unit conflicts across stages.
    """

    # the middle stage has a conflict with first stage
    # and another conflict with second stage
    hist = History()
    cc = hist.current_case
    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')
    st3 = cc.create_stage('st3')

    # a unit conflict is a unit shared by two different files
    text1 = """
mesh=LIRE_MAILLAGE(UNITE=7, FORMAT='MED')

mesh2=CREA_MAILLAGE(MAILLAGE=mesh, LINE_QUAD=_F(TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=10, RESU=_F(MAILLAGE=mesh2))
"""
    text2 = """
mesh=DEFI_GROUP(reuse=mesh, MAILLAGE=mesh, CREA_GROUP_MA=_F(NOM='TOUT', TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=4, RESU=_F(MAILLAGE=mesh))

mesh3=LIRE_MAILLAGE(UNITE=10, FORMAT='ASTER')

mesh4=LIRE_MAILLAGE(UNITE=11, FORMAT='MED')
"""
    text3 = """
mesh5=LIRE_MAILLAGE(UNITE=11, FORMAT='MED')

mesh5=CREA_MAILLAGE(MAILLAGE=mesh5, LINE_QUAD=_F(TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=5, RESU=_F(MAILLAGE=mesh4))
"""
    comm2study(text1, st1)
    comm2study(text2, st2)
    comm2study(text3, st3)

    # all distinct names
    st1['mesh']['UNITE'].value = {7: '/dummy/file/A'}
    st1[2]['UNITE'].value = {10: '/dummy/file/B'}

    st2[1]['UNITE'].value = {4: '/dummy/file/C'}
    st2['mesh3']['UNITE'].value = {10: '/dummy/file/D'}
    st2['mesh4']['UNITE'].value = {11: '/dummy/file/E'}

    st3[0]['UNITE'].value = {11: '/dummy/file/F'}
    st3[2]['UNITE'].value = {5: '/dummy/file/G'}

    # *True* if no conflicts, *False* if some conflicts detected
    assert_that(st1.unit_conflict(10, '/dummy/file/B'), equal_to(False))
    assert_that(st2.unit_conflict(10, '/dummy/file/D'), equal_to(False))
    assert_that(st2.unit_conflict(11, '/dummy/file/E'), equal_to(False))
    assert_that(st3.unit_conflict(11, '/dummy/file/F'), equal_to(False))

    assert_that(st1.unit_conflict(7, '/dummy/file/A'), equal_to(True))
    assert_that(st2.unit_conflict(4, '/dummy/file/C'), equal_to(True))
    assert_that(st3.unit_conflict(5, '/dummy/file/G'), equal_to(True))

def test_issue26196_4():
    """
    Test looking for file conflicts across stages.
    """
    # the middle stage has a conflict with first stage
    # and another conflict with second stage
    hist = History()
    cc = hist.current_case
    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')
    st3 = cc.create_stage('st3')

    # all logical units are different
    text1 = """
mesh=LIRE_MAILLAGE(UNITE=2, FORMAT='MED')

mesh2=CREA_MAILLAGE(MAILLAGE=mesh, LINE_QUAD=_F(TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=3, RESU=_F(MAILLAGE=mesh2))
"""
    text2 = """
mesh=DEFI_GROUP(reuse=mesh, MAILLAGE=mesh, CREA_GROUP_MA=_F(NOM='TOUT', TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=4, RESU=_F(MAILLAGE=mesh))

mesh3=LIRE_MAILLAGE(UNITE=5, FORMAT='ASTER')

mesh4=LIRE_MAILLAGE(UNITE=7, FORMAT='MED')
"""
    text3 = """
mesh5=LIRE_MAILLAGE(UNITE=10, FORMAT='MED')

mesh5=CREA_MAILLAGE(MAILLAGE=mesh5, LINE_QUAD=_F(TOUT='OUI'))

IMPR_RESU(FORMAT='MED', UNITE=11, RESU=_F(MAILLAGE=mesh4))
"""
    comm2study(text1, st1)
    comm2study(text2, st2)
    comm2study(text3, st3)

    # some files in common
    st1['mesh']['UNITE'].value = {2: '/dummy/file/A'}
    st1[2]['UNITE'].value = {3: '/dummy/file/B'}

    st2[1]['UNITE'].value = {4: '/dummy/file/C'}
    st2['mesh3']['UNITE'].value = {5: '/dummy/file/A'}
    st2['mesh4']['UNITE'].value = {7: '/dummy/file/D'}

    st3[0]['UNITE'].value = {10: '/dummy/file/C'}
    st3[2]['UNITE'].value = {11: '/dummy/file/E'}

    # *True* if no conflicts, *False* if some conflicts detected
    assert_that(st1.file_conflict(2, '/dummy/file/A')[0], equal_to(False))
    assert_that(st2.file_conflict(5, '/dummy/file/A')[0], equal_to(False))
    assert_that(st2.file_conflict(4, '/dummy/file/C')[0], equal_to(False))
    assert_that(st3.file_conflict(10, '/dummy/file/C')[0], equal_to(False))

    assert_that(st1.file_conflict(3, '/dummy/file/B')[0], equal_to(True))
    assert_that(st2.file_conflict(7, '/dummy/file/D')[0], equal_to(True))
    assert_that(st3.file_conflict(11, '/dummy/file/E')[0], equal_to(True))

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
