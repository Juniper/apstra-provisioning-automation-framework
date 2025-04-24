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

terraform {
  backend "local" {
  }

  required_providers {
    apstra = {
      source = "Juniper/apstra"
      version = "0.85.1"
    }
  }
}

data "terraform_remote_state" "remote_customer" {
  for_each = local.parent_projects != null ? toset(local.parent_projects) : toset([])
  backend  = "local"
  config = {
    path = "${local.domain_path}/projects/${each.value}/output/executions/execution_0/tfstate/${each.value}.tfstate"

  }
}

# # Option 1: Either hard-coding the data or based on environment variables

# provider "apstra" {
#   url = "https://user:password@apstraurl"
#   tls_validation_disabled = true
#   blueprint_mutex_enabled = false
#   experimental            = true # bypassing version compatibility checks in the SDK (necessary for AOS 4.2.0)
# }


# # Option 2: Using Terraform variables (defined in variables.tf as Sensitive and values assigned in secret.tfvars)
# # terraform plan -var-file="secret.tfvars"
# # Comment/uncomment lines in output.tf as required
# # Uncomment secret variables in variables.tf

# provider "apstra" {
#   url                     = "https://${var.aos_username}:${var.aos_password}@${var.aos_ip}"
#   tls_validation_disabled = true
#   blueprint_mutex_enabled = false
#   experimental            = true # bypassing version compatibility checks in the SDK (necessary for AOS 4.2.0)
# }


# Option 3: Using YAML variables
# This file decodes the yaml file and makes it into a terraform map
# # terraform plan
# Comment/uncomment lines in output.tf as required
# Comment secret variables in variables.tf

provider "apstra" {
  url                     = "https://${local.aos_login.username}:${local.aos_login.encoded_password}@${local.aos_login.ip}"
  tls_validation_disabled = true
  blueprint_mutex_enabled = false
  experimental            = true # bypassing version compatibility checks in the SDK (necessary for AOS 4.2.0)
  api_timeout             = 0
}


