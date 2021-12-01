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

"""Automatic tests for embedded files."""


import os
import os.path as osp
import unittest

from asterstudy.common import ExistingSwapError
from asterstudy.common.utilities import enable_autocopy
from asterstudy.datamodel.comm2study import comm2study
from asterstudy.datamodel.general import FileAttr
from asterstudy.datamodel.history import History
from asterstudy.datamodel.undo_redo import UndoRedo
from hamcrest import *
from testutils import tempdir
# initialize a fake Behavior for testing
import testutils.gui_utils


@tempdir
def test_history_tmpdir(tmpdir):
    """Test that the tmp directory is properly created, and stays during undo/redo"""

    history = History()
    history.folder = tmpdir

    undo_redo = UndoRedo(history)
    assert_that(undo_redo.model, same_instance(history))

    assert_that(osp.isdir(tmpdir), equal_to(True))
    undo_redo.commit("initialize")

    case = history.create_case('case')
    st = case.create_stage('st')

    undo_redo.commit("commit-changes")
    history2 = undo_redo.model
    undo_redo.revert()
    history = undo_redo.model
    assert_that(history2, is_not(same_instance(history)))

    tmpdir2 = history2.tmpdir
    tmpdir = history.tmpdir
    assert_that(tmpdir2, equal_to(tmpdir))
    assert_that(osp.isdir(tmpdir2))


@tempdir
def test_handle_embfiles(tmpdir):
    """
    Test the handling of embedded files at run time for one stage.
    """
    history = History()
    history.folder = tmpdir
    cc = history.current_case
    cc.name = 'cc'

    st1 = cc.create_stage('st1')
    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20)

mesh2 = LIRE_MAILLAGE(UNITE=30)

mesh3 = LIRE_MAILLAGE(UNITE=40)
"""

    # non existing file
    comm2study(text1, st1)
    st1['mesh']['UNITE'].value = {20: '/my/fake/path/dummy.txt'}
    st1.handle2info[20].embedded = True

    # existing file
    tmpfile = osp.join(tmpdir, 'testfile')
    with open(tmpfile, 'w') as fobj:
        fobj.write('existing file')
    st1.handle2info[30].filename = tmpfile
    st1.handle2info[30].embedded = True

    # file that will not be embedded
    external_path = '/my/fake/path/dummy_external.txt'
    st1['mesh3'].init({'UNITE': {40: external_path}})
    st1.handle2info[40].embedded = False

    cc._make_run_dir_helper(st1)

    embfolder = osp.join(osp.join(tmpdir, 'cc'), 'Embedded')

    path = osp.join(embfolder, 'dummy.txt')
    assert_that(st1.handle2info[20].filename, equal_to(path))
    assert_that(osp.isfile(path), equal_to(False))

    path = osp.join(embfolder, 'testfile')
    assert_that(st1.handle2info[30].filename, equal_to(path))
    assert_that(osp.isfile(path), equal_to(True))

    # external file should not have changed
    assert_that(st1.handle2info[40].filename, equal_to(external_path))


def test_parent_info():
    """Test the function that gives similar Info object in parent stages."""

    history = History()
    cc = history.current_case
    cc.name = 'cc'

    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')
    st3 = cc.create_stage('st3')

    # `handle2info` is a default dict, so new values may be created on the fly
    commonall = '/some/path/common/to/all/stages.txt'
    common13 = '/some/path/common/to/st1/and/st3.txt'
    unique3 = '/some/unique/path/to/st3.txt'

    st1.handle2info[10].filename = commonall
    st1.handle2info[11].filename = common13
    st1.handle2info[12].filename = '/some/unique/path/to/st1.txt'

    st2.handle2info[10].filename = commonall
    st2.handle2info[11].filename = '/some/unique/path/to/st2.txt'
    st2.handle2info[12].filename = '/some/other/unique/path/to/st2.txt'

    st3.handle2info[10].filename = commonall
    st3.handle2info[11].filename = common13
    st3.handle2info[12].filename = unique3

    assert_that(st3.parent_info(st3.handle2info[10]), same_instance(st2.handle2info[10]))
    assert_that(st2.parent_info(st2.handle2info[10]), same_instance(st1.handle2info[10]))
    assert_that(st1.parent_info(st1.handle2info[10]), equal_to(None))

    assert_that(st3.parent_info(st3.handle2info[12]), equal_to(None))
    assert_that(st3.parent_info(st3.handle2info[11]), same_instance(st1.handle2info[11]))

    # embed `unique3`, since it has the same basename, common13 will be returned
    st3.handle2info[12].embedded = True
    assert_that(st3.parent_info(st3.handle2info[12]), equal_to(None))

    st1.handle2info[11].embedded = True
    assert_that(st3.parent_info(st3.handle2info[12]), equal_to(st1.handle2info[11]))


@tempdir
def test_move_embfiles_2_stages(tmpdir):
    """Test handling embedded files at run time with several stages."""

    history = History()
    history.folder = tmpdir

    cc = history.current_case
    cc.name = 'cc'

    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')

    # the first stage contains a file, whatever in or out
    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')
"""
    comm2study(text1, st1)

    assert_that(os.listdir(history.tmpdir), equal_to([]))
    bname = 'dummy_common_file.txt'
    tmpfile = osp.join(history.tmpdir, bname)
    open(tmpfile, 'a').close()
    assert_that(osp.isfile(tmpfile))

    st1.handle2info[20].filename = tmpfile
    st1.handle2info[20].embedded = True

    # taken as an in file for the second stage
    text2 = \
