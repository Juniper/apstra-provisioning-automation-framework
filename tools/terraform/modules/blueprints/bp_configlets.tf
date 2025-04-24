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

# ----- Configlet resources // Module: blueprints

# Import property_sets from the Design menu into the Blueprint

resource "apstra_datacenter_configlet" "configlets" {
  for_each = can(local.flattened_configlets) ? {
    for configlet in try(local.flattened_configlets, null) : "${configlet.bp}.${configlet.name}" => configlet
  } : null
  blueprint_id         = local.blueprint_ids[each.value.bp]
  catalog_configlet_id = try(local.configlet_ids["${each.value.name}"], null)

  condition = join(" ", [
    for scope in each.value.scope :
    # Examples: role in ["spine", "leaf"], hostname in [\"apstra-esi-001-leaf1\", \"apstra-esi-001-leaf2\]"
    (contains(["role", "name", "hostname"], scope.condition) && index(each.value.scope, scope) == 0) ? try("${scope.condition} ${scope.inclusion} [${join(", ", [for filter in scope.filter : format("%q", filter)])}]", null) :
    (contains(["role", "name", "hostname"], scope.condition) && index(each.value.scope, scope) > 0) ? try("${scope.conjunction} ${scope.condition} ${scope.inclusion} [${join(", ", [for filter in scope.filter : format("%q", filter)])}]", null) :
    # Example: ("sriov" in tags)
    (contains(["tags"], scope.condition) && index(each.value.scope, scope) == 0) ? try("(\"${scope.filter[0]}\" ${scope.inclusion} ${scope.condition})", null) :
    (contains(["tags"], scope.condition) && index(each.value.scope, scope) > 0) ? try("${scope.conjunction} (\"${scope.filter[0]}\" ${scope.inclusion} ${scope.condition})", null) :
    null
  ])
}
