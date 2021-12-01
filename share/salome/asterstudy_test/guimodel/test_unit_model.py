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

"""Automatic tests for unit model."""


import unittest

import os
import os.path as osp

from PyQt5.Qt import Qt
from PyQt5 import Qt as Q

from asterstudy.gui.unit_model import UnitModel, NoSalomeProxyModel
from asterstudy.gui import Role

from asterstudy.datamodel.comm2study import comm2study

from hamcrest import *
from testutils import tempdir
import testutils.gui_utils

FileData_file = 0
FileData_embedded = 4

def _mock_validation(model, file_model, newname, state, unit):
    """Mock validation in UnitPanel."""
    stage_index = model.index(1, 0, Q.QModelIndex())
    row = file_model.unit2index(unit).row()
    index = model.index(row, 0, stage_index)
    obj = index.data(Role.CustomRole)
    obj.filename = newname
    obj.embedded = state
    file_model.transferFile(newname)
    model.update()


@tempdir
def test_external_to_embedded(tmpdir):
    """
    Test the conversion from external to embedded file in the Qt model
    """
    from asterstudy.gui.study import Study
    study = Study(None)

    # get the Qt model, interface to access data in `datamodel.file_descriptors`
    # this is a Stage hierarchy of tables
    # rows are Info objects, column properties of Info objects
    model = study.dataFilesModel()

    # populate the history with new objects, including files
    history = study.history
    history.folder = tmpdir
    cc = history.current_case
    cc.name = 'cc'
    st1 = cc.create_stage('st1')

    # the following imports a mesh, adds a group and writes the new mesh
    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

mesh2 = DEFI_GROUP(MAILLAGE=mesh,
                   CREA_GROUP_MA=_F(NOM='VOLUM',
                                    TOUT='OUI',
                                    TYPE_MAILLE='3D'))

IMPR_RESU(UNITE=80,
          FORMAT='MED',
          RESU=_F(MAILLAGE=mesh2))
