# -*- coding: utf-8 -*-
"""Contact analysis case study"""

from asterstudy.assistant import widgets as AW
from asterstudy.common import translate


def create_wizard(parent):
    """Factory function."""
    return ContactAnalysis(parent)


class ContactAnalysis(AW.Wizard):
    """Wizard dialog."""

    def __init__(self, parent=None):
        """Create wizard."""
        super().__init__(parent)

        title = translate("ContactAnalysis", "Contact analysis")
        self.setWindowTitle(title)
        self.setModal(True)
        tooltip = translate("ContactAnalysis", "Contact analysis case study")
        self.setToolTip(tooltip)
        self.setObjectName("Contact analysis")

        # Page:
        title = translate("ContactAnalysis", "Contact analysis")
        sub_title = translate("ContactAnalysis", "")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("page")
        self.addPage(page)

        title = translate("ContactAnalysis", "Introduction")
        widget = AW.Text(
            title,
            text=
            "This wizard will create a study with contact conditions between two surfaces.\n\nBoundary conditions are:\n- blocked displacements,\n- pressures,\n- and contact conditions between two surfaces.\n\nRequirements:\n- MED file containing a 2D or 3D mesh.\n- Defining a contact zone and applying a pressure needs a surface with consistent oriented normals.",
            typ="text")
        widget.setObjectName("Introduction")
        page.addWidget(widget)
        self.register("INTRO", widget)

        # Page: Mesh selection
        title = translate("ContactAnalysis", "Contact analysis")
        sub_title = translate("ContactAnalysis", "Mesh selection")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Mesh selection")
        self.addPage(page)

        title = translate("ContactAnalysis", "Specify input mesh")
        widget = AW.MeshSelector(title, unit=20)
        tooltip = translate("ContactAnalysis", "Enter a path to the MED file or select an existing Mesh object from the list")
        widget.setToolTip(tooltip)
        widget.setObjectName("Specify input mesh")
        page.addWidget(widget)
        self.register("INPUT", widget)

        # Page: Model definition
        title = translate("ContactAnalysis", "Contact analysis")
        sub_title = translate("ContactAnalysis", "Model definition")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Model definition")
        self.addPage(page)

        title = translate("ContactAnalysis", "What kind of model do you want to work on?")
        widget = AW.ComboBox(title, typ="string", into=["3D", "C_PLAN", "D_PLAN", "AXIS"], default="3D")
        tooltip = translate("ContactAnalysis", "Choose model type from the list")
        widget.setToolTip(tooltip)
        widget.setObjectName("What kind of model do you want to work on?")
        page.addWidget(widget)
        self.register("MODELISATION", widget)

        # Page: Material properties
        title = translate("ContactAnalysis", "Contact analysis")
        sub_title = translate("ContactAnalysis", "Material properties")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Material properties")
        self.addPage(page)

        title = translate("ContactAnalysis", "Young's modulus (E)")
        widget = AW.LineEdit(title, typ="float", val_min=0, default=210000000000.0)
        tooltip = translate("ContactAnalysis", "Enter value >= {val_min}")
        widget.setToolTip(tooltip)
        widget.setObjectName("Young's modulus (E)")
        page.addWidget(widget)
        self.register("E", widget)

        title = translate("ContactAnalysis", "Poisson's ratio (v)")
        widget = AW.LineEdit(title, typ="float", val_min=-1, val_max=0.5, default=0.3)
        tooltip = translate("ContactAnalysis", "Enter value between {val_min} and {val_max}")
        widget.setToolTip(tooltip)
        widget.setObjectName("Poisson's ratio (v)")
        page.addWidget(widget)
        self.register("NU", widget)

        # Page: Boundary conditions (1/2)
        title = translate("ContactAnalysis", "Contact analysis")
        sub_title = translate("ContactAnalysis", "Boundary conditions (1/2)")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Boundary conditions (1/2)")
        self.addPage(page)

        title = translate("ContactAnalysis", "Imposed degrees of freedom on groups")
        widget = AW.TableWidget(title, rule="{GROUP_MA!r} is not None and ({DX!r} is not None or {DY!r} is not None or {DZ!r} is not None)")
        column_title = translate("ContactAnalysis", "Group")
        widget.addColumn("GROUP_MA", column_title, typ="groups_ma")
        column_title = translate("ContactAnalysis", "DX")
        widget.addColumn("DX", column_title, typ="float", mandatory=False)
        column_title = translate("ContactAnalysis", "DY")
        widget.addColumn("DY", column_title, typ="float", mandatory=False)
        column_title = translate("ContactAnalysis", "DZ")
        widget.addColumn("DZ", column_title, typ="float", mandatory=False)
        tooltip = translate("ContactAnalysis", "Select mesh groups and apply degrees of freedom on them")
        widget.setToolTip(tooltip)
        widget.setObjectName("Imposed degrees of freedom on groups")
        page.addWidget(widget)
        self.register("BC", widget)

        # Page: Boundary conditions (2/2)
        title = translate("ContactAnalysis", "Contact analysis")
        sub_title = translate("ContactAnalysis", "Boundary conditions (2/2)")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Boundary conditions (2/2)")
        self.addPage(page)

        title = translate("ContactAnalysis", "Pressure on meshes groups")
        widget = AW.TableWidget(title)
        column_title = translate("ContactAnalysis", "Group")
        widget.addColumn("GROUP_MA", column_title, typ="groups_ma")
        column_title = translate("ContactAnalysis", "Pressure")
        widget.addColumn("PRES", column_title, typ="float", default=0)
        tooltip = translate("ContactAnalysis", "Select mesh groups and apply pressure on them")
        widget.setToolTip(tooltip)
        widget.setObjectName("Pressure on meshes groups")
        page.addWidget(widget)
        self.register("LOAD", widget)

        # Page: Contact definition
        title = translate("ContactAnalysis", "Contact analysis")
        sub_title = translate("ContactAnalysis", "Contact definition")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Contact definition")
        self.addPage(page)

        title = translate("ContactAnalysis", "Contact algorithm")
        choices = AW.Choices(title)
        tooltip = translate("ContactAnalysis", "Choose contact algorithm")
        choices.setToolTip(tooltip)
        choices.setObjectName("Contact algorithm")
        page.addWidget(choices)
        self.register("CONTACT", choices)

        # >> >> Choice: Standard method
        choice_title = translate("ContactAnalysis", "Standard method")
        choices.addChoice("STANDARD", choice_title)

        # >> >> Choice: LAC method
        choice_title = translate("ContactAnalysis", "LAC method")
        choices.addChoice("LAC", choice_title)

        title = translate("ContactAnalysis", "Contact zones definition")
        widget = AW.TableWidget(title)
        column_title = translate("ContactAnalysis", "Master zone")
        widget.addColumn("GROUP_MA_MAIT", column_title, typ="group_ma")
        column_title = translate("ContactAnalysis", "Slave zone")
        widget.addColumn("GROUP_MA_ESCL", column_title, typ="group_ma")
        tooltip = translate("ContactAnalysis", "Select mesh groups to define contact zones")
        widget.setToolTip(tooltip)
        widget.setObjectName("Contact zones definition")
        page.addWidget(widget)
        self.register("ZONES", widget)

    def value(self):
        """
        Adapt and return wizard context.

        Returns:
            dict: Dictionary mapping each parameter to its value.
        """
        value = super().value()
        groups = []
        slave_zones = []
        zones = []
        for zone in value['ZONES']:
            zone.update(dict(ALGO_CONT=value['CONTACT']))
            zones.append(zone)
            slave_zones.append(zone['GROUP_MA_ESCL'])
            groups.append(zone['GROUP_MA_MAIT'])
        value['ZONES'] = tuple(zones)
        value['SLAVE_ZONES'] = tuple(set(slave_zones)) # groups must not repeat!
        groups.extend(slave_zones)
        for load in value['LOAD']:
            groups.append(load['GROUP_MA'])
        value['ORIE_GROUPS'] = tuple(set(groups))
        return value