"""
mesh2 = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')
"""
    comm2study(text2, st2)
    st2.handle2info[20].filename = tmpfile
    st2.handle2info[20].embedded = True
    assert_that(st2.handle2info[20].attr, equal_to(FileAttr.In))

    # the following simulates what happens when running st1
    rc1 = history.create_run_case(exec_stages=0, name='rc1')
    rc1.make_run_dir()
    rc1.run()

    # check that the file has been copied
    rc1dir = osp.join(history.folder, 'rc1/Embedded')
    rc1file = osp.join(rc1dir, bname)
    assert_that(osp.isdir(rc1dir), equal_to(True))
    assert_that(osp.isfile(rc1file), equal_to(True))
    assert_that(rc1[0].handle2info[20].filename, equal_to(rc1file))

    # simulate running st2
    rc2 = history.create_run_case(exec_stages=1, name='rc2')
    rc2.make_run_dir()
    rc2.run()

    # check that the original file is referenced
    assert_that(rc2[1].handle2info[20].filename, equal_to(rc1file))
    assert_that(osp.isfile(rc1file), equal_to(True))

    rc2dir = osp.join(history.folder, 'rc2/Embedded')
    rc2file = osp.join(rc2dir, bname)
    assert_that(osp.isdir(rc2dir), equal_to(True))
    assert_that(osp.isfile(rc2file), equal_to(False))

    # taken as an out file for the second stage
    cc[1].clear()
    cc[1].handle2info.clear()
    text2 = \
"""
IMPR_RESU(UNITE=20,
          FORMAT='MED',
          RESU=_F(MAILLAGE=mesh))
"""
    comm2study(text2, cc[1])
    cc[1].handle2info[20].filename = tmpfile
    cc[1].handle2info[20].embedded = True
    assert_that(cc[1].handle2info[20].attr, equal_to(FileAttr.Out))

    # simulate running st2 again
    rc3 = history.create_run_case(exec_stages=1, name='rc3')
    rc3.make_run_dir()
    rc3.run()

    # check that nothing is copied, the reference is changed
    rc3dir = osp.join(history.folder, 'rc3/Embedded')
    rc3file = osp.join(rc3dir, bname)

    assert_that(rc3[1].handle2info[20].filename, equal_to(rc3file))
    assert_that(osp.isdir(rc3dir), equal_to(True))
    assert_that(osp.isfile(rc3file), equal_to(False))

    # taken as an inout file for the second stage
    cc[1].clear()
    cc[1]._handle2info.clear()
    text2 = \
"""
mesh2 = LIRE_MAILLAGE(UNITE=20, FORMAT='MED')

IMPR_RESU(UNITE=20,
          FORMAT='MED',
          RESU=_F(MAILLAGE=mesh2))
"""
    comm2study(text2, cc[1])
    cc[1].handle2info[20].filename = tmpfile
    cc[1].handle2info[20].embedded = True
    assert_that(cc[1].handle2info[20].attr, equal_to(FileAttr.InOut))

    # simulate running st2
    rc4 = history.create_run_case(exec_stages=1, name='rc4')
    rc4.make_run_dir()
    rc4.run()

    # check that the file is copied, the reference is changed
    rc4dir = osp.join(history.folder, 'rc4/Embedded')
    rc4file = osp.join(rc4dir, bname)

    assert_that(rc4[1].handle2info[20].filename, equal_to(rc4file))
    assert_that(osp.isdir(rc3dir), equal_to(True))
    assert_that(osp.isfile(rc4file), equal_to(True))

    assert_that(osp.isfile(rc1file), equal_to(True))
    assert_that(osp.isfile(tmpfile), equal_to(True))


