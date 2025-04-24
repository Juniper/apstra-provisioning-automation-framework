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

# ----- Logical Devices // Module: design

# Create the required logical devices

resource "apstra_logical_device" "logical_devices" {

  for_each = can(local.logical_devices) ? can(local.logical_devices.user_defined) ? {
    for logical_device in local.logical_devices.user_defined : logical_device.name => logical_device
  } : {} : {}

  name   = each.value.name
  panels = each.value.panels
}

# These data variables provide mappings of meaningful names for the devices potentially included in the rack resources, along with their corresponding logical devices ids.

data "apstra_logical_device" "logical_devices" {
  # Dependency established next so that the list of LDs is not retrieved until the resource in charge of creating the new LDs has finished
  depends_on = [
    apstra_logical_device.logical_devices,
  ]
  for_each = can(local.logical_device_names) ? toset(local.logical_device_names) : toset([])
  name     = each.value
}