"""

    comm2study(text1, st1)

    # define in and out files
    infile = osp.join(tmpdir, 'dummy_in.txt')
    open(infile, 'a').close()
    outfile = '/my/path/dummy.txt'
    st1['mesh']['UNITE'].value = {20: infile}
    st1[2]['UNITE'].value = {80: outfile}

    assert_that(st1.handle2info[20].embedded, equal_to(False))
    assert_that(st1.handle2info[80].embedded, equal_to(False))

    # update the Qt model
    model.update()

    # create a UnitModel for these files
    # there is no hierarchy in this model, just one table
    file_model = UnitModel(st1)
    assert_that(file_model.rowCount(), equal_to(2))
    assert_that(file_model.columnCount(), equal_to(1))

    # QModelIndex corresponding to each item in the model
    in_index = file_model.unit2index(20)
    out_index = file_model.unit2index(80)

    # get corresponding data
    # `IdRole` returns the logical unit
    unit = file_model.data(in_index, Role.IdRole)
    assert_that(unit, equal_to(20))

    # `Qt.ToolTipRole` returns the full path to the file
    filename = file_model.data(in_index, Qt.ToolTipRole)
    assert_that(filename, equal_to(infile))

    # `Qt.DisplayRole` and `Qt.EditRole` are the same to us, they return the basename
    basename = file_model.data(in_index, Qt.DisplayRole)
    assert_that(basename, equal_to(osp.basename(infile)))
    basename = file_model.data(in_index, Qt.EditRole)
    assert_that(basename, equal_to(osp.basename(infile)))

    # now, let us try to embedd the file from the Qt model
    inpath = file_model.ext2emb(infile)

    # assert the path accessed from the Qt model is changed
    # but the data model is not yet changed, nor is the file copied (user has to validate for that)
    testpath = osp.join(history.tmpdir, osp.basename(infile))
    assert_that(inpath, equal_to(testpath))

    accessed = file_model.data(in_index, Qt.ToolTipRole)
    assert_that(accessed, equal_to(testpath))

    testname = st1.handle2info[20].filename
    assert_that(testname, equal_to(infile))
    assert_that(testname, is_not(equal_to(inpath)))

    assert_that(osp.isfile(inpath), equal_to(False))

    # same test for the output file
    outpath = file_model.ext2emb(outfile)
    testpath = osp.join(history.tmpdir, osp.basename(outpath))
    assert_that(outpath, equal_to(testpath))

    accessed = file_model.data(out_index, Qt.ToolTipRole)
    assert_that(accessed, equal_to(testpath))

    testname = st1.handle2info[80].filename
    assert_that(testname, equal_to(outfile))
    assert_that(testname, is_not(equal_to(outpath)))

    # now, the user validates
    # the following mimics the code in gui.datafiles.unitpanel when validating
    _mock_validation(model, file_model, inpath, True, 20)
    _mock_validation(model, file_model, outpath, True, 80)

    # check that everything is changed this time
    testname = st1.handle2info[20].filename
    assert_that(testname, equal_to(inpath))
    assert_that(testname, is_not(equal_to(infile)))

    # file has been copied, not moved
    assert_that(osp.isfile(inpath), equal_to(True))
    assert_that(osp.isfile(infile), equal_to(True))

    # same test for the output file
    testname = st1.handle2info[80].filename
    assert_that(testname, equal_to(outpath))
    assert_that(testname, is_not(equal_to(outfile)))

    # access from `model`
    stage_index = model.index(1, 0, Q.QModelIndex())

    in_index_name = model.index(in_index.row(), FileData_file, stage_index)
    data = model.data(in_index_name, Qt.ToolTipRole)
    assert_that(data, equal_to('File: ' + inpath + ' (embedded)'))
    data = model.data(in_index_name, Qt.DisplayRole)
    assert_that(data, equal_to(osp.basename(inpath) + ' (embedded)'))

    out_index_name = model.index(out_index.row(), FileData_file, stage_index)
    data = model.data(out_index_name, Qt.ToolTipRole)
    assert_that(data, equal_to('File: ' + outpath + ' (embedded)'))


@tempdir
def test_conflicts_embedded(tmpdir):
    """Test an error is raised in case of conflicts when embedding a file"""
    from asterstudy.gui.study import Study
    study = Study(None)

    # get the Qt model, interface to access data in `datamodel.file_descriptors`
    # this is a Stage hierarchy of tables
    # rows are Info objects, column properties of Info objects
    model = study.dataFilesModel()

    # populate the history with new objects, including files
    history = study.history
    history.folder = tmpdir

    cc = history.current_case
    cc.name = 'cc'
    st1 = cc.create_stage('st1')

    # the following imports a mesh, adds a group and writes the new mesh
    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

mesh2 = DEFI_GROUP(MAILLAGE=mesh,
                   CREA_GROUP_MA=_F(NOM='VOLUM',
                                    TOUT='OUI',
                                    TYPE_MAILLE='3D'))

IMPR_RESU(UNITE=80,
          FORMAT='MED',
          RESU=_F(MAILLAGE=mesh2))
"""

    comm2study(text1, st1)

    # define in and out files, as if they were external
    # create the second file with the same basename on purpose
    infile = osp.join(tmpdir, 'dummy_in.txt')
    open(infile, 'a').close()

    outfile = osp.join('/my/dummy/path', osp.basename(infile))
    st1['mesh']['UNITE'].value = {20: infile}
    st1[2]['UNITE'].value = {80: outfile}
    assert_that(st1.handle2info[20].embedded, equal_to(False))
    assert_that(st1.handle2info[80].embedded, equal_to(False))

    model.update()

    # create a UnitModel
    file_model = UnitModel(st1)

    # try to embed two files in a row
    # check it errors (same basename)
    emb1 = file_model.ext2emb(infile)
    assert_that(calling(file_model.ext2emb).with_args(outfile), raises(ValueError))

    # try to embed a file, validate, embed the second
    # check it errors
    _mock_validation(model, file_model, emb1, True, 80)

    # the following simulates the generation of the unit editor
    file_model = UnitModel(st1)

    assert_that(calling(file_model.ext2emb).with_args(outfile), raises(ValueError))


