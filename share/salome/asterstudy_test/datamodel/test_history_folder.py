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

"""Tests for the links between datamodel and the study directory."""


import shutil
import unittest
from hamcrest import *
from testutils import attr, tempdir

from asterstudy.common import StudyDirectoryError, MissingStudyDirError

from asterstudy.datamodel.history import History


@tempdir
def test_load_missing_dir(tmpdir):
    """Test loading with a missing study directory."""
    import os
    import os.path as osp
    import tempfile

    # Create a model with a fake run
    history = History()
    cc = history.current_case
    st = cc.create_stage('Mystage')
    rc = history.create_run_case().run()
    ajs_file = osp.join(tmpdir, 'test.ajs')
    History.save(history, ajs_file)

    # loading an history with no runs in it
    # with an empty directory does not raise an error
    history0 = History()
    history0.folder = osp.join(tmpdir, 'history0_Files')
    history0.check_dir(History.warn)

    # Try to load it with a fictitious directory
    # But to a path where we are the rights to create it
    # Check it errors
    history2 = History.load(ajs_file)
    fake_dir = tempfile.mkdtemp(prefix="asterstudy-", suffix="-test")
    os.rmdir(fake_dir)
    history2.folder = fake_dir
    assert_that(calling(history2.check_dir).with_args(History.warn),
                raises(MissingStudyDirError))
    assert_that(calling(history2.check_dir).with_args(History.full_warn),
                raises(StudyDirectoryError))

    # Try to load it with a directory that actually exists but is empty
    # Check it errors
    actual_dir = osp.join(tmpdir, 'history_folder')
    os.makedirs(actual_dir)
    history2.folder = actual_dir
    assert_that(calling(history2.check_dir).with_args(History.warn),
                raises(StudyDirectoryError))
    assert_that(calling(history2.check_dir).with_args(History.full_warn),
                raises(StudyDirectoryError))

    # Give it a stage subdirectory with the right name
    # Check that it loads successfully
    case_dir = osp.join(actual_dir, rc.name)
    os.mkdir(case_dir)
    stage_dir = osp.join(case_dir, 'Result-' + st.name)
    os.mkdir(stage_dir)

    history2 = History.load(ajs_file)
    history.folder = history2.folder = actual_dir
    history2.check_dir(History.warn)
    history2.check_dir(History.full_warn)
    assert_that(history * history2, none())

    # test `check_dir` with empty `folder` attribute for full coverage
    history.folder = ''
    assert_that(calling(history.check_dir).with_args(History.warn),
                raises(MissingStudyDirError))

    # cleaning
    shutil.rmtree(actual_dir)

    # Test that a forced load gives `cc` only
    #     but the stage has been rescued
    history2 = History.load(ajs_file)
    history2.folder = actual_dir
    history2.check_dir(task=History.clean)

    cc2 = history2.current_case
    assert_that(history2.cases, equal_to([cc2]))
    assert_that(cc2.nb_stages, equal_to(1))


@tempdir
def test_load_incomplete_dir(tmpdir):
    """Test loading a study with an incomplete directory"""
    import os
    import os.path as osp

    # create a datamodel and save it
    history = History()
    cc = history.current_case
    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')

    rc0 = history.create_run_case((0,1), name='rc0').run()
    rc1 = history.create_run_case(1, name='rc1').run()

    ajs_file = osp.join(tmpdir, 'test.ajs')
    History.save(history, ajs_file)

    # create a study directory not consistent with it
    root = osp.join(tmpdir, 'history_folder')
    os.makedirs(root)

    # directories consistent with the datamodel
    rc0_dir = osp.join(root, rc0.name)
    os.mkdir(rc0_dir)

    st1_dir = osp.join(rc0_dir, 'Result-' + st1.name)
    os.mkdir(st1_dir)

    # directories not consistent with the datamodel
    rc2_dir = osp.join(root, 'rc2')
    os.mkdir(rc2_dir)

    st2_dir = osp.join(rc2_dir, 'Result-' + st1.name)
    os.mkdir(st2_dir)

    # test trying to load emits an error
    history2 = History.load(ajs_file)
    history2.folder = root
    assert_that(calling(history2.check_dir).with_args(History.warn),
                raises(StudyDirectoryError))
    assert_that(calling(history2.check_dir).with_args(History.full_warn),
                raises(StudyDirectoryError))

    # force load
    history2.check_dir(History.clean)

    # about run cases, test that only rc0/st1 remains
    #     in data model as well as in directory
    assert_that(len(history2.run_cases), equal_to(1))
    rc0_2 = history2.run_cases[0]
    st1_2 = rc0_2[0]
    assert_that(rc0_2.stages, equal_to([st1_2]))

    # assert that the directory from rc1 was removed
    assert_that(os.listdir(root),
                contains_inanyorder("Embedded", "not_loaded", rc0_2.name))
    assert_that(os.listdir(osp.join(root, rc0_2.name)),
                contains_inanyorder('Result-' + st1_2.name))
    assert_that(os.listdir(osp.join(root, "not_loaded")),
                contains_inanyorder('rc0-st1.comm', 'rc0-st2.comm',
                                    'rc1-st2.comm'))

    # assert `current_case` has been rescued
    cc_2 = history2.current_case
    assert_that(len(cc_2), equal_to(2))
    assert_that(cc_2[0], same_instance(st1_2))


