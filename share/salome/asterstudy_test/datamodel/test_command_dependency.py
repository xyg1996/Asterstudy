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

"""Automatic tests for commands."""


import unittest

from hamcrest import *

from asterstudy.common import get_cmd_mesh, is_medfile
from asterstudy.datamodel.history import History
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.command.helper import avail_meshes, avail_meshes_in_cmd
from asterstudy.datamodel.general import Validity

def test_issue_26221_1():
    """Test the mesh available for a command."""

    hist = History()
    cc = hist.current_case

    st = cc.create_stage('st1')
    text1 = """
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

mesh2 = LIRE_MAILLAGE(UNITE=21, FORMAT='ASTER')

model=AFFE_MODELE(MAILLAGE=mesh,
                  AFFE=_F(TOUT = 'OUI',
                          PHENOMENE = 'MECANIQUE',
                          MODELISATION = 'C_PLAN')
                  )

model2=AFFE_MODELE(MAILLAGE=mesh2,
                  AFFE=_F(TOUT = 'OUI',
                          PHENOMENE = 'MECANIQUE',
                          MODELISATION = 'C_PLAN')
                  )

matr=DEFI_MATERIAU(ELAS=_F( E = 2.E11,  NU = 0.3) )

matr2=DEFI_MATERIAU(ELAS=_F( E = 2.E11,  NU = 0.) )

chmat=AFFE_MATERIAU(MAILLAGE=mesh,
                    AFFE=_F(TOUT = 'OUI', MATER = (matr, matr2)))

boundc=AFFE_CHAR_MECA(MODELE=model,
                      DDL_IMPO=(_F(NOEUD = 'NO000007',
                                  DX = 0.),
                                _F(NOEUD = 'NO000008',
                                  DY = 0.),
                                )
                      )

resu=MECA_STATIQUE(MODELE=model, CHAM_MATER=chmat,
                   EXCIT=_F(CHARGE = boundc))

evolnoli=PROJ_CHAMP(METHODE='COLLOCATION',
                    RESULTAT=resu,
                    MODELE_1=model,
                    MODELE_2=model2,
                    NOM_CHAM='DEPL',
                    NUME_ORDRE=1,
                    VIS_A_VIS=_F(GROUP_MA_1='ALL_EL',
                                 GROUP_MA_2=('ALL_EL','ALL_EL_0'),
                                 ),
                    );
"""
    comm2study(text1, st)

    meshes = avail_meshes(st['chmat'].storage_nocopy)
    assert_that(meshes, equal_to([st['mesh']]))

    meshes = avail_meshes(st['boundc'].storage_nocopy)
    assert_that(meshes, equal_to([st['mesh']]))

    meshes = avail_meshes(st['evolnoli'].storage_nocopy)
    assert_that(set(meshes), equal_to({st['mesh'], st['mesh2']}))

def test_issue_26221_2():
    """Test the mesh available for a procedure."""

    # In this test, we test dependencies through procedures
    # A typical example with meshes is MACR_ADAP_MAIL

    hist = History()
    cc = hist.current_case

    st = cc.create_stage('st')

    text1 = """
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

MACR_ADAP_MAIL(ADAPTATION = 'RAFFINEMENT_UNIFORME',
               GROUP_MA=('VOLUME','ESCLAVE'),
               MAILLAGE_N=mesh,
               MAILLAGE_NP1=CO('mesh2'),
               )

model2=AFFE_MODELE(MAILLAGE=mesh2,
                  AFFE=_F(TOUT = 'OUI',
                          PHENOMENE = 'MECANIQUE',
                          MODELISATION = 'C_PLAN')
                  )

boundc2=AFFE_CHAR_MECA(MODELE=model2,
                       DDL_IMPO=_F(NOEUD = 'NO000007',
                                   DX = 0.),
                       )
"""
    comm2study(text1, st)

    meshes = avail_meshes(st['boundc2'].storage_nocopy)
    assert_that(set(meshes), equal_to({st['mesh'], st['mesh2']}))

def test_issue26221_3():
    """Test meshes available for a command, test with DETRUIRE/reuse."""

    hist = History()
    cc = hist.current_case

    st = cc.create_stage('st')

    text1 = """
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

mesh = DEFI_GROUP(reuse=mesh,
                  MAILLAGE=mesh,
                  CREA_GROUP_MA=_F(NOM='TOUT',
                                   TOUT='OUI'))

model = AFFE_MODELE(MAILLAGE=mesh,
                    AFFE=_F(TOUT = 'OUI',
                            PHENOMENE = 'MECANIQUE',
                            MODELISATION = 'C_PLAN')
                    )
"""
    comm2study(text1, st)

    meshes = avail_meshes(st['model'].storage_nocopy)
    assert_that(set(meshes), equal_to({st[0], st[1]}))

