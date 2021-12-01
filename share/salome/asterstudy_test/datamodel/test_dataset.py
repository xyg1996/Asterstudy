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

"""Automatic tests for general services."""


import unittest

from hamcrest import *

from asterstudy.datamodel.history import History
from asterstudy.datamodel.general import ConversionLevel


def test_list_of_commands():
    """Test for list of commands"""
    from asterstudy.datamodel.catalogs import CATA
    from asterstudy.datamodel.command import Command

    history = History()
    stage = history.current_case.create_stage(':memory:')
    dset = stage.dataset

    debut = stage('DEBUT')
    assert_that(dset, has_length(1))
    assert_that(debut, is_in(dset.commands))

    mesh = stage('LIRE_MAILLAGE', 'mesh')
    mater = stage('DEFI_MATERIAU', 'mater')
    asse = stage('ASSE_MAILLAGE', 'asse')
    assert_that(dset, has_length(4))

    # because of categories, mesh < mater
    # because of uid, mesh < asse
    assert_that(dset.sorted_commands, contains(debut, mesh, asse, mater))

def test_loc_task1():
    """Test for list of commands: starter"""
    from asterstudy.datamodel.dataset import STARTER, DELETERS, DELETED_NAMES
    history = History()
    stage = history.current_case.create_stage(':memory:')
    dset = stage.dataset

    # check list of commands cache content
    assert_that(dset._cache.get(STARTER), equal_to(None))
    assert_that(dset._cache.get(DELETERS), equal_to({}))
    assert_that(dset._cache.get(DELETED_NAMES), equal_to({}))

    mesh = stage('LIRE_MAILLAGE')
    starter = stage('DEBUT')
    assert_that(dset._cache.get(STARTER), equal_to(starter))
    assert_that(dset._ids, contains(starter.uid, mesh.uid))


def test_loc_task2():
    """Test for list of commands: deletions"""
    from asterstudy.datamodel.dataset import STARTER, DELETERS, DELETED_NAMES
    history = History()
    stage = history.current_case.create_stage(':memory:')
    dset = stage.dataset

    mesh = stage('LIRE_MAILLAGE', 'Mesh')
    detr = stage('DETRUIRE')
    detr["CONCEPT"]["NOM"] = mesh
    # needed to take new arguments into account
    dset.reorder(detr)

    # check list of commands cache content
    assert_that(dset._cache.get(STARTER), equal_to(None))
    assert_that(dset._cache.get(DELETERS), has_length(1))
    assert_that(dset._cache.get(DELETED_NAMES), has_length(1))
    assert_that(dset._ids, contains(mesh.uid, detr.uid))

    newmesh = stage('LIRE_MAILLAGE', 'Mesh')
    assert_that(dset._ids, contains(mesh.uid, detr.uid, newmesh.uid))


def test_loc_task3():
    """Test for list of commands: deletions/reuse"""
    from asterstudy.datamodel.dataset import STARTER, DELETERS, DELETED_NAMES
    history = History()
    stage = history.current_case.create_stage(':memory:')
    dset = stage.dataset

    mesh1 = stage('LIRE_MAILLAGE', 'mesh')

    mesh2 = stage('MODI_MAILLAGE', 'mesh')
    mesh2['MAILLAGE'] = mesh1
    dset.reorder(mesh2)

    detr = stage('DETRUIRE')
    detr["CONCEPT"]["NOM"] = mesh2

    # needed to take new arguments into account
    dset.reorder(detr)

    # check list of commands cache content
    assert_that(dset._cache.get(STARTER), equal_to(None))
    assert_that(dset._cache.get(DELETERS), has_length(1))
    assert_that(dset._cache.get(DELETED_NAMES), has_length(1))
    assert_that(dset._ids, contains(mesh1.uid, mesh2.uid, detr.uid))

    # be care to recursive dependencies
    dset.reorder(mesh1)
    assert_that(dset._cache.get(DELETERS), has_length(1))
    assert_that(dset._cache.get(DELETED_NAMES), has_length(1))
    assert_that(dset._ids, contains(mesh1.uid, mesh2.uid, detr.uid))


def test_loc_task4():
    """Test for list of commands: dependencies"""
    history = History()
    stage = history.current_case.create_stage(':memory:')
    dset = stage.dataset

    form = stage('FORMULE')
    mate = stage('DEFI_MATERIAU')
    # because of category
    assert_that(dset._ids, contains(mate.uid, form.uid))

    form.init({'VALE': '1.'})
    mate.init({'TRACTION': {'SIGM': form}})
    stage.check()
    # because of dependencies
    assert_that(dset._ids, contains(form.uid, mate.uid))


