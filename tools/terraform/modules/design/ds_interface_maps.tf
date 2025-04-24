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

# ----- Interface Maps // Module: design

# Create the required interface maps

# Two resources created to this end, each representing a distinct approach to convey the "interfaces" attribute:
#   - interface_mappings: an ordered list providing interface mapping information.
#   - interface_mapping_ranges: iterates over a list's elements to construct a detailed mapping between logical and physical ports based on mapping ranges.

resource "apstra_interface_map" "interface_maps_with_individual_bindings" {
  # for_each = can(local.interface_maps.user_defined) ? {
  for_each = can(local.interface_maps.user_defined) ? can(local.interface_maps.user_defined) ? {
    for interface_map in local.interface_maps.user_defined : interface_map.name => interface_map
    if(can(interface_map.interface_mappings) && !can(interface_map.interface_mapping_ranges))
  } : {} : {}
  name              = each.value.name
  logical_device_id = data.apstra_logical_device.logical_devices[each.value.logical_device].id
  device_profile_id = each.value.device_profile_id
  interfaces        = each.value.interface_mappings
}

resource "apstra_interface_map" "interface_maps_using_loops" {
  # for_each = can(local.interface_maps.user_defined) ? {
  for_each = can(local.interface_maps.user_defined) ? can(local.interface_maps.user_defined) ? {
    for interface_map in local.interface_maps.user_defined : interface_map.name => interface_map
    if(!can(interface_map.interface_mappings) && can(interface_map.interface_mapping_ranges))
  } : {} : {}
  name              = each.value.name
  logical_device_id = data.apstra_logical_device.logical_devices[each.value.logical_device].id
  device_profile_id = each.value.device_profile_id
  interfaces = flatten([
    for map in each.value.interface_mapping_ranges : [
      for i in range(map.count) : {
        logical_device_port     = format("%d/%d", map.ld_panel, map.ld_first_port + i)
        physical_interface_name = map.channelized ? format("%s%d%s%d", map.phy_prefix, map.phy_first_port + floor(i / map.channel_count), map.channel_prefix, map.channel_first_port + i % map.channel_count) : format("%s%d", map.phy_prefix, map.phy_first_port + i)
        # physical_interface_name = map.channelized == "True" ? format("%s%d%s%d", map.phy_prefix, map.phy_first_port + floor(i / 4), ":", 0 + i % 4) : format("%s%d", map.phy_prefix, map.phy_first_port + i)
        transformation_id = try(map.transformation_id, null)
      }
    ]
  ])
}

# These data variables provide mappings of meaningful names for the devices potentially included in the rack resources, along with their corresponding interface map ids.

data "apstra_interface_map" "interface_maps" {
  # Dependency established next so that the list of IMs is not retrieved until the resources in charge of creating the new IMs have finished
  depends_on = [
    apstra_interface_map.interface_maps_with_individual_bindings,
    apstra_interface_map.interface_maps_using_loops
  ]
  for_each = can(local.interface_map_names) ? toset(local.interface_map_names) : toset([])
  name     = each.value
}