@tempdir
def test_load_incomplete_dm(tmpdir):
    """Test loading a study with an incomplete data model."""
    import os
    import os.path as osp

    # create a datamodel and save it
    history = History()
    cc = history.current_case
    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')

    rc0 = history.create_run_case((0,1), name='rc0').run()
    rc1 = history.create_run_case(1, name='rc1').run()

    ajs_file = osp.join(tmpdir, 'test.ajs')
    History.save(history, ajs_file)

    # create a study directory not consistent with it
    root = osp.join(tmpdir, 'history_folder')
    os.makedirs(root)

    # directories consistent with the datamodel
    rc0_dir = osp.join(root, rc0.name)
    os.mkdir(rc0_dir)

    st1_dir = osp.join(rc0_dir, 'Result-' + st1.name)
    os.mkdir(st1_dir)

    st2_dir = osp.join(rc0_dir, 'Result-' + st2.name)
    os.mkdir(st2_dir)

    rc1_dir = osp.join(root, rc1.name)
    os.mkdir(rc1_dir)

    st3_dir = osp.join(rc1_dir, 'Result-' + st2.name)
    os.mkdir(st3_dir)

    # directories not consistent with the datamodel
    rc2_dir = osp.join(root, 'rc2')
    os.mkdir(rc2_dir)

    st4_dir = osp.join(rc2_dir, 'Result-' + st1.name)
    os.mkdir(st4_dir)

    # test trying to load emits an error
    history2 = History.load(ajs_file)
    history2.folder = root
    assert_that(calling(history2.check_dir).with_args(History.warn),
                raises(StudyDirectoryError))
    assert_that(calling(history2.check_dir).with_args(History.full_warn),
                raises(StudyDirectoryError))


@tempdir
def test_delete_case_dir(tmpdir):
    """
    Test that a case directory is deleted when deleting the case.
    """
    import os
    import os.path as osp

    # create a datamodel
    history = History()
    cc = history.current_case
    st1 = cc.create_stage('st1')
    st2 = cc.create_stage('st2')

    rc0 = history.create_run_case((0,1), name='rc0').run()
    rc1 = history.create_run_case(1, name='rc1').run()
    rc2 = history.create_run_case(1, name='rc2').run()

    # directories consistent with the datamodel
    root = osp.join(tmpdir, 'history_folder')
    os.makedirs(root)
    history.folder = root

    assert_that(history.folder, equal_to(root))
    # check that folder is unchanged
    history.folder = "/workaround/for/bug/27016/_Files"
    assert_that(history.folder, equal_to(root))

    rc0_dir = osp.join(root, rc0.name)
    os.mkdir(rc0_dir)

    st1_dir = osp.join(rc0_dir, 'Result-' + st1.name)
    os.mkdir(st1_dir)

    st2_dir = osp.join(rc0_dir, 'Result-' + st2.name)
    os.mkdir(st2_dir)

    rc1_dir = osp.join(root, rc1.name)
    os.mkdir(rc1_dir)

    st3_dir = osp.join(rc1_dir, 'Result-' + st2.name)
    os.mkdir(st3_dir)

    rc2_dir = osp.join(root, rc2.name)
    os.mkdir(rc2_dir)

    st4_dir = osp.join(rc2_dir, 'Result-' + st2.name)
    os.mkdir(st4_dir)

    # delete rc2, check that the corresponding directory is deleted
    rc2.delete()

    assert_that(osp.isdir(rc2_dir), equal_to(False))
    assert_that(osp.isdir(rc1_dir), equal_to(True))
    assert_that(osp.isdir(rc0_dir), equal_to(True))

    # delete rc0, every directory should be deleted because of dependencies
    rc0.delete()
    assert_that(osp.isdir(rc1_dir), equal_to(False))
    assert_that(osp.isdir(rc0_dir), equal_to(False))

