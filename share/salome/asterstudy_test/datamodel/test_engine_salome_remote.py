# -*- coding: utf-8 -*-

# Copyright 2017 EDF R&D
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

"""Automatic tests for Salome services on a remote server (Aster 5).

This tests must be run in the SALOME environment, using "salome shell" and
with a SALOME application running.

Example::

    salome start -t
    <running unittests>
    salome shell killSalome.py
"""


import unittest

from hamcrest import *
from testutils import attr

from asterstudy.datamodel.history import History
from asterstudy.datamodel.engine import Engine, serverinfos_factory
from asterstudy.datamodel.engine.salome_runner import has_salome

from engine_testcases import (USER, remote_server,
                              xtest_infos,
                              xtest_run_with_data,
                              xtest_success,
                              xtest_remote,
                              xtest_remote_out_file,
                              xtest_remote_in_file)
from asterstudy.datamodel.engine.engine_utils import (remote_exec,
                                                      remote_file_copy)

_multiprocess_can_split_ = False
ENGINE = Engine.Salome

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_salome(), "salome is required")
def test_infos():
    xtest_infos(ENGINE, remote_server(ENGINE))

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_salome(), "salome is required")
def test_run_with_data():
    xtest_run_with_data(ENGINE, remote_server(ENGINE))

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_salome(), "salome is required")
def test_success():
    xtest_success(ENGINE, remote_server(ENGINE))

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_salome(), "salome is required")
def test_remote():
    xtest_remote(ENGINE, remote_server(ENGINE))

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_salome(), "salome is required")
def test_remote_out_file():
    xtest_remote_out_file(ENGINE, remote_server(ENGINE))

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_salome(), "salome is required")
def test_remote_in_file():
    xtest_remote_in_file(ENGINE, remote_server(ENGINE))

def _set_remote_files():
    """Initialize two remote paths with and without valid file."""
    # Get server infos
    servername = remote_server(ENGINE)
    infos = serverinfos_factory(ENGINE)
    user = infos.server_username(servername)
    host = infos.server_hostname(servername)

    # Create some distant file
    tmp_file_path = "/tmp/{0}_tmp-asterstudy-existing-file".format(USER)
    command = "if [ ! -f {0} ]; then touch {0}; fi;".format(tmp_file_path)
    remote_exec(user, host, command)

    # Clean if necessary, before to copy
    tmp_copy_path = "/tmp/{0}_tmp-asterstudy-not-a-file".format(USER)
    command = "if [ -f {0} ]; then rm {0}; fi;".format(tmp_copy_path)
    remote_exec(user, host, command)

    # Check file does not exist yet
    exists = "if [ -f {} ]; then echo True; else echo False; fi;".format(tmp_file_path)
    assert_that(remote_exec(user, host, exists).rstrip(), equal_to("True"))
    exists = "if [ -f {} ]; then echo True; else echo False; fi;".format(tmp_copy_path)
    assert_that(remote_exec(user, host, exists).rstrip(), equal_to("False"))
    return infos, user, host, tmp_file_path, tmp_copy_path

@unittest.skipIf(not remote_server(ENGINE), "no server available")
@unittest.skipIf(not has_salome(), "salome is required")
def test_remote_file_copy():
    """Test copy from remote server to remote server"""
    _ , user, host, tmp_file_path, tmp_copy_path = _set_remote_files()

    # Copy file using `remote_file_copy
    remote_file_copy(user, host, tmp_file_path, tmp_copy_path, False)

    # Check copy now exists on remote server
    exists = "if [ -f {} ]; then echo True; else echo False; fi;".format(tmp_copy_path)
    assert_that(remote_exec(user, host, exists).rstrip(), equal_to("True"))

    # Clean
    command = "if [ -f {0} ]; then rm {0}; fi;".format(tmp_copy_path)
    remote_exec(user, host, command)
    command = "if [ -f {0} ]; then rm {0}; fi;".format(tmp_file_path)
    remote_exec(user, host, command)

def _setup_test():
    history = History()
    case = history.current_case
    stage = case.create_stage(':memory:')
    command = stage('LIRE_MAILLAGE')
    return command, stage


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
