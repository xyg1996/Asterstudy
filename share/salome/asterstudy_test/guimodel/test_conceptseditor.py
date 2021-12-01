# coding=utf-8

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

"""Automatic tests for concepts editor (issue 1684)."""


import unittest

from PyQt5 import Qt as Q

import testutils.gui_utils
from asterstudy.datamodel import History, Validity
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.gui import HistoryProxy
from asterstudy.gui.behavior import behavior
from asterstudy.gui.datasettings import create_data_settings_model
from asterstudy.gui.widgets.conceptseditor import ConceptsEditor
from common_test_gui import HistoryHolder, get_application
from hamcrest import *

stage1_text = \
"""
mesh1 = LIRE_MAILLAGE(UNITE=22)
mesh2 = LIRE_MAILLAGE(UNITE=22)
"""

# snippet based on the file "data/comm2code/comp001a.comm"
# with manually added command DETRUIRE in the end
stage2_text = \
"""
DEBUT(CODE=_F(NIV_PUB_WEB='INTERNET',),IMPR_MACRO='OUI');

# donnee materiau et fonction


#parametres elastiques
YOUNG = 200000.0;
POISSON = 0.3;

#parametres loi ISOT_LINE
SY = 437.0;
pente = 2024.74690664;

#unite en Pa
C_Pa = 1.e+6
#C_Pa = 1.
YOUNG_Pa = YOUNG * C_Pa
pente_Pa = pente * C_Pa
SY_Pa = SY * C_Pa;

acier0 = DEFI_MATERIAU(ELAS=_F(E=YOUNG_Pa,
                               NU=POISSON,
                               ALPHA=11.8e-6),
                    ECRO_LINE=_F(D_SIGM_EPSI=pente_Pa,
                                 SY=SY_Pa,),);
#unite en MPa
acier1 = DEFI_MATERIAU(ELAS=_F(E=YOUNG,
                               NU=POISSON,
                               ALPHA=11.8e-6),
                    ECRO_LINE=_F(D_SIGM_EPSI=pente,
                                 SY=SY,),)

compor='VMIS_ISOT_LINE'

DETRUIRE(CONCEPT=_F(NOM=mesh1, ))

tabresu=TEST_COMPOR(OPTION='MECA',

              COMPORTEMENT=_F(RELATION=compor,),
              NEWTON=_F(REAC_ITER=1),
              LIST_MATER=(acier0, acier1),
              VARI_TEST=('V1','VMIS','TRACE'),
              YOUNG=YOUNG,POISSON=POISSON,
              )


FIN();
"""

stage3_text = \
"""
MODELUPG = AFFE_MODELE(AFFE=_F(MODELISATION='AXIS_INCO_UPG',
                               PHENOMENE='MECANIQUE',
                               TOUT='OUI'),
                       MAILLAGE=mesh1)
"""

def setup():
    """required to create widgets"""
    get_application()

def dump(table):
    print()
    print(table.model().rowCount())
    print(table.model().columnCount())
    for i in range(table.model().rowCount()):
        data = [table.model().index(i,j).data(Q.Qt.EditRole) \
                    for j in range(table.model().columnCount())]
        print("{0} by {1} of type {2}".format(*data))

def _init():
    """Initialize model and concepts editor"""

    behavior().use_business_translations = True

    history = History()
    case = history.current_case

    stage1 = case.create_stage('Stage1')
    comm2study(stage1_text, stage1)

    stage2 = case.create_stage('Stage2')
    comm2study(stage2_text, stage2)
    stage2.use_text_mode()

    stage3 = case.create_stage('Stage3')
    comm2study(stage3_text, stage3)

    cmodel = create_data_settings_model(HistoryHolder(history))
    cmodel.update()

    editor = ConceptsEditor(stage2, None)

    return (stage1, stage2, stage3, editor)

