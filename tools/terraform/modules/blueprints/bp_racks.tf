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

# Configure the per-blueprint racks

resource "apstra_datacenter_rack" "racks" {
  # local.flattened_resources is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp, role and vrf keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_racks) ? {
    for rack in try(local.flattened_racks, null) : "${rack.bp}.${rack.name}" => rack
  } : null
  blueprint_id                = local.blueprint_ids[each.value.bp]
  name                        = each.value.name
  rack_type_id                = local.rack_ids["${each.value.rack_type}"]
  rack_elements_name_one_shot = true
}

# Delete the placeholder rack instantiated from the template

resource "terraform_data" "delete_placeholder_racks" {
  count = local.blueprint_list != null ? 1 : 0
  depends_on = [
    apstra_datacenter_rack.racks,
  ]
  provisioner "local-exec" {
    command = "python3 ../python/apstra_delete_placeholder_racks.py"
  }

}