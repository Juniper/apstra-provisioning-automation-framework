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

# ----- Local variables // Root module
locals {

  # Filenames and relative paths
  data_path = "../../data"

  scope = yamldecode(file("${local.data_path}/scope/scope.yml"))

  customer   = try(local.scope.customer, "")
  domain     = try(local.scope.domain, "")
  project    = try(local.scope.project, "")
  aos_target = try(local.scope.aos_target, "")

  customer_path = "${local.data_path}/customers/${local.customer}"
  domain_path   = "${local.customer_path}/domains/${local.domain}"
  project_path  = "${local.domain_path}/projects/${local.project}"

  files = yamldecode(file("${local.project_path}/input/_main/files.yml"))

  credentials_path     = "${local.domain_path}/${local.files.credentials.directory}"
  credentials_filename = local.files.credentials.filename

  # AOS login data obtained by extracting the details of the target AOS 
  # from the YAML file containing the data for all potential AOS targets.
  aos_list = yamldecode(file("${local.credentials_path}/${local.credentials_filename}"))["aos"]
  aos_login = try(
    [for aos in local.aos_list : aos if aos.target == local.aos_target][0],
    {}
  )

  parent_projects_path     = try("${local.project_path}/input/${local.files.parent_projects.directory}", "")
  parent_projects_filename = try(local.files.parent_projects.filename, "")

  resources_path     = "${local.project_path}/input/${local.files.resources.directory}"
  resources_filename = local.files.resources.filename

  design_path     = "${local.project_path}/input/${local.files.design.directory}"
  design_filename = local.files.design.filename

  blueprints_path     = "${local.project_path}/input/${local.files.blueprints.directory}"
  blueprints_filename = local.files.blueprints.filename

  configlets_path    = "${local.design_path}/${local.files.configlets.directory}"

  # Parent Projects YAML file decoded and made into a terraform map
  parent_projects = try(yamldecode(file("${local.parent_projects_path}/${local.parent_projects_filename}"))["parent_projects"], null)

}
