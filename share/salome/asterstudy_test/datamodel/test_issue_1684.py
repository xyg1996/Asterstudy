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
from testutils import attr

from asterstudy.datamodel.history import History
from asterstudy.datamodel.command import Command
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.general import Validity

#------------------------------------------------------------------------------
def test_concepts_in_text_stage():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('graphical')
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE(UNITE=22)

MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)

MODELUPQ = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)

MODELUPL = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UP',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)

MATER = DEFI_MATERIAU(ECRO_LINE=_F(D_SIGM_EPSI=-1950.0,
                                   SY=3.0),
                      ELAS=_F(E=30000.0,
                              NU=0.2,
                              RHO=2764.0))

CHMAT_Q = AFFE_MATERIAU(AFFE=_F(MATER=MATER,
                                TOUT='OUI'),
                        MAILLAGE=MAIL_Q)

MATMUPG = CALC_MATR_ELEM(CHAM_MATER=CHMAT_Q,
                         MODELE=MODELUPG,
                         OPTION='MASS_MECA')

FIN()
"""
    comm2study(text, stage)
    assert_that(stage.is_graphical_mode(), equal_to(True))
    assert_that(stage.check(), equal_to(Validity.Ok))

    assert_that(case.check(), equal_to(Validity.Ok))
    assert_that(case, has_length(1))

    #------------------------------------------------------------------------------
    stage2 = case.create_stage('text').use_text_mode()
    assert_that(stage2.is_text_mode(), equal_to(True))
    assert_that(stage2, has_length(0))

    #------------------------------------------------------------------------------
    stage2.add_command("LIRE_MAILLAGE", "MAIL_2")
    assert_that(stage2.check(), equal_to(Validity.Ok))
    assert_that(stage2.nb_commands, equal_to(1))

    command = stage2[0]
    assert_that(command.name, equal_to("MAIL_2"))
    assert_that(command.title, equal_to("LIRE_MAILLAGE"))
    assert_that("maillage_sdaster", equal_to(command.printable_type))

    #------------------------------------------------------------------------------
    stage2.add_command("AFFE_MODELE", "MODELUP2")
    assert_that(stage2.check(), equal_to(Validity.Ok))
    assert_that(stage2.nb_commands, equal_to(2))

    command = stage2[1]
    assert_that(command.name, equal_to("MODELUP2"))
    assert_that(command.title, equal_to("AFFE_MODELE"))
    assert_that("modele_sdaster", equal_to(command.printable_type))

    #------------------------------------------------------------------------------
    stage3 = case.create_stage('graphical2')
    assert_that(stage3.is_graphical_mode(), equal_to(True))
    assert_that(case, has_length(3))

    assert_that(stage3.check(), equal_to(Validity.Ok))
    assert_that(case.check(), equal_to(Validity.Ok))

    text3 = \
"""
MODELUP3 = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_2)
"""
    comm2study(text3, stage3)
    assert_that(stage3.is_graphical_mode(), equal_to(True))
    assert_that(stage3.check(), equal_to(Validity.Ok))
    assert_that(case.check(), equal_to(Validity.Ok))

#------------------------------------------------------------------------------
def test_type_assignment():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('').use_text_mode()

    assert_that("maillage_sdaster", is_in(Command.possible_types("LIRE_MAILLAGE")))
    command = stage.add_command("LIRE_MAILLAGE", "MAIL_Q")

    #------------------------------------------------------------------------------
    def assign_non_existing_type(): command.printable_type = "xxx"
    assert_that(assign_non_existing_type, raises(Exception))

    def assign_incompatible_type(): command.printable_type = "modele_sdaster"
    assert_that(assign_incompatible_type, raises(Exception))

    assert_that(command.printable_type, equal_to("maillage_sdaster"))

    #------------------------------------------------------------------------------
    command.printable_type = "maillage_sdaster"
    assert_that(command.printable_type, equal_to("maillage_sdaster"))

#------------------------------------------------------------------------------
def test_multi_type_affe_cara_elem():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('').use_text_mode()

    assert_that("cara_elem", is_in(Command.possible_types("AFFE_CARA_ELEM")))
    command = stage.add_command("AFFE_CARA_ELEM", "MAIL_Q")

    #------------------------------------------------------------------------------
    def assign_non_existing_type(): command.printable_type = "xxx"
    assert_that(assign_non_existing_type, raises(Exception))

    def assign_incompatible_type(): command.printable_type = "modele_sdaster"
    assert_that(assign_incompatible_type, raises(Exception))

    assert_that(command.printable_type, equal_to("cara_elem"))

    #------------------------------------------------------------------------------
    command.printable_type = "cara_elem"
    assert_that(command.printable_type, equal_to("cara_elem"))

#------------------------------------------------------------------------------
def test_multi_type_assemblage():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('').use_text_mode()

    command = stage.add_command("ASSEMBLAGE", "ASS")
    assert_that(Command.possible_types("ASSEMBLAGE"), has_items('matr_asse_depl_c', 'nume_ddl_sdaster', 'matr_asse_temp_r', 'cham_no_sdaster', 'matr_asse_pres_c', 'matr_asse_depl_r'))

    #------------------------------------------------------------------------------
    command.printable_type = "matr_asse_depl_c"
    assert_that(command.printable_type, equal_to("matr_asse_depl_c"))

#------------------------------------------------------------------------------
def test_multi_type_asse_maillage():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('').use_text_mode()

    command = stage.add_command("ASSE_MAILLAGE", "ASS")
    assert_that("maillage_sdaster", is_in(Command.possible_types("ASSE_MAILLAGE")))

    #------------------------------------------------------------------------------
    command.printable_type = "maillage_sdaster"
    assert_that(command.printable_type, equal_to("maillage_sdaster"))

#------------------------------------------------------------------------------
def test_debut():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('').use_text_mode()

    command = stage.add_command("DEBUT")
    assert_that(Command.possible_types("DEBUT"), empty())

    #------------------------------------------------------------------------------
    def assign_incompatible_type(): command.printable_type = "modele_sdaster"
    assert_that(assign_incompatible_type, raises(Exception))

    assert_that(command.printable_type, equal_to(''))

#------------------------------------------------------------------------------
def test_dependency_errors():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('text').use_text_mode()
    stage.add_command("LIRE_MAILLAGE", "MAIL_Q")

    #------------------------------------------------------------------------------
    stage2 = case.create_stage('graphical')
    assert_that(stage2.is_graphical_mode(), equal_to(True))
    text2 = \
"""
MODELUPQ = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)
"""
    comm2study(text2, stage2)
    assert_that(stage2.is_graphical_mode(), equal_to(True))

    #------------------------------------------------------------------------------
    del stage["MAIL_Q"]
    assert_that(stage2.check(), equal_to(Validity.Dependency))
    assert_that(case.check(), equal_to(Validity.Dependency))

#------------------------------------------------------------------------------
def test_no_syntaxic_errors():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('text').use_text_mode()
    stage.add_command("MODI_MAILLAGE", "MAIL")

    assert_that(stage.check(), equal_to(Validity.Ok))

    #------------------------------------------------------------------------------
    stage2 = case.create_stage('graphical')
    stage2.add_command("MODI_MAILLAGE", "MAIL")

    assert_that(stage2.check(), equal_to(Validity.Syntaxic))

#------------------------------------------------------------------------------
def test_naming_conflict_4_consequitive_text_stage():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('graphical')
    text = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=22)
"""
    comm2study(text, stage)

    #------------------------------------------------------------------------------
    stage2 = case.create_stage('text').use_text_mode()
    stage2.add_command("LIRE_MAILLAGE", "MAIL_Q")

    assert_that(stage2.check(), equal_to(Validity.Naming))
    assert_that(case.check(), equal_to(Validity.Naming))

