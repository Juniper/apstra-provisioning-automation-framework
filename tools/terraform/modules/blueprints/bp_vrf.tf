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

# Configure Routing Zones
resource "apstra_datacenter_routing_zone" "vrfs" {
  depends_on = [
    apstra_datacenter_routing_policy.routing_policies,
  ]
  # local.flattened_vrfs is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and vrf_name keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_vrfs) ? {
    for vrf in local.flattened_vrfs : "${vrf.bp}.${vrf.name}" => vrf
    if vrf.vrf_type == "user_defined"
  } : null
  blueprint_id         = local.blueprint_ids[each.value.bp]
  name                 = each.value.name
  vlan_id              = try(each.value.vlan_id, null)
  vni                  = try(each.value.vni, null)
  dhcp_servers         = try(each.value.dhcp_servers, null)
  export_route_targets = try(each.value.export_route_targets, null)
  import_route_targets = try(each.value.import_route_targets, null)
  junos_evpn_irb_mode  = try(each.value.junos_evpn_irb_mode, null)
  routing_policy_id    = try(local.routing_policy_ids["${each.value.bp}.${each.value.routing_policy}"], null)
}

# Gather the data of both pre-existing Routing Zones (pre-created in Apstra, not user-defined) and user-defined Routing Zones in a single list
data "apstra_datacenter_routing_zone" "vrfs" {
  # local.flattened_vrfs is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and vrf_name keys to
  # produce a single unique key per instance.

  depends_on = [
    apstra_datacenter_routing_zone.vrfs,
  ]

  for_each = can(local.flattened_vrfs) ? {
    for vrf in local.flattened_vrfs : "${vrf.bp}.${vrf.name}" => vrf
  } : null
  blueprint_id = local.blueprint_ids[each.value.bp]
  name         = each.value.name
}