@tempdir
def test_case_basefolder(tmpdir):
    """
    Test that the case folder is stored as an attribute
    """
    import os
    import os.path as osp

    history = History()
    root = osp.join(tmpdir, 'history_folder')
    os.makedirs(root)
    history.folder = root

    cc = history.current_case
    st = cc.create_stage('st')
    rc = history.create_run_case(0, name='rc')

    assert_that(rc.base_folder, equal_to(''))
    assert_that(st.base_folder, equal_to(''))
    rc.name = 'rc_copy'
    st.name = 'st_copy'
    assert_that(rc.base_folder, equal_to(''))
    assert_that(st.base_folder, equal_to(''))

    # `folder` attribute of rc1[0] is accessed,
    # which sets `base_folder` attribute for `rc1`
    stfolder = st.folder
    assert_that(rc.base_folder, equal_to('rc_copy'))
    assert_that(st.base_folder, equal_to('Result-st_copy'))

    rc.name = 'rc-copy2'
    st.name = 'st-copy2'
    stfolder = st.folder
    assert_that(rc.base_folder, equal_to('rc_copy'))
    assert_that(st.base_folder, equal_to('Result-st_copy'))

    # check that `base_folder` attribute is properly retrieved
    # after a save/load operation
    ajs_file = osp.join(tmpdir, 'test.ajs')
    History.save(history, ajs_file)

    history2 = History.load(ajs_file)
    rc2 = history2.run_cases[0]
    st2 = rc2[0]
    assert_that(rc2.base_folder, equal_to('rc_copy'))
    assert_that(st2.base_folder, equal_to('Result-st_copy'))

    # the `folder` attribute of history represents an absolute path
    # it should be lost after save/load operation:
    # one might have moved the file and load it from its new location
    assert_that(history2.folder, equal_to(None))

@tempdir
def test_load_empty_case(tmpdir):
    """Test loading a empty case"""
    import os
    import os.path as osp

    # create a datamodel and save it
    history = History()
    cc = history.current_case
    st1 = cc.create_stage('st1')

    rc0 = history.create_run_case(0, name='rc0').run()
    rc1 = history.create_run_case(0, name='rc1').run()

    # rc0 is now empty
    rc0[0].delete()

    ajs_file = osp.join(tmpdir, 'test.ajs')
    History.save(history, ajs_file)

    # create corresponding directory, empty rc0 folder
    root = osp.join(tmpdir, 'history_folder')
    os.makedirs(root)

    rc1_dir = osp.join(root, rc1.name)
    os.mkdir(rc1_dir)

    st1_dir = osp.join(rc1_dir, 'Result-' + st1.name)
    os.mkdir(st1_dir)

    assert_that(calling(history.check_dir).with_args(History.warn),
                raises(StudyDirectoryError))

    rc0_dir = osp.join(root, 'rc0')
    os.mkdir(rc0_dir)

    history.folder = root
    assert_that(calling(history.check_dir).with_args(History.warn),
                raises(StudyDirectoryError))
    history.check_dir(History.clean)

    # assert empty runcase no longer exists
    assert_that(rc0, is_not(is_in(history.cases)))

    # assert empty corresponding directory no longer exists
    assert_that(osp.isdir(rc0_dir), equal_to(False))

    # recreate empty case directory, check it is detected
    os.mkdir(rc0_dir)

    assert_that(calling(history.check_dir).with_args(History.warn),
                raises(StudyDirectoryError))
    history.check_dir(History.clean)
    assert_that(osp.isdir(rc0_dir), equal_to(False))


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
