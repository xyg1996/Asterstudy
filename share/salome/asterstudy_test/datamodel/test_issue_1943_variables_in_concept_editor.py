# -*- coding: utf-8 -*-
import unittest

from hamcrest import assert_that, equal_to, has_length, is_not
from testutils import attr

from asterstudy.datamodel import History, comm2study, Validity


def test_variables_in_concept_editor():
    history = History()
    case = history.current_case

    # Stage 1 (text mode) defines a variable
    stage1 = case.create_stage('Stage 1')
    comm2study('a = 1', stage1)
    assert_that(stage1.check(), equal_to(Validity.Ok))
    stage1.use_text_mode()
    assert_that(stage1.check(), equal_to(Validity.Ok))

    # Stage 2 (graphical) uses that variable
    stage2 = case.create_stage('Stage 2')
    stage2.add_command('DEFI_CONSTANTE', 'result1').init(dict(VALE=stage1['a']))
    assert_that(stage2.check(), equal_to(Validity.Ok))

    # Now we add another variable to Stage 1 and check it is available in Stage 2
    stage1.add_variable('b', '3')
    stage2.add_command('DEFI_CONSTANTE', 'result2').init(dict(VALE=stage1['b']))
    assert_that(stage2.check(), equal_to(Validity.Ok))

def test_variables_in_concept_editor_with_update():
    history = History()
    case = history.current_case

    # Stage 1 (text mode) defines a and b variables
    stage1 = case.create_stage('Stage 1')
    stage1.use_text_mode()
    assert_that(stage1.check(), equal_to(Validity.Ok))

    defs = [('a', '_CONVERT_VARIABLE', 'I'), ('b', '_CONVERT_VARIABLE', 'I')]
    stage1.update_commands(defs)
    assert_that(stage1.commands, has_length(2))
    assert_that(stage1.check(), equal_to(Validity.Ok))

    # Stage 2 (graphical) uses variables from Stage 1
    stage2 = case.create_stage('Stage 2')
    stage2.add_command('DEFI_CONSTANTE', 'result1').init(dict(VALE=stage1['a']))
    assert_that(stage2.check(), equal_to(Validity.Ok))
    stage2.add_command('DEFI_CONSTANTE', 'result2').init(dict(VALE=stage1['b']))
    assert_that(stage2.check(), equal_to(Validity.Ok))

@attr('fixit')
def test_delete_variables():
    history = History()
    case = history.current_case

    # Stage 1 (text mode) defines a variable
    stage1 = case.create_stage('Stage 1')
    comm2study('a = 1', stage1)
    assert_that(stage1.check(), equal_to(Validity.Ok))
    stage1.use_text_mode()
    assert_that(stage1.check(), equal_to(Validity.Ok))

    # Stage 2 (text mode) is added, empty for now
    stage2 = case.create_stage('Stage 2').use_text_mode()
    assert_that(stage2.check(), equal_to(Validity.Ok))

    # Stage 3 (graphical mode) uses variable from Stage 1
    stage3 = case.create_stage('Stage 3')
    stage3.add_command('DEFI_CONSTANTE', 'result1').init(dict(VALE=stage1['a']))
    assert_that(stage3.check(), equal_to(Validity.Ok))

    # Now we mark variable as deleted in Stage 2
    # Stage 3 should become invalid
    stage2.delete_commands(['a'])
    assert_that(stage3.check(), is_not(equal_to(Validity.Ok)))


if __name__ == "__main__":
    import sys
    from testutils import get_test_suite
    RET = unittest.TextTestRunner(verbosity=2).run(get_test_suite(__name__))
    sys.exit(not RET.wasSuccessful())
