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

# This data source returns Graph DB node IDs of system nodes within a Blueprint.
# Optional filters can be used to select only interesting nodes.

data "apstra_datacenter_systems" "vn_bindings" {

  depends_on = [
    apstra_datacenter_device_allocation.devices
  ]

  # local.flattened_vn_bindings is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and vn_binding vlan_id keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_vn_bindings) ? {
    for vn_binding in try(local.flattened_vn_bindings, []) : "${vn_binding.bp}.${vn_binding.vn}.${vn_binding.vlan_id}" => vn_binding
  } : null
  blueprint_id = local.blueprint_ids[each.value.bp]
  filters      = try(each.value.filters, null)
}
# This data source can be used to calculate the bindings data required by apstra_datacenter_virtual_network.
# Given a list of switch node IDs, it determines whether they're leaf or access nodes, replaces individual switch IDs with ESI or MLAG redundancy group IDs, finds required parent leaf switches of all access switches.
data "apstra_datacenter_virtual_network_binding_constructor" "vn_binding_constructors" {

  # local.flattened_vn_bindings is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and vn_binding vlan_id keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_vn_bindings) ? {
    for vn_binding in try(local.flattened_vn_bindings, []) : "${vn_binding.bp}.${vn_binding.vn}.${vn_binding.vlan_id}" => vn_binding
  } : null
  blueprint_id = local.blueprint_ids[each.value.bp]
  vlan_id      = try(each.value.vlan_id, null)
  switch_ids   = data.apstra_datacenter_systems.vn_bindings["${each.value.bp}.${each.value.vn}.${each.value.vlan_id}"].ids
}

# Configure Virtual Networks

resource "apstra_datacenter_virtual_network" "virtual_networks" {

  # local.flattened_vns is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and vn_name keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_vns) ? {
    for vn in try(local.flattened_vns, []) : "${vn.bp}.${vn.name}" => vn
  } : null
  blueprint_id                 = local.blueprint_ids[each.value.bp]
  name                         = each.value.name
  reserve_vlan                 = try(each.value.reserve_vlan, null)
  vni                          = try(each.value.vni, null)
  type                         = try(each.value.type, null)
  routing_zone_id              = local.vrf_ids["${each.value.bp}.${each.value.vrf}"]
  l3_mtu                       = try(each.value.l3_mtu, null)
  dhcp_service_enabled         = try(each.value.dhcp_service_enabled, null)
  ipv4_connectivity_enabled    = try(each.value.ipv4_connectivity_enabled, null)
  ipv4_subnet                  = try(each.value.ipv4_subnet, null)
  ipv4_virtual_gateway_enabled = try(each.value.ipv4_virtual_gateway_enabled, null)
  ipv4_virtual_gateway         = try(each.value.ipv4_virtual_gateway, null)
  ipv6_connectivity_enabled    = try(each.value.ipv6_connectivity_enabled, null)
  ipv6_subnet                  = try(each.value.ipv6_subnet, null)
  ipv6_virtual_gateway_enabled = try(each.value.ipv6_virtual_gateway_enabled, null)
  ipv6_virtual_gateway         = try(each.value.ipv6_virtual_gateway, null)
  export_route_targets = try(each.value.export_route_targets, null)
  import_route_targets = try(each.value.import_route_targets, null)
  bindings = data.apstra_datacenter_virtual_network_binding_constructor.vn_binding_constructors["${each.value.bp}.${each.value.name}.${each.value.bindings[0].vlan_id}"].bindings
}
