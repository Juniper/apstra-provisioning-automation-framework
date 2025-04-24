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

# ----- Local variables // Module: design

locals {

  # YAML files decoded and made into terraform maps and lists
  logical_devices = try(yamldecode(file("${var.design_path}/${var.design_filename}"))["logical_devices"], {})
  interface_maps  = try(yamldecode(file("${var.design_path}/${var.design_filename}"))["interface_maps"], {})
  racks           = try(yamldecode(file("${var.design_path}/${var.design_filename}"))["racks"], [])
  templates       = try(yamldecode(file("${var.design_path}/${var.design_filename}"))["templates"], [])
  configlets      = try(yamldecode(file("${var.design_path}/${var.design_filename}"))["configlets"], [])
  property_sets   = try(yamldecode(file("${var.design_path}/${var.design_filename}"))["property_sets"], [])

  # Mapping of each rack name with its corresponding ID
  rack_ids = {
    for rack_name, rack_data in try(apstra_rack_type.racks, {}) :
    rack_name => rack_data.id
  }

  # Lists of unique values of tag names across all the devices
  leaf_tags = distinct(flatten([
    for rack in try(local.racks, []) : [
      for leaf_switch in try(rack.leaf_switches, []) :
      try(leaf_switch.tags, [])
    ]
  ]))

  generic_system_tags = distinct(flatten([
    for rack in try(local.racks, []) : [
      for generic_system in try(rack.generic_systems, []) :
      try(generic_system.tags, [])
    ]
  ]))

  access_switch_tags = distinct(flatten([
    for rack in try(local.racks, []) : [
      for access_switch in try(rack.access_switches, []) :
      try(access_switch.tags, [])
    ]
  ]))

  generic_system_link_tags = distinct(flatten([
    for rack in try(local.racks, []) : [
      for generic_system in try(rack.generic_systems, []) : [
        for link in try(generic_system.links, []) :
        try(link.tags, [])
      ]
    ]
  ]))

  access_switch_link_tags = distinct(flatten([
    for rack in try(local.racks, []) : [
      for access_switch in try(rack.access_switches, []) : [
        for link in try(access_switch.links, []) :
        try(link.tags, [])
      ]
    ]
  ]))

  all_tags = distinct(concat(
    try(local.leaf_tags, []),
    try(local.generic_system_tags, []),
    try(local.access_switch_tags, []),
    try(local.generic_system_link_tags, []),
    try(local.access_switch_link_tags, []),
  ))

  logical_device_names = distinct(concat(
    try(local.logical_devices.pre_existing, []),
    try([for logical_device in local.logical_devices.user_defined : logical_device.name], [])
  ))

  interface_map_names = distinct(concat(
    try(local.interface_maps.pre_existing, []),
    try([for interface_map in local.interface_maps.user_defined : interface_map.name], [])
  ))

}

