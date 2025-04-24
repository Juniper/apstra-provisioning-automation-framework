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

# ----- Cabling Map Resources // Module: blueprints

# Update the cabling maps to set the correct Generic System and Switches port names and IPs

resource "terraform_data" "update_cabling_maps_trigger" {
  count = local.blueprint_list != null ? 1 : 0
  input = concat(
    local.flattened_generic_systems,
    local.flattened_spines
  )
}
resource "terraform_data" "update_cabling_maps" {
  count = local.blueprint_list != null ? 1 : 0
  lifecycle {
    replace_triggered_by = [
      terraform_data.update_cabling_maps_trigger
    ]
  }
  depends_on = [
    apstra_datacenter_generic_system.generic_systems,
  ]

  provisioner "local-exec" {
    command = "python3 ../python/apstra_update_cabling_maps.py pull_cabling_maps push_cabling_maps"
  }
}
