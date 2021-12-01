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

        title = translate("Wizard", "Integer QComboBox")
        widget = AW.ComboBox(title, typ="int", into=[11, 22], default=22)
        tooltip = translate("Wizard", "Description of PARAM1")
        widget.setToolTip(tooltip)
        widget.setObjectName("Integer QComboBox")
        page.addWidget(widget)
        self.register("PARAM1", widget)

        # Page: Page 2
        title = translate("Wizard", "Test calculation assistant")
        sub_title = translate("Wizard", "Page 2")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Page 2")
        self.addPage(page)

        # >> Group: Group of parameters
        title = translate("Wizard", "Group of parameters")
        group = AW.Group(title)
        group.setObjectName("Group of parameters")
        page.addWidget(group)

        title = translate("Wizard", "Integer QLineEdit")
        widget = AW.LineEdit(title, typ="int", val_min=1, val_max=100, default=10)
        tooltip = translate("Wizard", "Description of PARAM2")
        widget.setToolTip(tooltip)
        widget.setObjectName("Integer QLineEdit")
        group.addWidget(widget)
        self.register("PARAM2", widget)

        title = translate("Wizard", "Float QLineEdit")
        widget = AW.LineEdit(title, typ="float", val_max=1000000.0, default=12340.0)
        tooltip = translate("Wizard", "Description of PARAM3")
        widget.setToolTip(tooltip)
        widget.setObjectName("Float QLineEdit")
        group.addWidget(widget)
        self.register("PARAM3", widget)

        title = translate("Wizard", "String QLineEdit")
        widget = AW.LineEdit(title, typ="string", regex="[a-zA-Z]\w{1,7}", default="test")
        tooltip = translate("Wizard", "Description of PARAM4")
        widget.setToolTip(tooltip)
        widget.setObjectName("String QLineEdit")
        group.addWidget(widget)
        self.register("PARAM4", widget)