@tempdir
def test_embedded_to_external(tmpdir):
    """
    Test conversion from embedded to external
    """
    from asterstudy.gui.study import Study
    study = Study(None)

    model = study.dataFilesModel()
    history = study.history
    history.folder = tmpdir

    cc = history.current_case
    cc.name = 'cc'
    st1 = cc.create_stage('st1')

    # the following imports a mesh, adds a group and writes the new mesh
    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

mesh2 = DEFI_GROUP(MAILLAGE=mesh,
                   CREA_GROUP_MA=_F(NOM='VOLUM',
                                    TOUT='OUI',
                                    TYPE_MAILLE='3D'))

IMPR_RESU(UNITE=80,
          FORMAT='MED',
          RESU=_F(MAILLAGE=mesh2))
"""

    comm2study(text1, st1)

    # define in and out files, as if they were embedded
    embdir = history.tmpdir
    assert_that(os.listdir(embdir), equal_to([]))

    infile = osp.join(embdir, 'dummy_in.txt')
    open(infile, 'a').close()
    assert_that(osp.isfile(infile), equal_to(True))

    outfile = osp.join(embdir, 'dummy_out.txt')
    assert_that(osp.isfile(outfile), equal_to(False))

    # create the second file with the same basename on purpose
    st1['mesh']['UNITE'].value = {20: infile}
    st1[2]['UNITE'].value = {80: outfile}

    st1.handle2info[20].embedded = True
    st1.handle2info[80].embedded = True

    model.update()

    file_model = UnitModel(st1)

    # try to externalize both files
    indest = osp.join(tmpdir, 'indest')
    outdest = osp.join(tmpdir, 'outdest')
    file_model.emb2ext(infile, indest)
    file_model.emb2ext(outfile, outdest)

    # check that the path accessed from the Qt model is changed
    first_index = file_model.unit2index(20)
    inpath = file_model.data(first_index, Qt.ToolTipRole)
    assert_that(inpath, equal_to(indest))
    second_index = file_model.unit2index(80)
    outpath = file_model.data(second_index, Qt.ToolTipRole)
    assert_that(outpath, equal_to(outdest))

    # but no changes to data model yet
    assert_that(st1.handle2info[20].filename, equal_to(infile))
    assert_that(st1.handle2info[80].filename, equal_to(outfile))
    assert_that(osp.isfile(indest), equal_to(False))
    assert_that(osp.isfile(infile), equal_to(True))

    # validate changes
    _mock_validation(model, file_model, indest, False, 20)
    _mock_validation(model, file_model, outdest, False, 80)

    # check changes have been applied to the datamodel
    assert_that(st1.handle2info[20].filename, equal_to(indest))
    assert_that(st1.handle2info[80].filename, equal_to(outdest))

    # check the file has been moved, not copied
    assert_that(osp.isfile(indest), equal_to(True))
    assert_that(osp.isfile(infile), equal_to(False))

@tempdir
def test_conflicts_external(tmpdir):
    """Test an error is raised in case of a conflicts in external files."""

    from asterstudy.gui.study import Study
    study = Study(None)

    # get the Qt model, interface to access data in `datamodel.file_descriptors`
    # this is a Stage hierarchy of tables
    # rows are Info objects, column properties of Info objects
    model = study.dataFilesModel()

    # populate the history with new objects, including files
    history = study.history
    history.folder = tmpdir

    cc = history.current_case
    cc.name = 'cc'
    st1 = cc.create_stage('st1')

    # the following imports a mesh, adds a group and writes the new mesh
    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

mesh2 = DEFI_GROUP(MAILLAGE=mesh,
                   CREA_GROUP_MA=_F(NOM='VOLUM',
                                    TOUT='OUI',
                                    TYPE_MAILLE='3D'))

IMPR_RESU(UNITE=80,
          FORMAT='MED',
          RESU=_F(MAILLAGE=mesh2))
"""

    comm2study(text1, st1)

    # create in and out files, as if they were embedded
    embdir = history.tmpdir
    assert_that(os.listdir(embdir), equal_to([]))

    infile = osp.join(embdir, 'dummy_in.txt')
    open(infile, 'a').close()
    outfile = osp.join(embdir, 'dummy_out.txt')

    st1['mesh']['UNITE'].value = {20: infile}
    st1.handle2info[20].embedded = True

    st1[2]['UNITE'].value = {80: outfile}
    st1.handle2info[80].embedded = True

    # make the Qt model in line with the data model
    model.update()

    # create a unit model
    file_model = UnitModel(st1)

    # try to externalize both files with the same path
    path = osp.join(tmpdir, 'other_path')
    open(path, 'a').close()
    inpath = file_model.emb2ext(infile, path)
    assert_that(calling(file_model.emb2ext).with_args(outfile, path), raises(ValueError))

    # try to validate, then externalize the second
    # check an error is raised
    _mock_validation(model, file_model, path, False, 20)
    assert_that(calling(file_model.emb2ext).with_args(outfile, path), raises(ValueError))


