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

# output "template_ids" {
#   value = local.template_ids
# }

# Instantiate the blueprints from the global catalog templates
resource "apstra_datacenter_blueprint" "blueprints" {
  for_each                        = can(local.blueprints_to_create) ? try(local.blueprints_to_create, {}) : null
  name                            = each.key
  template_id                     = local.template_ids[each.value.template]
  ipv6_applications               = try(each.value.ipv6, null)
  esi_mac_msb                     = try(each.value.esi_mac_msb, null)
  fabric_mtu                      = try(each.value.fabric_mtu, null)
  default_svi_l3_mtu              = try(each.value.default_svi_l3_mtu, null)
  default_ip_links_to_generic_mtu = try(each.value.default_ip_links_to_generic_mtu, null)
  evpn_type_5_routes              = try(each.value.evpn_type_5_routes, null)
  optimize_routing_zone_footprint = try(each.value.optimize_routing_zone_footprint, null)
  max_evpn_routes_count           = try(each.value.max_evpn_routes_count, null)
  max_external_routes_count       = try(each.value.max_external_routes_count, null)
  max_fabric_routes_count         = try(each.value.max_fabric_routes_count, null)
  max_mlag_routes_count           = try(each.value.max_mlag_routes_count, null)
}

# Assign resource pool maps from the global catalog to the applicable roles
resource "apstra_datacenter_resource_pool_allocation" "resources" {
  # local.flattened_resources is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp, role and vrf keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_resources) ? {
    for resource in try(local.flattened_resources, []) : "${resource.bp}.${resource.role}.${resource.vrf}" => resource
  } : null
  blueprint_id    = local.blueprint_ids[each.value.bp]
  role            = each.value.role
  pool_ids        = [local.resource_pool_ids[each.value.resource_pool]]
  routing_zone_id = each.value.vrf != "n/a" ? local.vrf_ids["${each.value.bp}.${each.value.vrf}"] : null
}

# Assign interface map and system IDs
resource "apstra_datacenter_device_allocation" "devices" {

  depends_on = [
    apstra_datacenter_rack.racks,
    terraform_data.delete_placeholder_racks,
  ]

  for_each = can(local.switches_to_bp_allocation) ? {
    for device in try(local.switches_to_bp_allocation, []) : "${device.bp}.${device.initial_device_name}" => device
  } : null
  blueprint_id             = local.blueprint_ids[each.value.bp]
  node_name                = each.value.initial_device_name
  initial_interface_map_id = try(local.interface_map_ids[each.value.initial_interface_map], null)
  device_key = try(each.value.device_key, null)
  system_attributes = try({
    name          = try(each.value.blueprint_device_name, null)
    hostname      = try(each.value.blueprint_device_name, null)
    asn           = try(each.value.asn, null)
    deploy_mode   = try(each.value.deploy_mode, null)
    loopback_ipv4 = try(each.value.loopback_ipv4, null)
    loopback_ipv6 = try(each.value.loopback_ipv6, null)
    tags          = try(each.value.tags, null)
  }, null)
}