#------------------------------------------------------------------------------
def test_naming_conflict_4_consequitive_graphical_stage():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('text').use_text_mode()
    stage.add_command("LIRE_MAILLAGE", "MAIL_Q")

    #------------------------------------------------------------------------------
    stage2 = case.create_stage('graphical')
    text2 = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=22)
"""
    comm2study(text2, stage2)

    assert_that(stage2.check(), equal_to(Validity.Naming))
    assert_that(case.check(), equal_to(Validity.Naming))

#------------------------------------------------------------------------------
def test_graphical_stage_convert_2_text():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'), DEBUG=_F(SDVERI='OUI'))

MAIL_Q = LIRE_MAILLAGE(UNITE=22)
"""
    comm2study(text, stage)
    assert_that("MAIL_Q", is_in(stage))
    assert_that(stage, has_length(2))

    #------------------------------------------------------------------------------
    stage2 = case.create_stage('2')
    text2 = \
"""
MODELUPQ = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)
"""
    comm2study(text2, stage2)

    #------------------------------------------------------------------------------
    stage.use_text_mode()
    assert_that(stage.is_text_mode(), equal_to(True))
    assert_that("MAIL_Q", is_in(stage))

    assert_that(stage2.check(), equal_to(Validity.Ok))
    assert_that(case.check(), equal_to(Validity.Ok))

