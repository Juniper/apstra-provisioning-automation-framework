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

# ----- Imported modules // Root module

# Only the blueprint module must be imported into this root module, as the global catalog modules (design, resources) must be imported into the blueprint module.
# All the necessary relative paths and filenames will be passed as arguments.

module "blueprints" {
  source              = "./modules/blueprints"
  resources_path      = local.resources_path
  resources_filename  = local.resources_filename
  design_path         = local.design_path
  design_filename     = local.design_filename
  blueprints_path     = local.blueprints_path
  blueprints_filename = local.blueprints_filename
  configlets_path     = local.configlets_path
  parent_project_outputs = data.terraform_remote_state.remote_customer
}
