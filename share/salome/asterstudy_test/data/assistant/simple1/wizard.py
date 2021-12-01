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

        title = translate("Wizard", "Integer QLineEdit")
        widget = AW.LineEdit(title, typ="int", val_min=1, val_max=100, default=10)
        tooltip = translate("Wizard", "Description of PARAM1")
        widget.setToolTip(tooltip)
        widget.setObjectName("Integer QLineEdit")
        page.addWidget(widget)
        self.register("PARAM1", widget)
