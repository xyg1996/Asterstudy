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

from testutils import attr, tempdir

from asterstudy.common import enable_autocopy
from asterstudy.datamodel import History

@attr('fixit')
@tempdir
def test_msg_dup(tmpdir):
    """Test for duplication of messages"""

    def _check_msg(_case):
        _messages = _case.messages()
        assert_that(_messages, is_not(empty()))
        msg_0 = _case.messages()[0]
        _stage = _case.model.get_node(msg_0.stage_num)
        assert_that(_stage.folder, equal_to(osp.join(tmpdir, _case.name, 'Result-{}'.format(_stage.name))))

    # create study
    h = History()
    h.folder = tmpdir
    s1 = h.current_case.create_stage('s1')

    # save study
    History.save(h, osp.join(tmpdir, 'study.ajs'))

    # create run case and execute it (to produce some messages)
    rc1 = h.create_run_case(name='rc1')
    rc1.run(add_messages=True)

    # check messages in run case
    _check_msg(rc1)

    # modify current case (to force duplication of stages)
    with enable_autocopy(h.current_case, True):
        h.current_case[0].add_command('LIRE_MAILLAGE', 'mesh')

    # re-check messages in run case
    _check_msg(rc1)


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