def test_loc_task5():
    """Test for list of commands: independent group"""
    history = History()
    stage = history.current_case.create_stage(':memory:')
    dset = stage.dataset

    form = stage('FORMULE') # Functions and Lists: 3
    recu = stage("RECU_FONCTION") # Post Processing: 8
    tabl = stage('POST_COQUE') # Other: last
    mate = stage('DEFI_MATERIAU') # Material: 2
    # because of category
    assert_that(dset._ids, contains(mate.uid, form.uid, recu.uid, tabl.uid))

    recu.init({'TABLE': tabl})
    # because of dependencies
    assert_that(dset._ids, contains(mate.uid, form.uid, tabl.uid, recu.uid))

    mate.init({'TRACTION': {'SIGM': recu}})
    assert_that(dset._ids, contains(form.uid, tabl.uid, recu.uid, mate.uid))

    # this broke dependencies if we don't see deps on following commands
    mate.check()
    assert_that(dset._ids[0], is_not(mate.uid))
    assert_that(dset._ids, contains(form.uid, tabl.uid, recu.uid, mate.uid))

    # independency on a command update
    import random
    cmds = [form, tabl, recu, mate]
    for i in range(17):
        random.shuffle(cmds)
        for obj in cmds:
            obj.check()
            assert_that(dset._ids, contains(form.uid, tabl.uid, recu.uid,
                                            mate.uid))

    # check that save/restore preserves the commands order
    import tempfile
    import os
    ajs = tempfile.mkstemp(suffix='.ajs')[1]
    History.save(history, ajs)

    history2 = History.load(ajs, strict=ConversionLevel.NoFail)
    os.remove(ajs)
    stage2 = history2.current_case[0]
    titles = [i.title for i in stage2]
    assert_that(titles, contains('FORMULE', 'POST_COQUE', 'RECU_FONCTION',
                                 'DEFI_MATERIAU'))


def test_loc_task6():
    """Test for list of commands: comment"""
    from asterstudy.datamodel.abstract_data_model import add_parent
    history = History()
    stage = history.current_case.create_stage(':memory:')
    dset = stage.dataset

    comm = stage('_CONVERT_COMMENT')
    comm['EXPR'] = 'Line with a comment'

    debu = stage('DEBUT')
    add_parent(debu, comm)
    debu.check()

    mesh = stage('LIRE_MAILLAGE')

    assert_that(dset._ids, contains(comm.uid, debu.uid, mesh.uid))


def test_loc_task7():
    """Test for list of commands: comments category"""
    # Problem encountered with comm2code on zzzz289a.comm
    # Order changed after 'for i in stage: i.check()'
    from asterstudy.datamodel.comm2study import comm2study
    import os
    text = \
"""
DEBUT(CODE=_F(
NIV_PUB_WEB='INTERNET',),DEBUG=_F(SDVERI='OUI'))

#ON LIT UN MAILLAGE QUADRATIQUE EN TETRA10 POUR TESTER LES ELEM
# P2P1P1 (D_PLAN_INCO_UPG), P2P1P1 (D_PLAN_INCO_UPG) ET P2P1 (D_PLAN_INCO_UP)
MAIL_Q=LIRE_MAILLAGE();

MATER=DEFI_MATERIAU(ELAS=_F(E=30000.0,
                            NU=0.2,
                            RHO=2764.0,),
                    ECRO_LINE=_F(D_SIGM_EPSI=-1950.0,
                                 SY=3.0,),);

CHMAT_Q=AFFE_MATERIAU(MAILLAGE=MAIL_Q,
                      AFFE=_F(TOUT='OUI',
                              MATER=MATER,),);

MODELUPG=AFFE_MODELE(MAILLAGE=MAIL_Q,
                     AFFE=_F(TOUT='OUI',
                             PHENOMENE='MECANIQUE',
                             MODELISATION='D_PLAN_INCO_UPG',),);
"""
    history = History()
    stage = history.current_case.create_stage(':memory:')
    dset = stage.dataset

    comm2study(text, stage)

    # Categories: Mesh 0, Model 1, Mater 2
    refs = ['DEBUT', '_CONVERT_COMMENT', 'LIRE_MAILLAGE', 'AFFE_MODELE',
            'DEFI_MATERIAU', 'AFFE_MATERIAU']
    cmds = [i.title for i in stage.sorted_commands]
    assert_that(cmds, contains(*refs))

    # If comments are in category Other, when checking/ordering DEFI_MATERIAU,
    # it is less than the comment and can be inserted before LIRE_MAILLAGE.
    # If comments take the category of their child, it's ok.
    for i in stage:
        i.check()

    cmds = [i.title for i in stage.sorted_commands]
    assert_that(cmds, contains(*refs))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
