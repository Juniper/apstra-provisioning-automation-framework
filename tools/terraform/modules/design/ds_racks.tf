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

# ----- Rack resources // Module: design

# Create all tags assigned in the design block
resource "apstra_tag" "apstra_tags" {
  for_each = toset(local.all_tags)
  name     = each.key
}

# Create all racks

resource "apstra_rack_type" "racks" {
  for_each = {
    for rack in try(local.racks, []) : rack.name => rack
  }
  name                       = each.value.name
  fabric_connectivity_design = each.value.fabric_connectivity_design
  description                = try(each.value.description, null)

  leaf_switches = {
    for leaf_switch in try(each.value.leaf_switches, []) :
    leaf_switch.name => {
      logical_device_id   = data.apstra_logical_device.logical_devices[leaf_switch.logical_device].id
      spine_link_count    = try(leaf_switch.spine_link_count, null)
      spine_link_speed    = try(leaf_switch.spine_link_speed, null)
      redundancy_protocol = try(leaf_switch.redundancy_protocol, null)
      tag_ids = can(leaf_switch.tags) ? [
        for tag_name in leaf_switch.tags :
        apstra_tag.apstra_tags[tag_name].id
      ] : null
    }
  }

  generic_systems = can(each.value.generic_systems) ? {
    for generic_system in try(each.value.generic_systems, []) :
    generic_system.name => {
      logical_device_id   = data.apstra_logical_device.logical_devices[generic_system.logical_device].id
      count               = try(generic_system.count, 0)
      port_channel_id_max = try(generic_system.port_channel_id_max, 0)
      port_channel_id_min = try(generic_system.port_channel_id_min, 0)
      tag_ids = can(generic_system.tags) ? [
        for tag_name in generic_system.tags :
        apstra_tag.apstra_tags[tag_name].id
      ] : null
      links = can(generic_system.links) ? {
        for link in try(generic_system.links, []) :
        link.name => {
          target_switch_name = link.target_switch_name
          speed              = link.speed
          lag_mode           = try(link.lag_mode, null)
          links_per_switch   = try(link.links_per_switch, null)
          switch_peer        = try(link.switch_peer, null)
          tag_ids = can(link.tags) ? [
            for tag_name in link.tags :
            apstra_tag.apstra_tags[tag_name].id
          ] : null
        }
      } : null
    }
  } : null

  access_switches = can(each.value.access_switches) ? {
    for access_switch in try(each.value.access_switches, []) :
    access_switch.name => {
      logical_device_id = data.apstra_logical_device.logical_devices[access_switch.logical_device].id
      count             = try(access_switch.count, 1)
      esi_lag_info      = try(access_switch.esi_lag_info, null)
      tag_ids = can(access_switch.tags) ? [
        for tag_name in access_switch.tags :
        apstra_tag.apstra_tags[tag_name].id
      ] : null
      links = can(access_switch.links) ? {
        for link in try(access_switch.links, []) :
        link.name => {
          target_switch_name = link.target_switch_initial_name
          speed              = link.speed
          lag_mode           = try(link.lag_mode, null)
          links_per_switch   = try(link.links_per_switch, null)
          switch_peer        = try(link.switch_peer, null)
          tag_ids = can(link.tags) ? [
            for tag_name in link.tags :
            apstra_tag.apstra_tags[tag_name].id
          ] : null
        }
      } : null
    }
  } : null

}
