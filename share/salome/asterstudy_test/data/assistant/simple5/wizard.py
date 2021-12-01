# -*- coding: utf-8 -*-
"""No description"""

from asterstudy.assistant import widgets as AW
from asterstudy.common import translate


def create_wizard(parent):
    """Factory function."""
    return Wizard(parent)


class Wizard(AW.Wizard):
    """Wizard dialog."""

    def __init__(self, parent=None):
        """Create wizard."""
        super().__init__(parent)

        title = translate("Wizard", "Test calculation assistant")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setObjectName("Test calculation assistant")

        # Page: Page 1
        title = translate("Wizard", "Test calculation assistant")
        sub_title = translate("Wizard", "Page 1")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Page 1")
        self.addPage(page)

        title = translate("Wizard", "Choices")
        choices = AW.Choices(title, default="CHOICE_1")
        tooltip = translate("Wizard", "Set of choices")
        choices.setToolTip(tooltip)
        choices.setObjectName("Choices")
        page.addWidget(choices)
        self.register("CHOICE", choices)

        # >> >> Choice: First choice
        choice_title = translate("Wizard", "First choice")
        choice = choices.addChoice("CHOICE_1", choice_title)

        title = translate("Wizard", "Integer parameter")
        widget = AW.LineEdit(title, typ="int", default=100)
        widget.setObjectName("Integer parameter")
        choice.addWidget(widget)
        self.register("PARAM1", widget)

        # >> >> Choice: Second choice
        choice_title = translate("Wizard", "Second choice")
        choice = choices.addChoice("CHOICE_2", choice_title)

        title = translate("Wizard", "Float parameter")
        widget = AW.LineEdit(title, typ="float", default=1.2)
        widget.setObjectName("Float parameter")
        choice.addWidget(widget)
        self.register("PARAM2", widget)

        # >> >> Choice: Third choice
        choice_title = translate("Wizard", "Third choice")
        choice = choices.addChoice("CHOICE_3", choice_title)

        title = translate("Wizard", "String parameter")
        widget = AW.LineEdit(title, default="aaa")
        widget.setObjectName("String parameter")
        choice.addWidget(widget)
        self.register("PARAM3", widget)

        # >> >> Choice: Fourth choice
        choice_title = translate("Wizard", "Fourth choice")
        choices.addChoice("CHOICE_4", choice_title)
