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

# ----- Configlet resources // Module: design


# Calculate SHA256 hash for each configlet individually
resource "terraform_data" "update_configlets_trigger" {
  for_each = can(local.configlets) ? {
    for configlet in try(local.configlets, []) : configlet.name => configlet
  } : {}

  input = filesha256("${var.configlets_path}/${each.value.generators[0].template_file}")
}

# Define the configlet resource with per-configlet lifecycle replacement
resource "apstra_configlet" "configlets" {
  for_each = can(local.configlets) ? {
    for configlet in try(local.configlets, []) : configlet.name => configlet
  } : {}
  lifecycle {
    # Replace only if the hash for this specific configlet changes
    replace_triggered_by = [
      terraform_data.update_configlets_trigger[each.key]
    ]
  }
  name = each.value.name
  generators = [
    for generator in each.value.generators : {
      config_style  = generator.config_style
      section       = generator.section
      template_text = file("${var.configlets_path}/${generator.template_file}")
    }
  ]
}