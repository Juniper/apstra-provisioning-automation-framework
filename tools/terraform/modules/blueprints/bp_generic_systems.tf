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

# Configure Generic Systems
resource "apstra_datacenter_generic_system" "generic_systems" {

  depends_on = [
    apstra_datacenter_device_allocation.devices,
  ]

  # local.flattened_generic_systems is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and name keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_generic_systems) ? {
    for generic_system in try(local.flattened_generic_systems, []) : "${generic_system.bp}.${generic_system.name}" => generic_system
  } : null
  blueprint_id        = local.blueprint_ids[each.value.bp]
  name                = try(each.value.name, null)
  hostname            = try(each.value.hostname, null)
  tags                = try(each.value.tags, null)
  external            = try(each.value.external, null)
  deploy_mode         = try(each.value.deploy_mode, null)
  asn                 = try(each.value.asn, null)
  loopback_ipv4       = try(each.value.loopback_ipv4, null)
  loopback_ipv6       = try(each.value.loopback_ipv6, null)
  port_channel_id_min = try(each.value.port_channel_id_min, null)
  port_channel_id_max = try(each.value.port_channel_id_max, null)
  links = [
    for link_data in try(each.value.links, []) :
    {
      # target_switch_id              = "trDVmvFuj-9eltsI7g"
      target_switch_id              = local.bp_switch_ids["${local.blueprint_ids[each.value.bp]}.${link_data.target_switch_hostname}"]
      target_switch_if_name         = link_data.target_switch_if_name
      target_switch_if_transform_id = link_data.target_switch_if_transform_id
      group_label                   = try(link_data.group_label, null)
      lag_mode                      = try(link_data.lag_mode, null)
      tags                          = try(link_data.tags, null)
    }
  ]
}


