# ********************************************************
#
# Project: Apstra Provisioning Automation Framework
#
# Copyright (c) Juniper Networks, Inc., 2025. All rights reserved.
#
# Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html
#
# SPDX-License-Identifier: Apache-2.0
#
# Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.
#
# ********************************************************

# Imported modules, local variables and output modules stored in independent files maintain a well-organized and readable module structure.

# ----- Porperty set resources // Module: blueprints

resource "terraform_data" "update_property_sets_trigger" {
  for_each = can(local.flattened_property_sets) ? {
    for property_set in try(local.flattened_property_sets, null) :
    "${property_set.bp}.${property_set.name}" => module.design.property_sets[property_set.name]
    if contains(keys(local.property_set_ids_from_local_project), property_set.name)
  } : null

  input = each.value.data
}

# Import property_sets from the Design menu into the Blueprint

# This set of code is split into two resources:
# - resource "same_project_property_sets" --> to import property sets created in the design menu within the same project.
# - resource "other_project_property_sets" --> to import property sets created in the design menu within an ancestor project.

# The key difference is that the "replace_triggered_by" clause exists in the "same_project_property_sets" resource
# to trigger the replacement of the full property set if its contents change in the global catalog.

# Since this is unnecessary for property sets created in other projects, the resource "other_project_property_sets" does not include this clause.

# This split allows us to manage both locally and remotely created Property Sets (PS) efficiently, each with the appropriate conditions and lifecycle management.
resource "apstra_datacenter_property_set" "same_project_property_sets" {

  # local.flattened_property_sets is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and ps_name keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_property_sets) ? {
    for property_set in try(local.flattened_property_sets, null) :
    "${property_set.bp}.${property_set.name}" => property_set
    if contains(keys(local.property_set_ids_from_local_project), property_set.name)
  } : null
  lifecycle {
    # Replace only if the contents of this specific property_set changes
    replace_triggered_by = [
      terraform_data.update_property_sets_trigger[each.key]
    ]
  }
  blueprint_id      = local.blueprint_ids[each.value.bp]
  id                = local.property_set_ids["${each.value.name}"]
  sync_with_catalog = try(each.value.sync_with_catalog, false)
}

resource "apstra_datacenter_property_set" "other_project_property_sets" {

  # local.flattened_property_sets is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and ps_name keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_property_sets) ? {
    for property_set in try(local.flattened_property_sets, null) :
    "${property_set.bp}.${property_set.name}" => property_set
    if contains(keys(local.property_set_ids_from_parent_project), property_set.name)
  } : null

  blueprint_id      = local.blueprint_ids[each.value.bp]
  id                = local.property_set_ids["${each.value.name}"]
  sync_with_catalog = try(each.value.sync_with_catalog, false)
}