@tempdir
def test_back_conversion(tmpdir):
    """Test changing embedded state several times before validating is ok."""

    from asterstudy.gui.study import Study
    study = Study(None)

    # get the Qt model, interface to access data in `datamodel.file_descriptors`
    # this is a Stage hierarchy of tables
    # rows are Info objects, column properties of Info objects
    model = study.dataFilesModel()

    # populate the history with new objects, including files
    history = study.history
    history.folder = tmpdir

    cc = history.current_case
    cc.name = 'cc'
    st1 = cc.create_stage('st1')

    # the following imports a mesh, adds a group and writes the new mesh
    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

mesh2 = DEFI_GROUP(MAILLAGE=mesh,
                   CREA_GROUP_MA=_F(NOM='VOLUM',
                                    TOUT='OUI',
                                    TYPE_MAILLE='3D'))

IMPR_RESU(UNITE=80,
          FORMAT='MED',
          RESU=_F(MAILLAGE=mesh2))
"""

    comm2study(text1, st1)

    # create an in file
    infile = osp.join(tmpdir, 'dummy_in.txt')
    open(infile, 'a').close()
    st1['mesh']['UNITE'].filename = infile

    model.update()
    file_model = UnitModel(st1)

    # try to convert it back and forth
    inpath = file_model.ext2emb(infile)
    testpath = file_model.emb2ext(inpath, infile)
    assert_that(testpath, equal_to(infile))
    testpath = file_model.ext2emb(infile)
    _mock_validation(model, file_model, testpath, True, 20)

    #
    assert_that(st1.handle2info[20].filename, equal_to(testpath))
    assert_that(st1.handle2info[20].embedded, equal_to(True))
    assert_that(osp.isfile(testpath), equal_to(True))

def _mock_find_data_rec(model, index, sdata, role):
    """Recursive simulation of the `findData` into a Qt model."""

    if index.isValid() and model.data(index, role) == sdata:
        return index.row()
    if index.isValid() and not model.hasChildren(index):
        return -1
    nrows = model.rowCount(index)
    ncols = model.columnCount(index)
    rlist = []
    for i in range(nrows):
        for j in range(ncols):
            rlist.append(_mock_find_data_rec(model, model.index(i, j, index), sdata, role))
    return max(rlist) if rlist else -1

def _mock_find_data(model, sdata, role):
    """Simulation of the `findData` into a Qt model."""
    root_index = Q.QModelIndex()
    return _mock_find_data_rec(model, root_index, sdata, role)


def _mock_set_current_filename(model, filename, orig_bname=None):
    """Simulate setCurrentFilename operation of the file path editor."""
    if filename:
        index = _mock_find_data(model, filename, Role.CustomRole)
        if index == -1:
            if model.basename_conflict(filename, orig_bname):
                return index
            try:
                unit = model.addItem(filename)
            except ValueError:
                return index
            else:
                return _mock_find_data(model, unit, Role.IdRole)
        else:
            return index
    else:
        return 0

@tempdir
def test_issue_26313(tmpdir):
    """Test basename conflicts, as happens from unit editor."""

    import os
    import os.path as osp
    from asterstudy.gui.study import Study
    study = Study(None)

    history = study.history
    cc = history.current_case
    st1 = cc.create_stage('st1')
    study.commit("initialize")

    fmodel = UnitModel(study.history.current_case['st1'])

    # create two subfolders in tmpdir
    # containg each a file with basename 'same.txt'
    bname = "same.txt"

    subfolder_1 = osp.join(tmpdir, "subfolder_1")
    os.mkdir(subfolder_1)
    path1 = osp.join(subfolder_1, bname)
    open(path1, 'a').close()

    subfolder_2 = osp.join(tmpdir, "subfolder_2")
    os.mkdir(subfolder_2)
    path2 = osp.join(subfolder_2, bname)
    open(path2, 'a').close()

    # simulates what happens when first folder is added:
    # setCurrentFilename is called
    # indexes are added starting from 0
    ind_1 = _mock_set_current_filename(fmodel, path1)
    assert_that(ind_1, equal_to(0))

    # simulate the validation of the command
    # assuming 2 was given as logical unit
    # also add another file, with valid name
    st1 = study.history.current_case['st1']
    st1.handle2info[2].filename = path1

    bname2 = 'different.txt'
    path3 = osp.join(subfolder_2, bname2)
    open(path3, 'a').close()
    st1.handle2info[20].filename = path3

    text1 = """
