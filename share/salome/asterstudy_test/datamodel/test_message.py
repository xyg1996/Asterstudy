# -*- coding: utf-8 -*-

# Copyright 2016 - 2017 EDF R&D
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


import os
import os.path as osp
import unittest

from asterstudy.common import to_unicode
from asterstudy.datamodel import History
from asterstudy.datamodel.result import (Message, MsgLevel, MsgType,
                                         extract_messages)
from asterstudy.datamodel.result.message import search_msg
from hamcrest import *


def test_message():
    msg = Message(MsgLevel.Info, "Text of the message",
                  MsgType.Stage, "0:1", 1, 0)

    assert_that(msg.level, equal_to(MsgLevel.Info))
    assert_that(MsgLevel.to_str(msg.level), equal_to('INFO'))

    assert_that(msg.source, equal_to(MsgType.Stage))
    assert_that(msg.case_id, equal_to(-1))
    assert_that(msg.stage_num, equal_to(1))
    assert_that(msg.command_num, equal_to(0))
    assert_that(msg.line, equal_to(1))

    assert_that(msg.text, contains_string("Text of the message"))

    msg.add_topo('grel', ('GRMA1', 'GRMA2'))
    assert_that(msg.get_topo('grel'), has_length(2))
    msg.add_topo('grel', 'GRMA3')
    assert_that(msg.get_topo('grel'), has_length(3))
    assert_that(msg.get_topo('grel'),
                contains_inanyorder('GRMA1', 'GRMA2', 'GRMA3'))
    assert_that(msg.get_topo('grno'), has_length(0))
    assert_that(msg.get_topo('el'), has_length(0))
    assert_that(msg.get_topo('no'), has_length(0))

    assert_that(msg.get_unknown(), has_length(0))
    msg.add_unknown('DX')
    assert_that(msg.get_unknown(), has_length(1))
    msg.add_unknown(['DY', 'DZ'])
    assert_that(msg.get_unknown(), has_length(3))
    assert_that(msg.get_unknown(),
                contains_inanyorder('DX', 'DY', 'DZ'))
    assert_that(msg.checksum, instance_of(str))

    assert_that(msg.debug_repr(),
                equal_to("Stage INFO - case:-1 stage:1 cmd:0 line:1"))

    # incomplete command id for background compatibility
    msg = Message(MsgLevel.Info, "Text of the message",
                  MsgType.Stage, 123, 1, 0)
    assert_that(msg.stage_num, equal_to(-1))
    assert_that(msg.command_num, equal_to(123))


def test_result():
    history = History()
    stage = history.current_case.create_stage(":memory:")
    stage.add_command('LIRE_MAILLAGE', 'mesh')

    result = stage.result
    msglist = extract_messages("random")
    result.add_messages(msglist)
    assert_that(result.messages, has_length(greater_than_or_equal_to(3)))

    size = len(msglist)
    assert_that(result.messages, has_length(size))
    result.add_messages(msglist[0])
    # existing message, size should not changed
    assert_that(result.messages, has_length(size))

    # check case and stage id
    msg = msglist[0]
    assert_that(msg.case_id, equal_to(history.current_case.uid))
    assert_that(msg.stage_num, equal_to(1))

    # test source representation
    winmsg = []
    last = {}
    case = history.current_case
    for res in case.results():
        for msg in res.messages:
            last[msg.source] = msg
            # random messages are not consistent with the unique stage
            msg._cmd_num = 0
            infos = [MsgLevel.to_str(msg.level),
                     res.stage.name,
                     msg.source_repr(history),
                     msg.text]
            winmsg.append("{0:<8} | {1:<15} | {2:<40} | {3}".format(*infos))
    example = "\n".join(winmsg)
    assert_that(example, contains_string("Sample text"))
    # print "\nExample of window message representation:\n", example

    # to ensure full coverage, because of random messages
    msg = last[MsgType.Runner]
    msg._stg_num = 0
    assert_that(msg.source_repr(history), contains_string("initialization"))
    msg._stg_num = 4
    assert_that(msg.source_repr(history), contains_string("after run"))

    msg = last[MsgType.Command]
    assert_that(msg.source_repr(history), contains_string("LIRE_MAILLAGE"))
    assert_that(msg.source_repr(history), contains_string(" in "))
    # bad stage number
    msg._stg_num = 9
    assert_that(msg.source_repr(history), is_not(contains_string(" in ")))

def test_case():
    history = History()
    cc = history.current_case

    #--------------------------------------------------------------------------
    # create two stages
    s1 = cc.create_stage('s1')
    s2 = cc.create_stage('s2')

    #--------------------------------------------------------------------------
    # create run case, exec both stages 's1' and 's2' but keep results only for for stage 's2'
    rc1 = history.create_run_case(name='rc1', reusable_stages=[1])
    assert_that(cc['s1'].is_intermediate())

    #--------------------------------------------------------------------------
    # test that there are no messages
    messages = rc1.messages()
    assert_that(messages, has_length(0))

    #--------------------------------------------------------------------------
    # run case
    rc1.run(add_messages=True)

    #--------------------------------------------------------------------------
    # test messages
    messages = rc1.messages()
    assert_that(messages, has_length(greater_than(0)))


