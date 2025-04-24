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

# ----- Output variables // Module: design

# Mapping of each LD with its corresponding ID to be utilized in the blueprint module
output "logical_devices" {
  description = "Mapping of each LD with its corresponding ID"
  value       = data.apstra_logical_device.logical_devices
}

# Mapping of each IM with its corresponding ID to be utilized in the blueprint module
output "interface_maps" {
  description = "Mapping of each IM with its corresponding ID"
  value       = data.apstra_interface_map.interface_maps
}

# Mapping of each template name with its corresponding ID to be utilized in the blueprint module
output "rack_templates" {
  description = "Mapping of each rack template with its corresponding ID"
  value       = apstra_template_rack_based.templates
}

# Mapping of each rack type with its corresponding ID to be instantiated in the blueprint module
output "racks" {
  description = "Mapping of each rack type with its corresponding"
  value       = apstra_rack_type.racks
}

# Mapping of each configlet name with its corresponding ID to be utilized in the blueprint module
output "configlets" {
  description = "Mapping of each configlet with its corresponding ID"
  value       = apstra_configlet.configlets
}

# Mapping of each property set name with its corresponding ID and keys to be utilized in the blueprint module
output "property_sets" {
  description = "Mapping of each property set with its corresponding ID and keys"
  value       = apstra_property_set.property_sets
}
