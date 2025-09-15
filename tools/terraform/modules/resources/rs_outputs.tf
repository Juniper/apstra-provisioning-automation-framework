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

# ----- Output variables // Module: resources

# Mapping of each resource name with its corresponding ID to be utilized in the blueprint module

output "asn_pool_resources" {
  description = "Mapping of each ASN pool with its corresponding ID"
  value       = apstra_asn_pool.apstra_asn_pool
}
output "vni_pool_resources" {
  description = "Mapping of each VNI pool with its corresponding ID"
  value       = apstra_vni_pool.apstra_vni_pool
}
output "ipv4_pool_resources" {
  description = "Mapping of each IPv4 pool with its corresponding ID"
  value       = apstra_ipv4_pool.apstra_ipv4_pool
}
output "ipv6_pool_resources" {
  description = "Mapping of each IPv6 pool with its corresponding ID"
  value       = apstra_ipv6_pool.apstra_ipv6_pool
}