mesh = LIRE_MAILLAGE(UNITE=2, FORMAT='ASTER')

mesh2 = LIRE_MAILLAGE(UNITE=20, FORMAT='ASTER')
"""
    comm2study(text1, st1)
    study.commit("adding_file")
    fmodel = UnitModel(study.history.current_case['st1'])

    # simulate trying to give another file with identical basename
    index = _mock_set_current_filename(fmodel, path2)
    assert_that(index, equal_to(-1))

    # simulate changing dirname without changing basename
    index = _mock_set_current_filename(fmodel, path2, orig_bname=osp.basename(path2))
    assert_that(index, equal_to(2))

    # simulate trying to give the same file, sould yield the same index
    index = _mock_set_current_filename(fmodel, path1)
    assert_that(index, equal_to(ind_1))

    # simulate everything is ok with a valid file
    index = _mock_set_current_filename(fmodel, path3)
    assert_that(index, greater_than(0))

@tempdir
def test_issue_27535(tmpdir):
    """Test proxy models filtering out Salome objects"""
    from asterstudy.gui.study import Study
    study = Study(None)

    # get the Qt model, interface to access data in `datamodel.file_descriptors`
    # this is a Stage hierarchy of tables
    # rows are Info objects, column properties of Info objects
    model = study.dataFilesModel()

    # populate the history with new objects, including files
    history = study.history
    history.folder = tmpdir

    cc = history.current_case
    cc.name = 'cc'
    st1 = cc.create_stage('st1')

    # LIRE_MAILLAGE : IN and UnitMed type     => Salome references should be included
    # LIRE_FONCTION : IN but not UnitMed type => --------------------------- excluded
    # IMPR_RESU     : OUT                     => --------------------------- excluded
    text1 = \
"""
function=LIRE_FONCTION(UNITE=19,
                       NOM_PARA='INST',
                       INDIC_PARA=[1, 1],
                       INDIC_RESU=[1, 2]
                       )

mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')
"""

    comm2study(text1, st1)

    # create a standard file
    infile = osp.join(tmpdir, 'dummy_in.txt')
    open(infile, 'a').close()

    # mock a Salome reference
    inref = "0:1:2:3"
    st1['function']['UNITE'].value = {19: infile}
    st1['mesh']['UNITE'].value = {20: inref}

    model.update()

    # create a UnitModel
    file_model = UnitModel(st1)
    proxy_model = NoSalomeProxyModel(file_model)

    # Test data returned by the file model
    assert_that(file_model.rowCount(), equal_to(2))
    assert_that(file_model.columnCount(), equal_to(1))
    in_index = file_model.index(1, 0)
    basename = file_model.data(in_index, Qt.DisplayRole)
    assert_that(basename, equal_to(inref))

    # test data returned by the proxy model
    # There should be no reference (only 1 row)
    assert_that(proxy_model.rowCount(), equal_to(1))
    assert_that(proxy_model.columnCount(), equal_to(1))
    in_index = proxy_model.index(0, 0)
    basename = proxy_model.data(in_index, Qt.DisplayRole)
    assert_that(basename, equal_to(osp.basename(infile)))

    # Test helper functions
    ind = proxy_model.findDataHelper(basename, Qt.DisplayRole)
    assert_that(ind, equal_to(0))
    ind = proxy_model.findDataHelper("not_in_model", Qt.DisplayRole)
    assert_that(ind, equal_to(-1))
    bname = proxy_model.itemDataHelper(0, Qt.DisplayRole)
    assert_that(bname, equal_to(basename))
    invalid = proxy_model.itemDataHelper(-1, Qt.DisplayRole)
    assert_that(invalid, is_(None))
    invalid = proxy_model.itemDataHelper(1, Qt.DisplayRole)
    assert_that(invalid, is_(None))

    # Datamodel test of UnitMed type
    from asterstudy.datamodel.catalogs import CATA
    umed = CATA.package('DataStructure').UnitMed
    assert_that(st1['function']['UNITE'].gettype(), is_not(same_instance(umed)))
    assert_that(st1['mesh']['UNITE'].gettype(), same_instance(umed))

    # Test refresh
    proxy_model.refreshFromSource(file_model)
    assert_that(proxy_model.sourceModel(), same_instance(file_model))


def test_issue_29021():
    from asterstudy.datamodel import History
    from asterstudy.datamodel.general import FileAttr

    history = History()
    case = history.current_case
    case.name = 'Current'

    st1 = case.create_stage('st1')
    text1 = \
"""
func = DEFI_FONCTION(NOM_PARA='INST', VALE=(0.0, 0.0, 1.0, 10.0))

IMPR_FONCTION(COURBE=_F(FONCTION=func), UNITE=12)
"""
    comm2study(text1, st1)
    info12 = st1.handle2info[12]
    info12.filename = '/path/to/the_file'
    info12.attr = FileAttr.In

    model = UnitModel(st1)
    assert_that(model.rowCount(), equal_to(1))
    idx0 = model.index(0, 0)
    assert_that(model.data(idx0), equal_to('the_file'))
    assert_that(model.data(idx0, Role.IdRole), equal_to(12))
    assert_that(model.data(idx0, Role.CustomRole), equal_to('/path/to/the_file'))

    # check that file '12' is available in a second stage
    st2 = case.create_stage('st2')

    model = UnitModel(st2)
    assert_that(model.rowCount(), equal_to(1))
    idx0 = model.index(0, 0)
    assert_that(model.data(idx0), equal_to('the_file'))
    assert_that(model.data(idx0, Role.IdRole), equal_to(12))
    assert_that(model.data(idx0, Role.CustomRole), equal_to('/path/to/the_file'))

    # check that the file if also available even if '12' is present in 'st2'
    # but without a path.
    text2 = \
"""
func0 = LIRE_FONCTION(NOM_PARA='INST', UNITE=12)
"""
    comm2study(text2, st2)
    model = UnitModel(st2)
    assert_that(model.rowCount(), equal_to(1))
    idx0 = model.index(0, 0)
    assert_that(model.data(idx0), equal_to('the_file'))
    assert_that(model.data(idx0, Role.IdRole), equal_to(12))
    assert_that(model.data(idx0, Role.CustomRole), equal_to('/path/to/the_file'))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