def test_common_features():
    """Test for concepts editor (common features)"""
    (stage1, stage2, stage3, editor) = _init()
    table = editor.table
    model = table.model()

    # the table will contain the following concepts:
    # YOUNG    | Variable      | Real
    # POISSON  | Variable      | Real
    # SY       | Variable      | Real
    # pente    | Variable      | Real
    # C_Pa     | Variable      | Real
    # YOUNG_Pa | Variable      | Real
    # pente_Pa | Variable      | Real
    # SY_Pa    | Variable      | Real
    # compo    | Variable      | Text
    # acier0   | DEFI_MATERIAU | master_sdaster
    # acier1   | DEFI_MATERIAU | master_sdaster
    # tabresu  | TEST_COMPOR   | table_sdaster
    assert_that(model.rowCount(), equal_to(12))
    assert_that(model.columnCount(), equal_to(3))

    # check NameDelegate
    index = model.index(0, 0)
    table.openPersistentEditor(index)
    table.closePersistentEditor(index)

    # check CommandDelegate
    index = model.index(0, 1)
    table.openPersistentEditor(index)
    table.closePersistentEditor(index)

    # check TypeDelegate
    item = model.index(0, 2)
    table.openPersistentEditor(item)
    table.closePersistentEditor(item)

    # check read-only mode
    editor.setReadOnly(True)
    assert_that(table.editTriggers() == Q.QAbstractItemView.NoEditTriggers,
                equal_to(True))
    editor.setReadOnly(False)
    assert_that(table.editTriggers() == Q.QAbstractItemView.NoEditTriggers,
                equal_to(False))

    # check that apply is not allowed (no modifications made)
    assert_that(editor.isApplyAllowed(), equal_to(False))

    # check that apply is not allowed (the table has invalid empty cell)
    model.setData(model.index(2, 0), "", Q.Qt.EditRole)
    assert_that(editor.isApplyAllowed(), equal_to(False))

    # check that apply is allowed (the table cell has been modified)
    model.setData(model.index(2, 0), "tabresu", Q.Qt.EditRole)
    assert_that(editor.isApplyAllowed(), equal_to(True))

    # check ConceptsEditor.updateTranslations()
    behavior().use_business_translations = False
    editor.updateTranslations()

    # check ConceptsEditor.cellChanged()
    model.setData(model.index(2, 1), "STAT_NON_LINE", Q.Qt.EditRole) # type is changed to evol_noli
    prod = model.index(2, 2).data()
    assert_that(prod, equal_to("evol_noli"))

def test_add_remove_command():
    """Test for concepts editor (add/remove command)"""
    (stage1, stage2, stage3, editor) = _init()
    table = editor.table
    model = table.model()

    # check command addition
    editor.add()
    assert_that(model.rowCount(), equal_to(13))

    # check command removing; negative case: no selection
    table.clearSelection()
    editor.remove()
    assert_that(model.rowCount(), equal_to(13))

    # check command removing; positive case
    table.setCurrentIndex(model.index(12, 0))
    editor.remove()
    assert_that(model.rowCount(), equal_to(12))

def test_concepts_to_add():
    """Test for concepts editor (change and apply 'Concepts to add')"""
    (stage1, stage2, stage3, editor) = _init()
    table = editor.table
    model = table.model()

    # case 1:
    # "tabresu | TEST_COMPOR | table_sdaster" changed to
    # "tabresu | STAT_NON_LINE | evol_noli"
    model.setData(model.index(2, 1), "STAT_NON_LINE", Q.Qt.EditRole)
    editor.applyChanges()

    # case 2:
    # "tabresu | STAT_NON_LINE | evol_noli" changed to
    # "tabresu | STAT_NON_LINE | table_sdaster" (invalid case)
    model.setData(model.index(2, 2), "table_sdaster", Q.Qt.EditRole)
    try:
        editor.applyChanges()
    except AssertionError:
        model.setData(model.index(2, 2), "evol_noli", Q.Qt.EditRole) # reset valid value

    # case 3:
    # add new command "test | LIRE_MAILLAGE | ..."
    editor.add()
    model.setData(model.index(3, 0), "test", Q.Qt.EditRole)
    assert_that(model.index(3, 0).data(Q.Qt.DisplayRole), equal_to("test"))
    assert_that(model.index(3, 0).data(Q.Qt.EditRole), equal_to("test"))
    assert_that(model.index(3, 0).data(Q.Qt.ToolTipRole), none())
    model.setData(model.index(3, 1), "LIRE_MAILLAGE", Q.Qt.EditRole)
    assert_that(model.index(3, 1).data(Q.Qt.DisplayRole), equal_to("Read a mesh (LIRE_MAILLAGE)"))
    assert_that(model.index(3, 1).data(Q.Qt.EditRole), equal_to("LIRE_MAILLAGE"))
    assert_that(model.index(3, 1).data(Q.Qt.ToolTipRole), none())
    assert_that(model.index(3, 2).data(Q.Qt.DisplayRole), equal_to("maillage"))
    assert_that(model.index(3, 2).data(Q.Qt.EditRole), equal_to("maillage_sdaster"))
    assert_that(model.index(3, 2).data(Q.Qt.ToolTipRole), none())
    editor.applyChanges()
    assert_that("test" in stage2, equal_to(True))

    # case 4:
    # remove last command "test | LIRE_MAILLAGE | ..."
    table.setCurrentIndex(model.index(3, 0))
    editor.remove()
    editor.applyChanges()
    assert_that("test" in stage2, equal_to(False))