def _debug_msglist(msglist):
    class Fake:
        def get_node(self, x):
            return 0

    fake = Fake()
    for i, m in enumerate(msglist):
        print("=" * 50, i, MsgLevel.to_str(m.level), m.source_repr(fake),  "=" * 50)
        print(m.text)

def _test_ssnv128a(filename, msgtype, info0_id, info0_line):
    with open(filename, "rb") as fobj:
        text = to_unicode(fobj.read())

    msglist = extract_messages(text)
    # _debug_msglist(msglist)
    assert_that(msglist, has_length(28))

    msgrun = [msg for msg in msglist if msg.source is MsgType.Runner]
    assert_that(msgrun, has_length(11))
    info = [msg for msg in msgrun if msg.level is MsgLevel.Info]
    warn = [msg for msg in msgrun if msg.level is MsgLevel.Warn]
    error = [msg for msg in msgrun if msg.level is MsgLevel.Error]
    assert_that(info, has_length(10))
    assert_that(warn, has_length(1))
    assert_that(error, has_length(0))

    msgexec = [msg for msg in msglist if msg.source is msgtype]
    assert_that(msgexec, has_length(17))
    info = [msg for msg in msgexec if msg.level is MsgLevel.Info]
    warn = [msg for msg in msgexec if msg.level is MsgLevel.Warn]
    error = [msg for msg in msgexec if msg.level is MsgLevel.Error]
    assert_that(info, has_length(2))
    assert_that(warn, has_length(15))
    assert_that(error, has_length(0))

    info0 = info[0]
    assert_that(info0.level, equal_to(MsgLevel.Info))
    assert_that(info0.stage_num, equal_to(-1)) # set_stage not called
    assert_that(info0.source, equal_to(msgtype))
    assert_that(info0.command_num, equal_to(info0_id))
    assert_that(info0.line, equal_to(info0_line))

    checksum = set([msg.checksum for msg in msglist])
    assert_that(checksum, has_length(28))

def test_messages_text():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'ssnv128a.output')
    _test_ssnv128a(output, MsgType.Stage, 4, 411)


def test_messages_graph():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'ssnv128a_graph.output')
    _test_ssnv128a(output, MsgType.Command, 65, 442)


def test_messages_xx():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'ssnv128a_xx.output')
    with open(output, "rb") as fobj:
        text = to_unicode(fobj.read().decode('utf-8'))

    msglist = extract_messages(text)
    # _debug_msglist(msglist)
    assert_that(msglist, has_length(18))

    error = [msg for msg in msglist if msg.level is MsgLevel.Error]
    # _debug_msglist(error)
    assert_that(error, has_length(2))

    assert_that(error[0].text, starts_with("Traceback"))
    assert_that(error[1].text, starts_with("NotImplementedError"))


def test_messages_trunc():
    text = "?\n" * 50
    dmsg = search_msg(text, 49)
    assert_that(dmsg, has_length(1))
    assert_that(dmsg, has_key('run0_txt1'))
    line, text = dmsg['run0_txt1'][0]
    assert_that(line, equal_to(1))
    assert_that(text, contains_string('Only the messages'))


def test_messages_failure():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'test_failure_message2.output')
    with open(output, "rb") as fobj:
        text = to_unicode(fobj.read().decode('utf-8'))

    msglist = extract_messages(text)
    # _debug_msglist(msglist)
    assert_that(msglist, has_length(5))

    info = [msg for msg in msglist if msg.level is MsgLevel.Info]
    assert_that(len(info), greater_than_or_equal_to(2))
    assert_that(info[0].text, contains_string("<INFO>"))
    # development version of code_aster may print SUPERVIS_41
    assert_that(info[-1].text, contains_string("EXECUTION_CODE_ASTER_"))

    warning = [msg for msg in msglist if msg.level is MsgLevel.Warn]
    assert_that(warning, has_length(1))
    assert_that(warning[0].text, contains_string("SUPERVIS_1"))

    error = [msg for msg in msglist if msg.level is MsgLevel.Error]
    assert_that(error, has_length(1))
    assert_that(error[0].text, contains_string("JDC.py"))


def test_multi_stages():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'multiple.output')
    with open(output, "rb") as fobj:
        text = to_unicode(fobj.read())

    msglist = extract_messages(text)
    # _debug_msglist(msglist)
    assert_that(msglist, has_length(16))
    warning = [msg for msg in msglist if msg.level is MsgLevel.Warn]
    assert_that(warning, has_length(4))

    # cmd0:1, cmd0:2, cmd1:2
    ids = ((0, 1), (0, 2), (1, 2))
    for ncmd, nstg in ids:
        msg = warning.pop(0)
        assert_that(msg.command_num, equal_to(ncmd))
        assert_that(msg.stage_num, equal_to(nstg))


