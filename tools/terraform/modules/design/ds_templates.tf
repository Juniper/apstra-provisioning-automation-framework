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

# ----- Template resources // Module: design

resource "apstra_template_rack_based" "templates" {
  for_each = can(local.templates) ? {
    for template in local.templates : template.name => template
    if(can(local.templates))
  } : null
  name                     = each.value.name
  asn_allocation_scheme    = each.value.asn_allocation_scheme
  overlay_control_protocol = each.value.overlay_control_protocol
  spine = {
    count             = each.value.spine.count
    logical_device_id = data.apstra_logical_device.logical_devices[each.value.spine.logical_device].id
  }
  rack_infos = {
    for rack in try(each.value.racks, []) :
    local.rack_ids[rack.name] => {
      count = rack.count
    }
  }
}