@tempdir
def test_copy_as_current(tmpdir):
    """Test the copy as current operation with embedded files."""
    history = History()
    history.folder = tmpdir

    cc = history.current_case
    cc.name = 'cc'

    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')

    text1 = \
"""
mesh = LIRE_MAILLAGE(UNITE=30, FORMAT='MED')
"""
    text2 = \
"""
mesh2 = LIRE_MAILLAGE(UNITE=31, FORMAT='MED')

IMPR_RESU(UNITE=32,
          FORMAT='MED',
          RESU=_F(MAILLAGE=mesh2))
"""
    comm2study(text1, st1)

    fileA = osp.join(history.tmpdir, 'fileA.txt')
    open(fileA, 'a').close()
    assert_that(osp.isfile(fileA), equal_to(True))
    st1.handle2info[30].filename = fileA
    st1.handle2info[30].embedded = True

    comm2study(text2, st2)

    fileB = osp.join(history.tmpdir, 'fileB.txt')
    open(fileB, 'a').close()
    assert_that(osp.isfile(fileB), equal_to(True))
    st2.handle2info[31].filename = fileB
    st2.handle2info[31].embedded = True

    fileC = osp.join(history.tmpdir, 'fileC.txt')
    assert_that(osp.isfile(fileC), equal_to(False))
    st2.handle2info[32].filename = fileC
    st2.handle2info[32].embedded = True

    # simulate a run, then another
    rc1 = history.create_run_case(exec_stages=[0, 1], name='rc1')
    rc1.make_run_dir()
    rc1.run()

    rc2 = history.create_run_case(exec_stages=1, name='rc2')
    rc2.make_run_dir()
    rc2.run()

    pathA = osp.join(history.folder, rc1.name, 'Embedded', 'fileA.txt')
    assert_that(cc[0].handle2info[30].filename, equal_to(pathA))
    assert_that(osp.isfile(pathA), equal_to(True))

    pathB = osp.join(history.folder, rc2.name, 'Embedded', 'fileB.txt')
    assert_that(cc[1].handle2info[31].filename, equal_to(pathB))
    assert_that(osp.isfile(pathB), equal_to(True))

    pathC = osp.join(history.folder, rc2.name, 'Embedded', 'fileC.txt')
    assert_that(cc[1].handle2info[32].filename, equal_to(pathC))
    assert_that(osp.isfile(pathC), equal_to(False))

    # copy as current, check tmpdir is empty
    cc.copy_from(rc1)
    assert_that(os.listdir(history.tmpdir), equal_to([]))

    pathA = osp.join(history.folder, rc1.name, 'Embedded', 'fileA.txt')
    assert_that(cc[0].handle2info[30].filename, equal_to(pathA))
    assert_that(osp.isfile(pathA), equal_to(True))

    pathB = osp.join(history.folder, rc1.name, 'Embedded', 'fileB.txt')
    assert_that(cc[1].handle2info[31].filename, equal_to(pathB))
    assert_that(osp.isfile(pathB), equal_to(True))

    pathC = osp.join(history.folder, rc1.name, 'Embedded', 'fileC.txt')
    assert_that(cc[1].handle2info[32].filename, equal_to(pathC))
    assert_that(osp.isfile(pathC), equal_to(False))

    # perform some meaningless modification to the second stage
    with enable_autocopy(cc):
        cc[1]['mesh2']['FORMAT'] = 'ASTER'

    # now the path has not been changed for the files in the first stage
    pathA = osp.join(history.folder, rc1.name, 'Embedded', 'fileA.txt')
    assert_that(cc[0].handle2info[30].filename, equal_to(pathA))
    assert_that(osp.isfile(pathA), equal_to(True))

    # it has changed for the files in the second stage
    pathB = osp.join(history.tmpdir, 'fileB.txt')
    assert_that(cc[1].handle2info[31].filename, equal_to(pathB))
    assert_that(osp.isfile(pathB), equal_to(True))

    pathC = osp.join(history.tmpdir, 'fileC.txt')
    assert_that(cc[1].handle2info[32].filename, equal_to(pathC))
    assert_that(osp.isfile(pathC), equal_to(False))