#------------------------------------------------------------------------------
def test_text_2_graphical_2_text_conversion():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('').use_text_mode()
    text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET'),
      DEBUG=_F(SDVERI='OUI'))
"""
    stage.set_text(text)
    assert_that(stage.nb_commands, equal_to(0))
    assert_that(stage, has_length(2))

    stage.add_command("LIRE_MAILLAGE", "MAIL_Q")
    assert_that("MAIL_Q", is_in(stage))
    assert_that(stage.nb_commands, equal_to(1))

    #------------------------------------------------------------------------------
    stage.use_graphical_mode()
    assert_that(stage.is_graphical_mode(), equal_to(True))

    assert_that(stage, has_length(1))
    assert_that(stage[0].title, equal_to("DEBUT"))

    #------------------------------------------------------------------------------
    stage.use_text_mode()
    assert_that(stage.nb_commands, equal_to(1))
    assert_that(stage, has_length(2))
    assert_that(stage[0].title, equal_to("DEBUT"))

#------------------------------------------------------------------------------
def test_broken_text_2_graphical_conversion():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('1').use_text_mode()
    text = \
"""
@ % ^ &
"""
    stage.set_text(text)
    assert_that(stage.nb_commands, equal_to(0))
    assert_that(stage, has_length(1))

    stage.add_command("LIRE_MAILLAGE", "MAIL_Q")
    assert_that("MAIL_Q", is_in(stage))
    assert_that(stage.nb_commands, equal_to(1))

    #------------------------------------------------------------------------------
    stage2 = case.create_stage('2')
    text2 = \
"""
MODELUPQ = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)
"""
    comm2study(text2, stage2)
    assert_that(stage2.check(), equal_to(Validity.Ok))

    #------------------------------------------------------------------------------
    assert_that(calling(stage.use_graphical_mode), raises(Exception))
    assert_that(stage.is_graphical_mode(), equal_to(False))

    assert_that(stage, has_length(1))
    assert_that("MAIL_Q", is_in(stage))
    assert_that(stage2.check(), equal_to(Validity.Ok))

    #------------------------------------------------------------------------------
    stage2["MODELUPQ"].reset_validity()
    assert_that(stage2.check(), equal_to(Validity.Ok))

#------------------------------------------------------------------------------
def test_keep_dependencies():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=22)
"""
    comm2study(text, stage)

    #------------------------------------------------------------------------------
    stage2 = case.create_stage('2')
    text2 = \
"""
MODELUPQ = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)
"""
    comm2study(text2, stage2)

    #------------------------------------------------------------------------------
    assert_that(stage2.check(), equal_to(Validity.Ok))
    stage.use_text_mode()
    assert_that(stage2.check(), equal_to(Validity.Ok))

#------------------------------------------------------------------------------
def test_update_dependencies():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('1')
    text = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=22)
"""
    comm2study(text, stage)

    #------------------------------------------------------------------------------
    stage2 = case.create_stage('2')
    text2 = \
"""
MODELUPQ = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)
"""
    comm2study(text2, stage2)

    #------------------------------------------------------------------------------
    assert_that(stage2.check(), equal_to(Validity.Ok))
    stage.use_text_mode()
    stage.use_graphical_mode()
    assert_that(stage2.check(), equal_to(Validity.Dependency))

#------------------------------------------------------------------------------
def test_command_suppression():
    history = History()
    case = history.current_case

    #------------------------------------------------------------------------------
    stage = case.create_stage('')
    text = \
"""
MAIL_Q = LIRE_MAILLAGE(UNITE=22)
"""
    comm2study(text, stage)

    #------------------------------------------------------------------------------
    stage2 = case.create_stage('2').use_text_mode()

    #------------------------------------------------------------------------------
    stage3 = case.create_stage('3')
    text3 = \
"""
MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=MAIL_Q)
"""
    comm2study(text3, stage3)

    assert_that('MAIL_Q', is_in(stage3['MODELUPG'].previous_names()))

    #------------------------------------------------------------------------------
    destroy = stage2.add_command('DETRUIRE', '_')
    assert_that(stage2.nb_commands, equal_to(1))
    assert_that(stage2, has_length(0))

    preceding = list(stage2.preceding_stages)[-1]
    destroy['CONCEPT']['NOM'] = preceding['MAIL_Q']

    assert_that('MAIL_Q', is_not(is_in(stage3['MODELUPG'].previous_names())))

    #------------------------------------------------------------------------------
    destroy.delete()
    assert_that(stage2, has_length(0))

    assert_that('MAIL_Q', is_in(stage3['MODELUPG'].previous_names()))

#------------------------------------------------------------------------------
def test_lookup_with_detruire():
    history = History()
    case = history.current_case

    stage = case.create_stage('')
    text = \
"""
mesh = LIRE_MAILLAGE()
"""
    comm2study(text, stage)

    stage2 = case.create_stage('2')
    text2 = \
"""
model = AFFE_MODELE(MAILLAGE=mesh,
    AFFE=_F(MODELISATION='3D', PHENOMENE='MECANIQUE', TOUT='OUI'),
)

