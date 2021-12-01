# -*- coding: utf-8 -*-
"""No description"""

from asterstudy.assistant import widgets as AW
from asterstudy.common import translate


def create_wizard(parent):
    """Factory function."""
    return CalcWizard(parent)


class CalcWizard(AW.Wizard):
    """Wizard dialog."""

    def __init__(self, parent=None):
        """Create wizard."""
        super().__init__(parent)

        title = translate("CalcWizard", "Test calculation assistant")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setObjectName("Test calculation assistant")

        # Page: Page 1
        title = translate("CalcWizard", "Test calculation assistant")
        sub_title = translate("CalcWizard", "Page 1")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Page 1")
        self.addPage(page)

        # >> Group: untitled
        group = AW.Group()
        group.setObjectName("group")
        page.addWidget(group)

        title = translate("CalcWizard", "Table with different data types")
        widget = AW.TableWidget(title)
        column_title = translate("CalcWizard", "String column")
        widget.addColumn("TABLE_PARAM1", column_title, typ="string", into=["value1", "value2"])
        column_title = translate("CalcWizard", "Integer column")
        widget.addColumn("TABLE_PARAM2", column_title, typ="int", val_min=1, val_max=100, default=10)
        column_title = translate("CalcWizard", "Float column")
        widget.addColumn("TABLE_PARAM3", column_title, typ="float", val_max=1000000.0, default=12340.0)
        column_title = translate("CalcWizard", "String column")
        widget.addColumn("TABLE_PARAM4", column_title, typ="string", regex="[a-zA-Z]\w{1,7}", default="test")
        tooltip = translate("CalcWizard", "Description of PARAM1")
        widget.setToolTip(tooltip)
        widget.setObjectName("Table with different data types")
        group.addWidget(widget)
        self.register("PARAM1", widget)

        # Page: Page 2
        title = translate("CalcWizard", "Test calculation assistant")
        sub_title = translate("CalcWizard", "Page 2")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Page 2")
        self.addPage(page)

        title = translate("CalcWizard", "Integer QLineEdit")
        widget = AW.LineEdit(title, typ="int", val_min=1, val_max=100, default=10)
        widget.setObjectName("Integer QLineEdit")
        page.addWidget(widget)
        self.register("PARAM2", widget)

        title = translate("CalcWizard", "Integer QComboBox")
        widget = AW.ComboBox(title, typ="int", into=[11, 22], default=22)
        widget.setObjectName("Integer QComboBox")
        page.addWidget(widget)
        self.register("PARAM3", widget)

        title = translate("CalcWizard", "QCheckBox")
        widget = AW.CheckBox(title, default=True)
        widget.setObjectName("QCheckBox")
        page.addWidget(widget)
        self.register("PARAM4", widget)