@tempdir
def test_save_load_embedded_files(tmpdir):
    """Test plain save and load operations on embedded files."""

    # When loading a file, the following operations are called:
    # 1. the data model (*History* object) is recreated from the .ajs file
    #     o done in  `History.load`, called in Study.load
    # 2. the `folder` attribute of *History* is set,
    #   and study root folder is created if non-existing
    #     o done in `History.folder` setter method, called in Study.load
    # 3. the consistency between the study directory and data model
    #   thus built is checked, and adjusted if necessary
    #     o that would be `History.check_dir`, called in Study.load
    # 4. load operations specific to embedded files are called
    #     o that would be history.load_embedded_files

    # When saving a file:
    # a. the `folder` attribute is not set on first save,
    #   (remember that saving at least once is necessary before embedding,
    #    this is checked in the method `embeddedChanged` of *UnitPanel*)
    #   and thus root directory not created
    # b. it is set at embedding time if necessary
    #     o see `gui.datafiles.unitpanel.py`, also `UnitPanel.embeddedChanged`
    # c. function `ext2emb` copies the external file to its embedded location
    # d. then, at second save, the files is moved from its embedded location
    #   to a temporary directory, from where it will be put within the HDF

    # The present test is meant to test mostly operations 4. and d.
    # It does not test the whole process
    # For this, see `test_full_save_load_embedded_files`

    import tempfile
    history = History()
    history.folder = tmpdir

    cc = history.current_case
    cc.name = 'cc'
    cc.create_stage('st1')

    # the following produces a file at an embedded location
    myfile = osp.join(history.tmpdir, 'dummy.txt')
    open(myfile, 'a').close()

    # the following simulates what happens to this file at save time
    # in reality, files in `tmpsavedir` will be put in the HDF in Salome
    ajsfile = osp.join(tmpdir, 'test.ajs')
    History.save(history, ajsfile)

    tmpsavedir = osp.join(tmpdir, 'tmpsavedir')
    os.makedirs(tmpsavedir)
    bnames = history.save_embedded_files(tmpsavedir)

    assert_that(osp.isfile(osp.join(tmpsavedir, 'dummy.txt')), equal_to(True))
    assert_that(bnames, equal_to(['dummy.txt']))

    # the following simulates some unsaved change to study files
    # followed by a unexpected Salome interruption
    myfile2 = osp.join(history.tmpdir, 'dummy2.txt')
    open(myfile2, 'a').close()

    # the following tests what happens at load time
    history2 = History.load(ajsfile)
    history2.folder = tmpdir

    history2.load_embedded_files(tmpsavedir, ['dummy.txt'], check=False)

    assert_that(osp.isfile(myfile), equal_to(True))
    assert_that(osp.isfile(myfile2), equal_to(False))

    # with check option, an error is raised
    # because the embedded directory is not empty
    assert_that(calling(history2.load_embedded_files).with_args(tmpsavedir, ['dummy.txt'], True), raises(ExistingSwapError))

    # check the cleaning of the directory
    history.clean_embedded_files()
    assert_that(osp.isfile(myfile), equal_to(False))

    # test that calling `load_embedded_files` with an empty dir returns nothing
    empty = tempfile.mkdtemp(prefix="asterstudy-", suffix="dir")
    history2.load_embedded_files(empty, ['dummy.txt'], True)

def mock_b(study, stage, extpath):
    """Simulate step b of saving.

    Arguments:
        study (Study): the study object.
        stage (Stage): the stage containg the file to embed.
        extpath (str): path to the file to embed.

    Returns the path to the embedded file.
    """
    path = study.url()
    if path:
        path = os.path.splitext(path)[0] + '_Files'
        if not os.path.isdir(path):
            os.mkdir(path)
        study.history.folder = path
        # check selected file
        return stage.ext2emb(extpath)
    return None

