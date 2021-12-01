# -*- coding: utf-8 -*-

# Copyright 2016 - 2019 EDF R&D
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

"""Common functionality for testing wizards."""

from PyQt5 import Qt as Q

from hamcrest import *

from asterstudy.assistant import Runner
from asterstudy.assistant.widgets import TableWidget, Choices


def check_runner(wizard, template, values):
    runner = Runner(None)
    runner.wizard_data = wizard
    runner.template_data = template
    runner.createWizard()

    def _mock_validity(cls):
        return True

    for widget in runner.wizard.widgets:
        widget.__class__.checkValidity = classmethod(_mock_validity)

    def _mock_visited(cls, int):
        return True

    def _mock_value(cls):
        return values

    runner.wizard.__class__.hasVisitedPage = classmethod(_mock_visited)
    runner.wizard.__class__.value = classmethod(_mock_value)

    uids = runner.wizard.pageIds()
    for uid in uids:
        runner.wizard.page(uid).validatePage()

    runner._wizardFinished(Q.QDialog.Accepted)

    return runner