def test_get_cmd_mesh():
    """Test getting meshfile from a mesh command"""

    import os
    hist = History()
    cc = hist.current_case

    st = cc.create_stage('st')
    text1 = """
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

mesh2 = LIRE_MAILLAGE(UNITE=38, FORMAT='ASTER')

mesh3 = ASSE_MAILLAGE(MAILLAGE_1=mesh, MAILLAGE_2=mesh2, OPERATION='SUPERPOSE')
"""
    comm2study(text1, st)

    # test standard LIRE_MAILLAGE with MED format
    filename = os.path.join(os.getenv('ASTERSTUDYDIR'),
                            'data', 'export', 'adlv100a.mmed')
    assert_that(is_medfile(filename), equal_to(True))
    st['mesh']['UNITE'].value = {20: filename}

    filepath, medname = get_cmd_mesh(st['mesh'])
    assert_that(os.path.samefile(filename, filepath), equal_to(True))
    assert_that(medname, equal_to("MA"))

    # test a file not in MED format
    filename = os.path.join(os.getenv('ASTERSTUDYDIR'),
                        'data', 'export', 'fileB.38')
    st['mesh2']['UNITE'].value = {38: filename}

    filepath, medname = get_cmd_mesh(st['mesh2'])
    assert_that(filepath, equal_to(None))
    assert_that(medname, equal_to(None))

    # test another command than LIRE_MAILLAGE
    filepath, medname = get_cmd_mesh(st['mesh3'])
    assert_that(filepath, equal_to(None))
    assert_that(medname, equal_to(None))

    # after that the command is deleted
    cmd = st['mesh']
    cmd.delete()
    filepath, medname = get_cmd_mesh(cmd)
    assert_that(filepath, equal_to(None))
    assert_that(medname, equal_to(None))

def test_issue_26625():
    """Test providing *None* to avail_meshes_in_cmd."""
    assert_that(avail_meshes_in_cmd(None), equal_to([]))

def test_issue_26694():
    """Test avail_meshes_in_cmd with output type depending on args."""
    # create an empty DEFI_FONCTION command
    hist = History()
    cc = hist.current_case

    st = cc.create_stage('st')
    cmd = st('DEFI_FONCTION')

    # assert available meshes in it returns empty list
    assert_that(avail_meshes_in_cmd(cmd), equal_to([]))

def test_26790():
    # Warning: in 'dict_categories_test', category POST_COQUE is after
    #   POST_RCCM category, but not in 'dict_categories'.
    hist = History()
    cc = hist.current_case

    st = cc.create_stage('st')
    lire1 = st('POST_COQUE', 'pres')
    lire2 = st('POST_COQUE', 'ther')
    lire3 = st('POST_COQUE', 'ther2')

    post1 = st('POST_RCCM', 'pmpb1')
    sn1 = st('POST_RCCM', 'sn1')
    # without dependency
    assert_that(st.sorted_commands, contains(post1, sn1, lire1, lire2, lire3))

    post1.init({'TYPE_RESU_MECA': 'B3200',
                'RESU_MECA_UNIT': {'TABL_PRES': lire1}})
    sn1.init({'TYPE_RESU_MECA': 'B3200',
              'RESU_THER': [{'TABL_RESU_THER': lire2},
                            {'TABL_RESU_THER': lire3}]})

    # with dependencies
    st.reorder()
    assert_that(st.sorted_commands, contains(lire1, post1, lire2, lire3, sn1))

def test_issue_27758():
    """Test dependencies are preserved during a copy paste."""
    # Create two stages
    hist = History()
    cc = hist.current_case

    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')
    text1 = """
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

model=AFFE_MODELE(MAILLAGE=mesh,
                  AFFE=_F(TOUT = 'OUI',
                          PHENOMENE = 'MECANIQUE',
                          MODELISATION = 'C_PLAN')
                  )

matr=DEFI_MATERIAU(ELAS=_F( E = 2.E11,  NU = 0.3) )

chmat=AFFE_MATERIAU(MAILLAGE=mesh,
                    AFFE=_F(TOUT = 'OUI', MATER = matr))
"""
    text2 = """

boundc=AFFE_CHAR_MECA(MODELE=model,
                      DDL_IMPO=(_F(NOEUD = 'NO000007',
                                  DX = 0.),
                                _F(NOEUD = 'NO000008',
                                  DY = 0.),
                                )
                      )

resu=MECA_STATIQUE(MODELE=model, CHAM_MATER=chmat,
                   EXCIT=_F(CHARGE = boundc))

"""
    comm2study(text1, st1)
    comm2study(text2, st2)

    # Simulate copy operation
    clipboard = "\n".join([st1['model'].__str__(rename=True)])

    # Simulate paste operation
    st1.paste(clipboard)

    # Check both stages are valid
    assert_that(cc.check(), equal_to(Validity.Nothing))

    # Check validity is preserved during a duplicate
    # on the condition that the command be renamed
    copy = st1['model'].copy()
    copy.rename('model_cp')
    assert_that(cc.check(), equal_to(Validity.Nothing))

if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())

#------------------------------------------------------------------------------