@tempdir
def test_full_save_load_embedded_files(tmpdir):
    """Test comprehensive save and load operations on embedded files."""

    # When loading a file, the following operations are called:
    # 1. the data model (*History* object) is recreated from the .ajs file
    #     o done in  `History.load`, called in Study.load
    # 2. the `folder` attribute of *History* is set,
    #   and study root folder is created if non-existing
    #     o done in `History.folder` setter method, called in Study.load
    # 3. the consistency between the study directory and data model
    #   thus built is checked, and adjusted if necessary
    #     o that would be `History.check_dir`, called in Study.load
    # 4. load operations specific to embedded files are called
    #     o that would be history.load_embedded_files

    # When saving a file:
    # a. the `folder` attribute is not set on first save,
    #   (remember that saving at least once is necessary before embedding,
    #    this is checked in the method `embeddedChanged` of *UnitPanel*)
    #   and thus root directory not created
    # b. it is set at embedding time if necessary
    #     o see `gui.datafiles.unitpanel.py`, also `UnitPanel.embeddedChanged`
    # c. function `UnitModel.transferFile` copies the external file to its embedded location
    # d. then, at second save, the files is moved from its embedded location
    #   to a temporary directory, from where it will be put within the HDF

    # The present test is meant to test the whole process
    # In a case where there is no issue


    import tempfile
    from asterstudy.gui.study import Study
    study = Study(None)

    # study creation comes along with a *History* object
    history = study.history
    cc = history.current_case

    # create a stage with an external file
    st1 = cc.create_stage('st1')
    extpath = tempfile.mkstemp(prefix="asterstudy-", suffix="-test")[1]
    bname = osp.basename(extpath)
    st1.handle2info[20].filename = extpath
    text1 = """
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT="ASTER")
"""
    comm2study(text1, st1)
    study.commit("initialize")

    # folder is not set at this stage
    assert_that(history.folder, is_(None))

    # simulate step a. of saving
    astfile = tempfile.mkstemp(prefix="asterstudy-", suffix="-test")[1]
    study.saveAs(astfile, renamed=False)

    # folder is automatically set when 'savedAs'
    assert_that(history.folder, equal_to(astfile + "_Files"))

    # test that `save_embedded_files` returns empty list
    # when called with empty study dir
    assert_that(study.history.save_embedded_files(tmpdir), equal_to([]))

    # we cannot call `embbededChanged` directly
    # so we copy some of its code in a mock function
    embpath = mock_b(study, st1, extpath)

    # assert folder set at this stage
    assert_that(history.folder, is_not(none()))
    assert_that(history.tmpdir.startswith(history.folder), equal_to(True))
    assert_that(embpath.startswith(history.folder), equal_to(True))
    assert_that(embpath.startswith(history.tmpdir), equal_to(True))

    # the following simulates what happens at step c
    # (when `UnitEditor.applyChanges` executes)
    from asterstudy.datamodel.file_descriptors import copy_file
    copy_file(extpath, embpath)
    st1.handle2info[20].filename = embpath
    st1.handle2info[20].embedded = True
    study.commit("embedding-file")

    # assert files were correctly moved
    assert_that(osp.isfile(embpath), equal_to(True))
    assert_that(osp.isfile(extpath), equal_to(True))
    assert_that(embpath, is_not(equal_to(extpath)))

    # simulate step d
    study.save()
    tmpsavedir = osp.join(tmpdir, 'tmpsavedir')
    os.makedirs(tmpsavedir)
    bnames = history.save_embedded_files(tmpsavedir)

    # assert file was properly copied at the place it was assigned
    assert_that(osp.isfile(osp.join(tmpsavedir, bname)), equal_to(True))
    assert_that(bnames, equal_to([bname]))
    # backup ajs
    assert_that(osp.isfile(osp.join(history.folder, "data.ajs")),
                equal_to(True))

    # now, let us clean the study directories
    os.remove(embpath)
    os.remove(osp.join(history.folder, "data.ajs"))
    assert_that(osp.isfile(embpath), equal_to(False))
    os.rmdir(history.tmpdir)
    os.rmdir(history.folder)

    # try to load without study directory
    # there should be no errors because there are no runs

    # simulate step 1 to 3
    study2 = Study.load(None, astfile)

    # simulate step 4
    history2 = study2.history
    history2.load_embedded_files(tmpsavedir, [bname], check=False)

    # assert that the data model contains an embedded file
    # and the file exists at its embedded location
    cc2 = history2.current_case
    assert_that(cc2['st1'].handle2info[20].filename, equal_to(embpath))
    assert_that(cc2['st1'].handle2info[20].embedded, equal_to(True))
    assert_that(osp.isfile(embpath), equal_to(True))


