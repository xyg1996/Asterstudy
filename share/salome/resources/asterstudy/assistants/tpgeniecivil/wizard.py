# -*- coding: utf-8 -*-
"""Reinforced concrete beam case study"""

from asterstudy.assistant import widgets as AW
from asterstudy.common import translate


def create_wizard(parent):
    """Factory function."""
    return TPGenieCivil(parent)


class TPGenieCivil(AW.Wizard):
    """Wizard dialog."""

    def __init__(self, parent=None):
        """Create wizard."""
        super().__init__(parent)

        title = translate("TPGenieCivil", "Reinforced concrete beam")
        self.setWindowTitle(title)
        self.setModal(True)
        tooltip = translate("TPGenieCivil", "Reinforced concrete beam case study")
        self.setToolTip(tooltip)
        self.setObjectName("Reinforced concrete beam")

        # Page:
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("page")
        self.addPage(page)

        title = translate("TPGenieCivil", "Introduction")
        widget = AW.Text(
            title,
            text=
            "This wizard will create an analysis using reinforced concrete beams.\n\nBoundary conditions are:\n- blocked displacements,\n- and imposed displacements.\n\nRequirements:\n- a MED file of the 1D beam elements containing the groups of nodes to apply the boundary conditions,\n- and a MED file of the section of the beams.",
            typ="text")
        widget.setObjectName("Introduction")
        page.addWidget(widget)
        self.register("INTRO", widget)

        # Page: Beam mesh selection
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "Beam mesh selection")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Beam mesh selection")
        self.addPage(page)

        title = translate("TPGenieCivil", "Specify input mesh")
        widget = AW.MeshSelector(title, unit=20)
        tooltip = translate("TPGenieCivil", "Enter a path to the MED file or select an existing Mesh object from the list")
        widget.setToolTip(tooltip)
        widget.setObjectName("Specify input mesh")
        page.addWidget(widget)
        self.register("INPUTPOU", widget)

        # Page: Beam definition
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "Beam definition")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Beam definition")
        self.addPage(page)

        title = translate("TPGenieCivil", "Select the group that defines the beam")
        widget = AW.GroupElSelector(title, mesh="INPUTPOU")
        widget.setObjectName("Select the group that defines the beam")
        page.addWidget(widget)
        self.register("GROUP_BEAM", widget)

        # Page: Cross-section mesh selection
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "Cross-section mesh selection")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Cross-section mesh selection")
        self.addPage(page)

        title = translate("TPGenieCivil", "Specify input mesh")
        widget = AW.MeshSelector(title, unit=22)
        tooltip = translate("TPGenieCivil", "Enter a path to the MED file or select an existing Mesh object from the list")
        widget.setToolTip(tooltip)
        widget.setObjectName("Specify input mesh")
        page.addWidget(widget)
        self.register("INPUTSEC", widget)

        # Page: Material properties
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "Material properties")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Material properties")
        self.addPage(page)

        title = translate("TPGenieCivil", "Concrete type")
        widget = AW.ComboBox(title, typ="string", into=["C30/37", "C60/75", "C70/85", "C80/95", "C90/105"], default="C30/37")
        tooltip = translate("TPGenieCivil", "Choose concrete type amongst the list")
        widget.setToolTip(tooltip)
        widget.setObjectName("Concrete type")
        page.addWidget(widget)
        self.register("CBETON", widget)

        title = translate("TPGenieCivil", "Steel yield stress")
        widget = AW.LineEdit(title, typ="float")
        tooltip = translate("TPGenieCivil", "Enter value")
        widget.setToolTip(tooltip)
        widget.setObjectName("Steel yield stress")
        page.addWidget(widget)
        self.register("SIGY_ACIER", widget)

        # Page: Steel reinforcement location
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "Steel reinforcement location")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Steel reinforcement location")
        self.addPage(page)

        title = translate("TPGenieCivil", "Steel reinforcement location and diameter")
        widget = AW.MatrixWidget(title)
        column_title = translate("TPGenieCivil", "x")
        widget.addColumn("X_STEEL", column_title, typ="float")
        column_title = translate("TPGenieCivil", "y")
        widget.addColumn("Y_STEEL", column_title, typ="float")
        column_title = translate("TPGenieCivil", "Diameter")
        widget.addColumn("DIAM_STEEL", column_title, typ="float")
        tooltip = translate("TPGenieCivil", "Enter the positions and section of the steel bars")
        widget.setToolTip(tooltip)
        widget.setObjectName("Steel reinforcement location and diameter")
        page.addWidget(widget)
        self.register("VALE_TRIPLET", widget)

        # Page: Result
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "Result")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Result")
        self.addPage(page)

        title = translate("TPGenieCivil", "Specify output result file for beam cross-section mesh")
        widget = AW.FileSelector(title, mode="out", unit=80)
        tooltip = translate("TPGenieCivil", "Enter a path to the MED result file")
        widget.setToolTip(tooltip)
        widget.setObjectName("Specify output result file for beam cross-section mesh")
        page.addWidget(widget)
        self.register("OUTPUTFIBSEC", widget)

        title = translate("TPGenieCivil", "Specify output result file for local coordinate systems")
        widget = AW.FileSelector(title, mode="out", unit=81)
        tooltip = translate("TPGenieCivil", "Enter a path to the MED result file")
        widget.setToolTip(tooltip)
        widget.setObjectName("Specify output result file for local coordinate systems")
        page.addWidget(widget)
        self.register("OUTPUTREPLOC", widget)

        title = translate("TPGenieCivil", "Specify output result file for reinforcement beams location")
        widget = AW.FileSelector(title, mode="out", unit=82)
        tooltip = translate("TPGenieCivil", "Enter a path to the MED result file")
        widget.setToolTip(tooltip)
        widget.setObjectName("Specify output result file for reinforcement beams location")
        page.addWidget(widget)
        self.register("OUTPUTFIBPOS", widget)

        # Page: Boundary conditions (1/2)
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "Boundary conditions (1/2)")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Boundary conditions (1/2)")
        self.addPage(page)

        title = translate("TPGenieCivil", "Blocked degrees of freedom on groups")
        widget = AW.TableWidget(title, mesh="INPUTPOU", rule="{GROUP_NO!r} is not None and set([{DX}, {DY}, {DZ}, {DRX}, {DRY}, {DRZ}]).difference([None])")
        column_title = translate("TPGenieCivil", "Group")
        widget.addColumn("GROUP_NO", column_title, typ="groups_no")
        column_title = translate("TPGenieCivil", "DX")
        widget.addColumn("DX", column_title, typ="float", mandatory=False)
        column_title = translate("TPGenieCivil", "DY")
        widget.addColumn("DY", column_title, typ="float", mandatory=False)
        column_title = translate("TPGenieCivil", "DZ")
        widget.addColumn("DZ", column_title, typ="float", mandatory=False)
        column_title = translate("TPGenieCivil", "DRX")
        widget.addColumn("DRX", column_title, typ="float", mandatory=False)
        column_title = translate("TPGenieCivil", "DRY")
        widget.addColumn("DRY", column_title, typ="float", mandatory=False)
        column_title = translate("TPGenieCivil", "DRZ")
        widget.addColumn("DRZ", column_title, typ="float", mandatory=False)
        tooltip = translate("TPGenieCivil", "Select groups and apply degrees of freedom on them")
        widget.setToolTip(tooltip)
        widget.setObjectName("Blocked degrees of freedom on groups")
        page.addWidget(widget)
        self.register("BC", widget)

        # Page: Boundary conditions (2/2)
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "Boundary conditions (2/2)")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Boundary conditions (2/2)")
        self.addPage(page)

        title = translate("TPGenieCivil", "Imposed degrees of freedom on groups")
        widget = AW.TableWidget(title, mesh="INPUTPOU", rule="{GROUP_NO!r} is not None and set([{DX}, {DY}, {DZ}]).difference([None])")
        column_title = translate("TPGenieCivil", "Group")
        widget.addColumn("GROUP_NO", column_title, typ="groups_no")
        column_title = translate("TPGenieCivil", "DX")
        widget.addColumn("DX", column_title, typ="float", mandatory=False)
        column_title = translate("TPGenieCivil", "DY")
        widget.addColumn("DY", column_title, typ="float", mandatory=False)
        column_title = translate("TPGenieCivil", "DZ")
        widget.addColumn("DZ", column_title, typ="float", mandatory=False)
        tooltip = translate("TPGenieCivil", "Select groups and apply apply degrees of freedom on them")
        widget.setToolTip(tooltip)
        widget.setObjectName("Imposed degrees of freedom on groups")
        page.addWidget(widget)
        self.register("LOAD", widget)

        # Page: Time discretisation
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "Time discretisation")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Time discretisation")
        self.addPage(page)

        title = translate("TPGenieCivil", "Time steps (0. is already included with a nul load coefficient)")
        widget = AW.TableWidget(title)
        column_title = translate("TPGenieCivil", "Up until...")
        widget.addColumn("JUSQU_A", column_title, typ="float")
        column_title = translate("TPGenieCivil", "number of substeps")
        widget.addColumn("NOMBRE", column_title, typ="int", default=1)
        column_title = translate("TPGenieCivil", "load coefficient")
        widget.addColumn("COEF", column_title, typ="float")
        tooltip = translate("TPGenieCivil", "Enter a list of times")
        widget.setToolTip(tooltip)
        widget.setObjectName("Time steps (0. is already included with a nul load coefficient)")
        page.addWidget(widget)
        self.register("TIME", widget)

        title = translate("TPGenieCivil", "Do you want to add a subdivision?")
        choices = AW.Choices(title)
        choices.setObjectName("Do you want to add a subdivision?")
        page.addWidget(choices)
        self.register("SUBD", choices)

        # >> >> Choice: Yes
        choice_title = translate("TPGenieCivil", "Yes")
        choice = choices.addChoice("YES_SUBD", choice_title)

        title = translate("TPGenieCivil", "Subdivision step")
        widget = AW.LineEdit(title, typ="int", default=10)
        tooltip = translate("TPGenieCivil", "Subdivision step")
        widget.setToolTip(tooltip)
        widget.setObjectName("Subdivision step")
        choice.addWidget(widget)
        self.register("SUBD_PAS1", widget)

        title = translate("TPGenieCivil", "Subdivision level")
        widget = AW.LineEdit(title, typ="int", default=10)
        tooltip = translate("TPGenieCivil", "Enter level")
        widget.setToolTip(tooltip)
        widget.setObjectName("Subdivision level")
        choice.addWidget(widget)
        self.register("SUBD_NIVEAU1", widget)

        # >> >> Choice: No
        choice_title = translate("TPGenieCivil", "No")
        choice = choices.addChoice("NO_SUBD", choice_title)

        # Page: Results
        title = translate("TPGenieCivil", "Reinforced concrete beam")
        sub_title = translate("TPGenieCivil", "Results")
        page = AW.WizardPage(title, sub_title=sub_title)
        page.setObjectName("Results")
        self.addPage(page)

        title = translate("TPGenieCivil", "Specify output result file")
        widget = AW.FileSelector(title, mode="out", unit=90)
        tooltip = translate("TPGenieCivil", "Enter a path to the MED result file")
        widget.setToolTip(tooltip)
        widget.setObjectName("Specify output result file")
        page.addWidget(widget)
        self.register("OUTPUT", widget)

    def value(self):
        """
        Adapt and return wizard context.

        Returns:
            dict: Dictionary mapping each parameter to its value.
        """
        value = super().value()
        intervalle = tuple(list(value['TIME']))
        value['INSTFIN'] = intervalle[-1]['JUSQU_A']
        value['FOMULT'] = [0., 0.]
        for time in intervalle:
            value['FOMULT'].extend([time['JUSQU_A'], time['COEF']])
            del time['COEF']
        value['INTERVALLE'] = tuple(intervalle)
        return value
