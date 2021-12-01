# Copyright (C) 2016  CEA/DEN, EDF R&D
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

set(SALOME_TEST_DRIVER "$ENV{KERNEL_ROOT_DIR}/bin/salome/appliskel/salome_test_driver.py")

set(COMPONENT_NAME ASTERSTUDY)
set(TIMEOUT        500)

set(ASTERSTUDY_TEST_FILES "datamodel/test_add_unit.py;datamodel/test_affe_cara_elem.py;datamodel/test_api_execution.py;datamodel/test_api_remote.py;datamodel/test_automatic_naming.py;datamodel/test_backup_utility.py;datamodel/test_case.py;datamodel/test_catalog.py;datamodel/test_categories.py;datamodel/test_command.py;datamodel/test_command_as_text.py;datamodel/test_command_consistency.py;datamodel/test_command_dependency.py;datamodel/test_command_introspection.py;datamodel/test_command_name_type.py;datamodel/test_command_return_type.py;datamodel/test_command_validity.py;datamodel/test_context.py;datamodel/test_conversion.py;datamodel/test_convert_mesh.py;datamodel/test_copy_results.py;datamodel/test_dataset.py;datamodel/test_decoder.py;datamodel/test_embedded_files.py;datamodel/test_engine_asrun.py;datamodel/test_engine_asrun_remote.py;datamodel/test_engine_direct.py;datamodel/test_engine_generic.py;datamodel/test_engine_misc.py;datamodel/test_engine_salome.py;datamodel/test_engine_salome_remote.py;datamodel/test_engine_simulator.py;datamodel/test_export.py;datamodel/test_export_default.py;datamodel/test_fakecmd.py;datamodel/test_file_basic.py;datamodel/test_file_conflicts.py;datamodel/test_file_stage_context.py;datamodel/test_formula.py;datamodel/test_freeze_1349.py;datamodel/test_general.py;datamodel/test_history.py;datamodel/test_history_folder.py;datamodel/test_import2study.py;datamodel/test_import_broken_file.py;datamodel/test_import_comp001h.py;datamodel/test_import_errors.py;datamodel/test_import_fdlv102b.py;datamodel/test_import_reuse.py;datamodel/test_import_szlz106a.py;datamodel/test_import_szlz108b.py;datamodel/test_import_test_table.py;datamodel/test_import_test_table2.py;datamodel/test_import_variable.py;datamodel/test_import_zzzz289f.py;datamodel/test_include.py;datamodel/test_issue27114.py;datamodel/test_issue27134.py;datamodel/test_issue27760.py;datamodel/test_issue_0784.py;datamodel/test_issue_0791.py;datamodel/test_issue_0915.py;datamodel/test_issue_0941.py;datamodel/test_issue_0964.py;datamodel/test_issue_0965.py;datamodel/test_issue_0973.py;datamodel/test_issue_0980.py;datamodel/test_issue_0984.py;datamodel/test_issue_0988.py;datamodel/test_issue_1009.py;datamodel/test_issue_1013.py;datamodel/test_issue_1018.py;datamodel/test_issue_1072.py;datamodel/test_issue_1095.py;datamodel/test_issue_1137_comment_management.py;datamodel/test_issue_1138_variable_management.py;datamodel/test_issue_1139_command_copy_paste.py;datamodel/test_issue_1152_variable_usage.py;datamodel/test_issue_1153_macro_keyword_management.py;datamodel/test_issue_1161_backup_restore_case.py;datamodel/test_issue_1171.py;datamodel/test_issue_1201.py;datamodel/test_issue_1221.py;datamodel/test_issue_1226.py;datamodel/test_issue_1233.py;datamodel/test_issue_1237.py;datamodel/test_issue_1288.py;datamodel/test_issue_1407.py;datamodel/test_issue_1609.py;datamodel/test_issue_1620.py;datamodel/test_issue_1682.py;datamodel/test_issue_1684.py;datamodel/test_issue_1705.py;datamodel/test_issue_1727.py;datamodel/test_issue_1733.py;datamodel/test_issue_1769.py;datamodel/test_issue_1777.py;datamodel/test_issue_1815.py;datamodel/test_issue_1852.py;datamodel/test_issue_1943_variables_in_concept_editor.py;datamodel/test_issue_26196.py;datamodel/test_issue_26514.py;datamodel/test_issue_26683.py;datamodel/test_issue_27243.py;datamodel/test_issue_27279.py;datamodel/test_issue_27499.py;datamodel/test_issue_27893.py;datamodel/test_issue_27902.py;datamodel/test_issue_27948.py;datamodel/test_issue_28550.py;datamodel/test_issue_29072.py;datamodel/test_message.py;datamodel/test_model_deps.py;datamodel/test_node.py;datamodel/test_parametric.py;datamodel/test_persistence.py;datamodel/test_recover.py;datamodel/test_remove_command_from_case.py;datamodel/test_remove_command_from_stage.py;datamodel/test_remove_stage_from_case.py;datamodel/test_rename_command_in_case.py;datamodel/test_result.py;datamodel/test_sequential.py;datamodel/test_stage.py;datamodel/test_sync.py;datamodel/test_template.py;datamodel/test_text_command_return_type.py;datamodel/test_text_dataset.py;datamodel/test_undo_redo.py;datamodel/test_unit_basic.py;datamodel/test_unit_registering.py;datamodel/test_use_command_from_other_stage.py;datamodel/test_utilities.py;datamodel/test_validation.py;datamodel/test_version_selection.py;datamodel/test_visiting_groups.py;guimodel/test_assistant.py;guimodel/test_catalogsview.py;guimodel/test_category.py;guimodel/test_category_model.py;guimodel/test_conceptseditor.py;guimodel/test_exec_wizard.py;guimodel/test_file_descriptors_model.py;guimodel/test_infoview.py;guimodel/test_issue_1626.py;guimodel/test_issue_1648.py;guimodel/test_issue_1672.py;guimodel/test_issue_1719.py;guimodel/test_issue_1724.py;guimodel/test_unit_model.py")

set(ASTERSTUDY_TEST_FILES_INTEGR "datamodel/test_case.py;datamodel/test_engine_salome.py;datamodel/test_general.py;datamodel/test_import_test_table.py;datamodel/test_import_variable.py;datamodel/test_message.py")

set(ENV{ASTERSTUDYDIR} "$ENV{ASTERSTUDY_ROOT_DIR}/share/salome/asterstudy_test")


foreach(_path ${ASTERSTUDY_TEST_FILES})
  get_filename_component(_name ${_path} NAME)
  set(TEST_NAME ASTERSTUDY_${_name})
  add_test(${TEST_NAME} python ${SALOME_TEST_DRIVER} ${TIMEOUT} $ENV{ASTERSTUDYDIR}/${_path})

  set(_props "${COMPONENT_NAME}")

  string(FIND "${ASTERSTUDY_TEST_FILES_INTEGR}" ${_path} _found)
  if(${_found} GREATER -1)
    string(CONCAT _props "${_props}" ";" "SMECA_INTEGR")
  endif()

  string(FIND ${TEST_NAME} "remote.py" _found)
  if(${_found} GREATER -1)
    string(CONCAT _props "${_props}" ";" "SMECA_REMOTE")
  endif()

  set_tests_properties(${TEST_NAME} PROPERTIES
    LABELS "${_props}"
    ENVIRONMENT "PYTHONPATH=$ENV{ASTERSTUDYDIR}:$ENV{PYTHONPATH}"
    )
endforeach()
