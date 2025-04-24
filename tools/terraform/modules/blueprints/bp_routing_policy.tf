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

# ----- Resources // Module: blueprints

# Configure Routing Policies
resource "apstra_datacenter_routing_policy" "routing_policies" {
  # local.flattened_routing_policies is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and name keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_routing_policies) ? {
    for routing_policy in try(local.flattened_routing_policies, []) : "${routing_policy.bp}.${routing_policy.name}" => routing_policy
  } : null
  blueprint_id        = local.blueprint_ids[each.value.bp]
  name                = each.value.name
  description         = try(each.value.description, null)
  import_policy       = try(each.value.import_policy, null)
  extra_imports       = try(each.value.extra_imports, null)
  export_policy       = try(each.value.export_policy, null)
  extra_exports       = try(each.value.extra_exports, null)
  aggregate_prefixes  = try(each.value.aggregate_prefixes, null)
  expect_default_ipv4 = try(each.value.expect_default_ipv4, false)
  expect_default_ipv6 = try(each.value.expect_default_ipv6, false)
}