@tempdir
def test_save_move_load_embedded_files(tmpdir):
    """Test save and load operations on embedded files, move hdf in between."""

    # does the same save/load as before, but moves the ajs file in between
    # refers to issue27152

    import tempfile
    from asterstudy.gui.study import Study
    study = Study(None)

    # study creation comes along with a *History* object
    history = study.history
    cc = history.current_case

    # create a stage with an external file
    st1 = cc.create_stage('st1')
    extpath = tempfile.mkstemp(prefix="asterstudy-", suffix="-test")[1]
    bname = osp.basename(extpath)
    st1.handle2info[20].filename = extpath
    text1 = """
mesh = LIRE_MAILLAGE(UNITE=20, FORMAT="ASTER")
"""
    comm2study(text1, st1)
    study.commit("initialize")

    # folder is not set at this stage
    assert_that(history.folder, is_(None))

    # simulate step a. of saving
    astfile = tempfile.mkstemp(prefix="asterstudy-", suffix="-test")[1]
    study.saveAs(astfile, renamed=False)

    # folder is automatically set when 'savedAs'
    assert_that(history.folder, equal_to(astfile + "_Files"))

    # backup ajs
    assert_that(osp.isfile(osp.join(history.folder, "data.ajs")),
                equal_to(True))

    # test that `save_embedded_files` returns empty list
    # when called with empty study dir
    assert_that(study.history.save_embedded_files(tmpdir), equal_to([]))

    # we cannot call `embbededChanged` directly
    # so we copy some of its code in a mock function
    embpath = mock_b(study, st1, extpath)

    # assert folder set at this stage
    assert_that(history.folder, is_not(none()))
    assert_that(history.tmpdir.startswith(history.folder), equal_to(True))
    assert_that(embpath.startswith(history.folder), equal_to(True))
    assert_that(embpath.startswith(history.tmpdir), equal_to(True))

    # the following simulates what happens at step c
    # (when `UnitEditor.applyChanges` executes)
    from asterstudy.datamodel.file_descriptors import copy_file
    copy_file(extpath, embpath)
    st1.handle2info[20].filename = embpath
    st1.handle2info[20].embedded = True
    study.commit("embedding-file")

    # assert files were correctly moved
    assert_that(osp.isfile(embpath), equal_to(True))
    assert_that(osp.isfile(extpath), equal_to(True))
    assert_that(embpath, is_not(equal_to(extpath)))

    # simulate step d
    study.save()
    tmpsavedir = osp.join(tmpdir, 'tmpsavedir')
    os.makedirs(tmpsavedir)
    bnames = history.save_embedded_files(tmpsavedir)

    # assert file was properly copied at the place it was assigned
    assert_that(osp.isfile(osp.join(tmpsavedir, bname)), equal_to(True))
    assert_that(bnames, equal_to([bname]))

    # now, let us clean the study directories
    os.remove(embpath)
    os.remove(osp.join(history.folder, "data.ajs"))
    assert_that(osp.isfile(embpath), equal_to(False))
    os.rmdir(history.tmpdir)
    os.rmdir(history.folder)

    # now let us move the permanent file (ajs or hdf)
    astdir = tempfile.mkdtemp(prefix="asterstudy-", suffix="-test")
    from asterstudy.common.base_utils import move_file
    dest = osp.join(astdir, osp.basename(astfile))
    move_file(astfile, dest)

    # try to load without study directory
    # there should be no errors because there are no runs

    # simulate step 1 to 3
    study2 = Study.load(None, dest)

    # simulate step 4
    history2 = study2.history
    history2.load_embedded_files(tmpsavedir, [bname], check=False)
    history2.reset_current_embedded()

    # assert that the data model contains an embedded file
    # and the file exists at its embedded location
    cc2 = history2.current_case
    embpath2 = mock_b(study2, cc2['st1'], extpath)
    assert_that(cc2['st1'].handle2info[20].filename, equal_to(embpath2))
    assert_that(cc2['st1'].handle2info[20].embedded, equal_to(True))
    assert_that(osp.isfile(embpath2), equal_to(True))

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
