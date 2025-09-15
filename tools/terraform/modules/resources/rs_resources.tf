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

# ----- Resources // Module: resources

# ASN resource pools
resource "apstra_asn_pool" "apstra_asn_pool" {
  for_each = {
    for asn_pool in try(local.resources.asn_pools, []) : asn_pool.name => asn_pool
  }
  name   = each.value.name
  ranges = each.value.ranges
}


# VNI resource pools
resource "apstra_vni_pool" "apstra_vni_pool" {
  for_each = {
    for vni_pool in try(local.resources.vni_pools, []) : vni_pool.name => vni_pool
  }
  name   = each.value.name
  ranges = each.value.ranges
}

# IPv4 resource pools
resource "apstra_ipv4_pool" "apstra_ipv4_pool" {
  for_each = {
    for ipv4_pool in try(local.resources.ipv4_pools, []) : ipv4_pool.name => ipv4_pool
  }
  name    = each.value.name
  subnets = each.value.subnets
}

# IPv6 resource pools
resource "apstra_ipv6_pool" "apstra_ipv6_pool" {
  for_each = {
    for ipv6_pool in try(local.resources.ipv6_pools, []) : ipv6_pool.name => ipv6_pool
  }
  name    = each.value.name
  subnets = each.value.subnets
}