DETRUIRE(CONCEPT=_F(NOM=mesh))

model2 = AFFE_MODELE(MAILLAGE=mesh,
    AFFE=_F(MODELISATION='3D', PHENOMENE='MECANIQUE', TOUT='OUI'),
)
"""
    comm2study(text2, stage2)

    mesh = stage['mesh']
    model = stage2['model']
    model2 = stage2['model2']
    destroy = [cmd for cmd in stage2 if cmd.is_deleter][0]
    assert_that(destroy.title, equal_to('DETRUIRE'))

    assert_that(model.check(), equal_to(Validity.Nothing))
    assert_that(destroy.depends_on(mesh), equal_to(True))
    assert_that(model2.depends_on(destroy), equal_to(True))
    assert_that(model2.check(), equal_to(Validity.Dependency))

    # commands available before DETRUIRE
    before_destroy = stage2.preceding_commands(destroy)
    assert_that(before_destroy, has_length(2))
    assert_that(mesh, is_in(before_destroy))

    # meshes available before DETRUIRE
    mesh_before_destroy = destroy.groupby(mesh.type)
    assert_that(mesh_before_destroy, has_length(1))
    assert_that(mesh, is_in(before_destroy))

    # commands available after DETRUIRE (before model2)
    after_destroy = stage2.preceding_commands(model2)
    assert_that(model, is_in(after_destroy))
    assert_that(destroy, is_in(after_destroy))
    assert_that(after_destroy, has_length(2))

    # meshes available after DETRUIRE (before model2)
    mesh_after_destroy = model2.groupby(mesh.type)
    assert_that(mesh_after_destroy, has_length(0))
    assert_that(mesh, is_not(is_in(after_destroy)))


def test_validity_with_detruire():
    history = History()
    case = history.current_case

    stage = case.create_stage('')
    text = \
"""
mesh = LIRE_MAILLAGE()
"""
    comm2study(text, stage)

    stage2 = case.create_stage('2')
    text2 = \
"""
DETRUIRE(CONCEPT=_F(NOM=mesh))
"""
    comm2study(text2, stage2)

    stage3 = case.create_stage('3')
    text3 = \
"""
model = AFFE_MODELE(
    AFFE=_F(MODELISATION='AXIS_INCO_UPG', PHENOMENE='MECANIQUE', TOUT='OUI'),
    MAILLAGE=mesh
)
"""
    comm2study(text3, stage3)

    assert_that(stage3['model'].check(), equal_to(Validity.Dependency))


def test_issue_1761():
    history = History()
    case = history.current_case

    stage = case.create_stage('stage')
    stage.add_command('LIRE_MAILLAGE', 'MAIL')
    assert_that(stage.check(), equal_to(Validity.Ok))

    stage_2 = case.create_stage('stage_2')
    destroy = stage_2.add_command('DETRUIRE', '_')
    destroy['CONCEPT']['NOM'] = stage['MAIL']
    assert_that(stage.check(), equal_to(Validity.Ok))
    assert_that(stage_2, has_length(1))

    stage_3 = case.create_stage('stage_3')
    mesh = stage_3.add_command('LIRE_MAILLAGE', 'MAIL')
    mesh.init({})
    assert_that(stage_3.check(), equal_to(Validity.Ok))

    destroy.delete()
    assert_that(stage_2, has_length(0))
    assert_that(mesh.check(), equal_to(Validity.Naming))
    assert_that(stage_3.check(), equal_to(Validity.Naming))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