def test_concepts_to_delete():
    """Test for concepts editor (change and apply 'Concepts to delete')"""
    (stage1, stage2, stage3, editor) = _init()
    list_widget = editor.list_widget

    # uncheck (enable) concept "mesh1" and check (disable) concept "mesh2"
    assert_that("mesh1", is_not(is_in(stage3["MODELUPG"].previous_names())))
    assert_that("mesh2", is_in(stage3["MODELUPG"].previous_names()))

    list_widget.item(0).setCheckState(Q.Qt.Unchecked) # enable "mesh1"
    list_widget.item(1).setCheckState(Q.Qt.Checked) # disable "mesh2"
    editor.applyChanges()

    assert_that("mesh1", is_in(stage3["MODELUPG"].previous_names()))
    assert_that("mesh2", is_not(is_in(stage3["MODELUPG"].previous_names())))

stage4_text = \
"""
MAIL = LIRE_MAILLAGE(FORMAT='MED',
                     UNITE=20)

MAIL = MODI_MAILLAGE(reuse=MAIL,
                     MAILLAGE=MAIL,
                     ORIE_PEAU_2D=_F(GROUP_MA='haut'))

MODE = AFFE_MODELE(AFFE=_F(MODELISATION='C_PLAN',
                           PHENOMENE='MECANIQUE',
                           TOUT='OUI'),
                   MAILLAGE=MAIL)
"""

def test_1759():
    """Test for the issue 1759
    (broken dependencies after apply in ConceptsEditor)"""
    history = History()
    case = history.current_case

    stage4 = case.create_stage('Stage4')
    comm2study(stage4_text, stage4)

    stage4.use_text_mode()

    cmodel = create_data_settings_model(HistoryHolder(history))
    cmodel.update()

    editor = ConceptsEditor(stage4, None)

    assert_that(stage4.check(), equal_to(Validity.Nothing))

    editor.applyChanges()

    assert_that(stage4.check(), equal_to(Validity.Nothing))

stage5_text = \
"""
xxx = ASSEMBLAGE(
  NUME_DDL=CO('aaa'),
  VECT_ASSE=_F(
    OPTION='CHAR_ACOU',
    VECTEUR=CO('bbb')
  ),
  MATR_ASSE=_F(
    MATRICE=CO('ccc'),
    OPTION='AMOR_ACOU'
  ),
)
"""

def test_hidden():
    """Test for concepts editor (manage Hidden commands)"""
    history = History()
    case = history.current_case

    stage5 = case.create_stage('Stage4')
    comm2study(stage5_text, stage5)

    stage5.use_text_mode()

    cmodel = create_data_settings_model(HistoryHolder(history))
    cmodel.update()

    editor = ConceptsEditor(stage5, None)
    table = editor.table
    model = table.model()

    # the order may change (keyword args order is not stable in py2)
    expected = {
        'aaa': ('ASSEMBLAGE', 'nume_ddl_sdaster'),
        'bbb': ('ASSEMBLAGE', 'cham_no_sdaster'),
        'ccc': ('ASSEMBLAGE', 'matr_asse_pres_c'),
    }
    assert_that(model.rowCount(), equal_to(len(expected)))

    i = -1
    while expected:
        i += 1
        name = model.index(i, 0).data(Q.Qt.EditRole)
        cmd, typ = expected.pop(name)
        assert_that(model.index(i, 1).data(Q.Qt.EditRole), equal_to(cmd))
        assert_that(model.index(i, 2).data(Q.Qt.EditRole), equal_to(typ))
    # ensure that all values were checked
    assert_that(expected, has_length(0))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
