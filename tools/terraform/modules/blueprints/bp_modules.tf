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

# ----- Imported modules // Module: blueprints

# Global catalog modules (design, resources) must be imported into the blueprint module.
# All the necessary relative paths and filenames will be passed as arguments.

module "resources" {
  source             = "../resources"
  resources_path     = var.resources_path
  resources_filename = var.resources_filename
}

module "design" {
  source             = "../design"
  design_path        = var.design_path
  design_filename    = var.design_filename
  configlets_path    = var.configlets_path
}
