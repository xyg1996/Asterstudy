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

        # Page: Input files
        title = translate("Wizard", "Test calculation assistant")
        sub_title = translate("Wizard", "Input files")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Input files")
        self.addPage(page)

        title = translate("Wizard", "Mesh")
        widget = AW.MeshSelector(title, unit=20, default="foo.med")
        widget.setObjectName("Mesh")
        page.addWidget(widget)
        self.register("MESH", widget)

        title = translate("Wizard", "Input file")
        widget = AW.FileSelector(title, mode="in", unit=21, filters="*.txt;;*.xyz", default="bar.txt")
        widget.setObjectName("Input file")
        page.addWidget(widget)
        self.register("INPUT_FILE", widget)

        # Page: Single group selectors
        title = translate("Wizard", "Test calculation assistant")
        sub_title = translate("Wizard", "Single group selectors")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Single group selectors")
        self.addPage(page)

        title = translate("Wizard", "Group of elements")
        widget = AW.GroupElSelector(title, mesh="MESH", default="ma_group")
        widget.setObjectName("Group of elements")
        page.addWidget(widget)
        self.register("GR_MA", widget)

        title = translate("Wizard", "Group of nodes")
        widget = AW.GroupNoSelector(title, mesh="MESH", default="no_group")
        widget.setObjectName("Group of nodes")
        page.addWidget(widget)
        self.register("GR_NO", widget)

        # Page: Output files
        title = translate("Wizard", "Test calculation assistant")
        sub_title = translate("Wizard", "Output files")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Output files")
        self.addPage(page)

        title = translate("Wizard", "Output file")
        widget = AW.FileSelector(title, mode="out", unit=80, default="foobar.med")
        widget.setObjectName("Output file")
        page.addWidget(widget)
        self.register("OUTPUT_FILE", widget)