def test_27709():
    history = History()
    case = history.current_case
    st1 = case.create_stage("st1")
    st1.add_command('DEBUT')

    st2 = case.create_stage("st2")
    st2.add_command("LIRE_MAILLAGE", "mesh")

    # similar to Dashboard._showLogFile
    def _shown_stage(message):
        case = history.get_node(message.case_id)
        if case is not None:
            num = message.stage_num
            while num <= case.nb_stages:
                stage = case.get_stage_by_num(num)
                if not stage.is_intermediate():
                    break
                num += 1
            return stage

    # similar to Dashboard._gotoCommand
    def _goto_command(message):
        case = history.get_node(message.case_id)
        if case is not None:
            case.restore_stages_mode()
            stage = case.get_stage_by_num(message.stage_num)
            if stage is not None:
                cmd = stage.get_cmd_by_index(message.command_num)
                return cmd

    # run separately
    run1 = history.create_run_case(exec_stages=[0, 1], reusable_stages=[0, 1])
    assert_that(run1['st1'].is_intermediate(), equal_to(False))
    assert_that(run1['st2'].is_intermediate(), equal_to(False))

    run1.run()
    msg1 = Message(MsgLevel.Warn, "Alarm because of PAR_LOT='NON'",
                   MsgType.Command, "0:1", 22, 1)
    msg2 = Message(MsgLevel.Info, "Number of elements found",
                   MsgType.Command, "0:2", 144, 1)
    run1['st1'].result.add_messages(msg1)
    run1['st2'].result.add_messages(msg2)

    assert_that(msg1.case_id, equal_to(run1.uid))
    assert_that(msg2.case_id, equal_to(run1.uid))
    assert_that(msg1.stage_num, equal_to(1))
    assert_that(msg2.stage_num, equal_to(2))
    assert_that(msg1.command_num, equal_to(0))
    assert_that(msg2.command_num, equal_to(0))

    # dashboard tasks
    assert_that(_shown_stage(msg1), same_instance(run1['st1']))
    assert_that(_shown_stage(msg2), same_instance(run1['st2']))
    assert_that(_goto_command(msg1), same_instance(run1['st1'][0]))
    assert_that(_goto_command(msg2), same_instance(run1['st2'][0]))

    # run together
    run2 = history.create_run_case(exec_stages=[0, 1])
    assert_that(run2['st1'].is_intermediate(), equal_to(True))
    assert_that(run2['st2'].is_intermediate(), equal_to(False))

    run2.run()
    msg1 = Message(MsgLevel.Warn, "Alarm because of PAR_LOT='NON'",
                   MsgType.Command, "0:1", 22, 1)
    msg2 = Message(MsgLevel.Info, "Number of elements found",
                   MsgType.Command, "0:2", 144, 1)
    run2['st2'].result.add_messages([msg1, msg2])

    assert_that(msg1.case_id, equal_to(run2.uid))
    assert_that(msg2.case_id, equal_to(run2.uid))
    assert_that(msg1.stage_num, equal_to(1))
    assert_that(msg2.stage_num, equal_to(2))
    assert_that(msg1.command_num, equal_to(0))
    assert_that(msg2.command_num, equal_to(0))

    # dashboard tasks
    assert_that(_shown_stage(msg1), same_instance(run2['st2']))
    assert_that(_shown_stage(msg2), same_instance(run2['st2']))
    assert_that(_goto_command(msg1), same_instance(run2['st1'][0]))
    assert_that(_goto_command(msg2), same_instance(run2['st2'][0]))


def _test_mpi_output(output):
    with open(output, "rb") as fobj:
        text = to_unicode(fobj.read())

    msglist = extract_messages(text)
    # _debug_msglist(msglist)
    assert_that(len(msglist), is_in([24, 28]))


def test_output_openmpi():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'zzzz307b_openmpi.output')
    _test_mpi_output(output)

def test_output_impi():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'zzzz307b_impi.output')
    _test_mpi_output(output)


def test_old_identifiers():
    output = osp.join(os.getenv('ASTERSTUDYDIR'),
                      'data', 'export', 'output.log.old_version')

    with open(output, "rb") as fobj:
        text = to_unicode(fobj.read())

    msglist = extract_messages(text)
    # _debug_msglist(msglist)
    assert_that(msglist, has_length(26))
    # stage number is not present
    for i, m in enumerate(msglist):
        assert_that(m.stage_num, equal_to(-1))

    fromcmd = [msg for msg in msglist if msg.source is MsgType.Command]
    assert_that(fromcmd, has_length(15))
    cmd_id = set([m.command_num for m in fromcmd])
    # emitted by 5 different commands
    assert_that(cmd_id, has_length(5))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
