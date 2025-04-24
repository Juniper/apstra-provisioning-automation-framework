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

resource "apstra_datacenter_connectivity_template_interface" "ct_interface" {
  # local.flattened_connectivity_templates is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and the ct keys to
  # produce a single unique key per instance.

  for_each = {
    for ct in local.flattened_connectivity_templates : "${ct.bp}.${ct.name}" => ct
  }
  blueprint_id = local.blueprint_ids[each.value.bp]
  name         = try(each.value.name, null)
  description  = try(each.value.description, null)
  tags         = try(each.value.tags, null)


  virtual_network_singles = length([
    for prim in [
      for primitive in try(local.flattened_primitives, []) :
      can(primitive.type) && primitive.type == "virtual_network_single" &&
      primitive.is_a_root_primitive == true && primitive.bp == each.value.bp && primitive.ct == each.value.name ?
      {
        name               = try(primitive.name, null)
        tagged             = try(primitive.data.tagged, false)
        virtual_network_id = try(local.vn_ids["${primitive.bp}.${primitive.data.vn}"], null)

        static_routes = length([
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name              = try(child_primitive.name, null)
              share_ip_endpoint = try(child_primitive.data.share_ip_endpoint, false)
              network           = try(child_primitive.data.network, null)
            } : null
            if child_primitive.type == "static_route" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
          child_prim if child_prim != null
          ]) > 0 ? {
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name              = try(child_primitive.name, null)
              share_ip_endpoint = try(child_primitive.data.share_ip_endpoint, false)
              network           = try(child_primitive.data.network, null)
            } : null
            if child_primitive.type == "static_route" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
        try(child_prim.name) => {
          share_ip_endpoint = try(child_prim.share_ip_endpoint, null)
          network = try(child_prim.network, null)
        } if child_prim != null
        } : null

        bgp_peering_generic_systems = length([
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name                 = try(child_primitive.name, null)
              ttl                  = try(child_primitive.data.ttl, null)
              bfd_enabled          = try(child_primitive.data.bfd_enabled, false)
              password             = try(child_primitive.data.password, null)
              keepalive_time       = try(child_primitive.data.keepalive_time, null)
              hold_time            = try(child_primitive.data.hold_time, null)
              ipv4_addressing_type = try(child_primitive.data.ipv4_addressing_type, "none")
              ipv6_addressing_type = try(child_primitive.data.ipv6_addressing_type, "none")
              local_asn            = try(child_primitive.data.local_asn, null)
              neighbor_asn_dynamic = try(child_primitive.data.neighbor_asn_dynamic, false)
              peer_from_loopback   = try(child_primitive.data.peer_from_loopback, false)
              peer_to              = try(child_primitive.data.peer_to, "interface_or_ip_endpoint")
            } : null
            if child_primitive.type == "bgp_peering_generic_system" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
          child_prim if child_prim != null
          ]) > 0 ? {
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name                 = try(child_primitive.name, null)
              ttl                  = try(child_primitive.data.ttl, null)
              bfd_enabled          = try(child_primitive.data.bfd_enabled, false)
              password             = try(child_primitive.data.password, null)
              keepalive_time       = try(child_primitive.data.keepalive_time, null)
              hold_time            = try(child_primitive.data.hold_time, null)
              ipv4_addressing_type = try(child_primitive.data.ipv4_addressing_type, "none")
              ipv6_addressing_type = try(child_primitive.data.ipv6_addressing_type, "none")
              local_asn            = try(child_primitive.data.local_asn, null)
              neighbor_asn_dynamic = try(child_primitive.data.neighbor_asn_dynamic, false)
              peer_from_loopback   = try(child_primitive.data.peer_from_loopback, false)
              peer_to              = try(child_primitive.data.peer_to, "interface_or_ip_endpoint")
              routing_policies = length([
                for grand_child_prim in [
                  for grand_child_primitive in try(local.flattened_primitives, []) :
                  try(contains(try(child_primitive.data.child_primitives, []), grand_child_primitive.name), false) ?
                  {
                    name              = try(grand_child_primitive.name, null)
                    routing_policy_id = try(local.routing_policy_ids["${grand_child_primitive.bp}.${grand_child_primitive.data.routing_policy}"], null)
                  } : null
                  if grand_child_primitive.type == "routing_policy" && grand_child_primitive.is_a_root_primitive == false && grand_child_primitive.bp == primitive.bp && grand_child_primitive.ct == primitive.ct
                ] :
                grand_child_prim if grand_child_prim != null
                ]) > 0 ? {
                for grand_child_prim in [
                  for grand_child_primitive in try(local.flattened_primitives, []) :
                  try(contains(try(child_primitive.data.child_primitives, []), grand_child_primitive.name), false) ?
                  {
                    name              = try(grand_child_primitive.name, null)
                    routing_policy_id = try(local.routing_policy_ids["${grand_child_primitive.bp}.${grand_child_primitive.data.routing_policy}"], null)
                  } : null
                  if grand_child_primitive.type == "routing_policy" && grand_child_primitive.is_a_root_primitive == false && grand_child_primitive.bp == primitive.bp && grand_child_primitive.ct == primitive.ct
                ] :
              try(grand_child_prim.name) => {
                routing_policy_id = try(grand_child_prim.routing_policy_id, null)
              } if grand_child_prim != null
              } : null
            } : null
            if child_primitive.type == "bgp_peering_generic_system" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
        try(child_prim.name) => {
          ttl                  = try(child_prim.ttl, null)
          bfd_enabled          = try(child_prim.bfd_enabled, false)
          password             = try(child_prim.password, null)
          keepalive_time       = try(child_prim.keepalive_time, null)
          hold_time            = try(child_prim.hold_time, null)
          ipv4_addressing_type = try(child_prim.ipv4_addressing_type, "none")
          ipv6_addressing_type = try(child_prim.ipv6_addressing_type, "none")
          local_asn            = try(child_prim.local_asn, null)
          neighbor_asn_dynamic = try(child_prim.neighbor_asn_dynamic, false)
          peer_from_loopback   = try(child_prim.peer_from_loopback, false)
          peer_to              = try(child_prim.peer_to, "interface_or_ip_endpoint")
          routing_policies              = try(child_prim.routing_policies, "interface_or_ip_endpoint")
        } if child_prim != null
        } : null

      } : null
    ] :
    prim if prim != null
    ]) > 0 ? {
    for prim in [
      for primitive in try(local.flattened_primitives, []) :
      can(primitive.type) && primitive.type == "virtual_network_single" &&
      primitive.is_a_root_primitive == true && primitive.bp == each.value.bp && primitive.ct == each.value.name ?
      {
        name               = try(primitive.name, null)
        tagged             = try(primitive.data.tagged, false)
        virtual_network_id = try(local.vn_ids["${primitive.bp}.${primitive.data.vn}"], null)
      } : null
    ] :
    try(prim.name) => {
      tagged             = try(prim.tagged, null)
      virtual_network_id = try(prim.virtual_network_id, null)
    } if prim != null
    } : null

  virtual_network_multiples = length([
    for prim in [
      for primitive in try(local.flattened_primitives, []) :
      can(primitive.type) && primitive.type == "virtual_network_multiple" &&
      primitive.is_a_root_primitive == true && primitive.bp == each.value.bp && primitive.ct == each.value.name ?
      {
        name = try(primitive.name, null)
        tagged_vn_ids = can(primitive.data.tagged_vn) ? [
          for vn in try(primitive.data.tagged_vn, []) :
          try(local.vn_ids["${primitive.bp}.${vn}"], null)
        ] : null
        untagged_vn_id = try(local.vn_ids["${primitive.bp}.${primitive.data.untagged_vn}"], null)
      } : null
    ] :
    prim if prim != null
    ]) > 0 ? {
    for prim in [
      for primitive in try(local.flattened_primitives, []) :
      can(primitive.type) && primitive.type == "virtual_network_multiple" &&
      primitive.is_a_root_primitive == true && primitive.bp == each.value.bp && primitive.ct == each.value.name ?
      {
        name = try(primitive.name, null)
        tagged_vn_ids = can(primitive.data.tagged_vn) ? [
          for vn in try(primitive.data.tagged_vn, []) :
          try(local.vn_ids["${primitive.bp}.${vn}"], null)
        ] : null
        untagged_vn_id = try(local.vn_ids["${primitive.bp}.${primitive.data.untagged_vn}"], null)
      } : null
    ] :
    try(prim.name) => {
      tagged_vn_ids = try(prim.tagged_vn_ids, null)
      untagged_vn_id = try(prim.untagged_vn_id, null)
    } if prim != null
    } : null

  ip_links = length([
    for prim in [
      for primitive in try(local.flattened_primitives, []) :
      can(primitive.type) && primitive.type == "ip_link" &&
      primitive.is_a_root_primitive == true && primitive.bp == each.value.bp && primitive.ct == each.value.name ?
      {
        name                 = try(primitive.name, null)
        routing_zone_id      = try(local.vrf_ids["${primitive.bp}.${primitive.data.vrf}"], null)
        vlan_id              = try(primitive.data.vlan_id, null)
        l3_mtu               = try(primitive.data.l3_mtu, null)
        ipv4_addressing_type = try(primitive.data.ipv4_addressing_type, "none")
        ipv6_addressing_type = try(primitive.data.ipv6_addressing_type, "none")
      } : null
    ] :
    prim if prim != null
    ]) > 0 ? {
    for prim in [
      for primitive in try(local.flattened_primitives, []) :
      can(primitive.type) && primitive.type == "ip_link" &&
      primitive.is_a_root_primitive == true && primitive.bp == each.value.bp && primitive.ct == each.value.name ?
      {
        name                 = try(primitive.name, null)
        routing_zone_id      = try(local.vrf_ids["${primitive.bp}.${primitive.data.vrf}"], null)
        vlan_id              = try(primitive.data.vlan_id, null)
        l3_mtu               = try(primitive.data.l3_mtu, null)
        ipv4_addressing_type = try(primitive.data.ipv4_addressing_type, "none")
        ipv6_addressing_type = try(primitive.data.ipv6_addressing_type, "none")

        bgp_peering_generic_systems = length([
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name                 = try(child_primitive.name, null)
              ttl                  = try(child_primitive.data.ttl, null)
              bfd_enabled          = try(child_primitive.data.bfd_enabled, false)
              password             = try(child_primitive.data.password, null)
              keepalive_time       = try(child_primitive.data.keepalive_time, null)
              hold_time            = try(child_primitive.data.hold_time, null)
              ipv4_addressing_type = try(child_primitive.data.ipv4_addressing_type, "none")
              ipv6_addressing_type = try(child_primitive.data.ipv6_addressing_type, "none")
              local_asn            = try(child_primitive.data.local_asn, null)
              neighbor_asn_dynamic = try(child_primitive.data.neighbor_asn_dynamic, false)
              peer_from_loopback   = try(child_primitive.data.peer_from_loopback, false)
              peer_to              = try(child_primitive.data.peer_to, "interface_or_ip_endpoint")
            } : null
            if child_primitive.type == "bgp_peering_generic_system" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
          child_prim if child_prim != null
          ]) > 0 ? {
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name                 = try(child_primitive.name, null)
              ttl                  = try(child_primitive.data.ttl, null)
              bfd_enabled          = try(child_primitive.data.bfd_enabled, false)
              password             = try(child_primitive.data.password, null)
              keepalive_time       = try(child_primitive.data.keepalive_time, null)
              hold_time            = try(child_primitive.data.hold_time, null)
              ipv4_addressing_type = try(child_primitive.data.ipv4_addressing_type, "none")
              ipv6_addressing_type = try(child_primitive.data.ipv6_addressing_type, "none")
              local_asn            = try(child_primitive.data.local_asn, null)
              neighbor_asn_dynamic = try(child_primitive.data.neighbor_asn_dynamic, false)
              peer_from_loopback   = try(child_primitive.data.peer_from_loopback, false)
              peer_to              = try(child_primitive.data.peer_to, "interface_or_ip_endpoint")
              routing_policies = length([
                for grand_child_prim in [
                  for grand_child_primitive in try(local.flattened_primitives, []) :
                  try(contains(try(child_primitive.data.child_primitives, []), grand_child_primitive.name), false) ?
                  {
                    name              = try(grand_child_primitive.name, null)
                    routing_policy_id = try(local.routing_policy_ids["${grand_child_primitive.bp}.${grand_child_primitive.data.routing_policy}"], null)
                  } : null
                  if grand_child_primitive.type == "routing_policy" && grand_child_primitive.is_a_root_primitive == false && grand_child_primitive.bp == primitive.bp && grand_child_primitive.ct == primitive.ct
                ] :
                grand_child_prim if grand_child_prim != null
                ]) > 0 ? {
                for grand_child_prim in [
                  for grand_child_primitive in try(local.flattened_primitives, []) :
                  try(contains(try(child_primitive.data.child_primitives, []), grand_child_primitive.name), false) ?
                  {
                    name              = try(grand_child_primitive.name, null)
                    routing_policy_id = try(local.routing_policy_ids["${grand_child_primitive.bp}.${grand_child_primitive.data.routing_policy}"], null)
                  } : null
                  if grand_child_primitive.type == "routing_policy" && grand_child_primitive.is_a_root_primitive == false && grand_child_primitive.bp == primitive.bp && grand_child_primitive.ct == primitive.ct
                ] :
              try(grand_child_prim.name) => {
                routing_policy_id = try(grand_child_prim.routing_policy_id, null)
              } if grand_child_prim != null
              } : null
            } : null
            if child_primitive.type == "bgp_peering_generic_system" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
        try(child_prim.name) => {
          ttl                  = try(child_prim.ttl, null)
          bfd_enabled          = try(child_prim.bfd_enabled, false)
          password             = try(child_prim.password, null)
          keepalive_time       = try(child_prim.keepalive_time, null)
          hold_time            = try(child_prim.hold_time, null)
          ipv4_addressing_type = try(child_prim.ipv4_addressing_type, "none")
          ipv6_addressing_type = try(child_prim.ipv6_addressing_type, "none")
          local_asn            = try(child_prim.local_asn, null)
          neighbor_asn_dynamic = try(child_prim.neighbor_asn_dynamic, false)
          peer_from_loopback   = try(child_prim.peer_from_loopback, false)
          peer_to              = try(child_prim.peer_to, "interface_or_ip_endpoint")
          routing_policies              = try(child_prim.routing_policies, "interface_or_ip_endpoint")
        } if child_prim != null
        } : null
    
        bgp_peering_ip_endpoints = length([
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name           = try(child_primitive.name, null)
              neighbor_asn   = try(child_primitive.data.neighbor_asn, null)
              ttl            = try(child_primitive.data.ttl, null)
              bfd_enabled    = try(child_primitive.data.bfd_enabled, false)
              password       = try(child_primitive.data.password, null)
              keepalive_time = try(child_primitive.data.keepalive_time, null)
              hold_time      = try(child_primitive.data.hold_time, null)
              local_asn      = try(child_primitive.data.local_asn, null)
              ipv4_address   = try(child_primitive.data.ipv4_address, null)
              ipv6_address   = try(child_primitive.data.ipv6_address, null)
            } : null
            if child_primitive.type == "bgp_peering_ip_endpoint" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
          child_prim if child_prim != null
          ]) > 0 ? {
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name           = try(child_primitive.name, null)
              neighbor_asn   = try(child_primitive.data.neighbor_asn, null)
              ttl            = try(child_primitive.data.ttl, null)
              bfd_enabled    = try(child_primitive.data.bfd_enabled, false)
              password       = try(child_primitive.data.password, null)
              keepalive_time = try(child_primitive.data.keepalive_time, null)
              hold_time      = try(child_primitive.data.hold_time, null)
              local_asn      = try(child_primitive.data.local_asn, null)
              ipv4_address   = try(child_primitive.data.ipv4_address, null)
              ipv6_address   = try(child_primitive.data.ipv6_address, null)
              routing_policies = length([
                for grand_child_prim in [
                  for grand_child_primitive in try(local.flattened_primitives, []) :
                  try(contains(try(child_primitive.data.child_primitives, []), grand_child_primitive.name), false) ?
                  {
                    name              = try(grand_child_primitive.name, null)
                    routing_policy_id = try(local.routing_policy_ids["${grand_child_primitive.bp}.${grand_child_primitive.data.routing_policy}"], null)
                  } : null
                  if grand_child_primitive.type == "routing_policy" && grand_child_primitive.is_a_root_primitive == false && grand_child_primitive.bp == primitive.bp && grand_child_primitive.ct == primitive.ct
                ] :
                grand_child_prim if grand_child_prim != null
                ]) > 0 ? {
                for grand_child_prim in [
                  for grand_child_primitive in try(local.flattened_primitives, []) :
                  try(contains(try(child_primitive.data.child_primitives, []), grand_child_primitive.name), false) ?
                  {
                    name              = try(grand_child_primitive.name, null)
                    routing_policy_id = try(local.routing_policy_ids["${grand_child_primitive.bp}.${grand_child_primitive.data.routing_policy}"], null)
                  } : null
                  if grand_child_primitive.type == "routing_policy" && grand_child_primitive.is_a_root_primitive == false && grand_child_primitive.bp == primitive.bp && grand_child_primitive.ct == primitive.ct
                ] :
              try(grand_child_prim.name) => {
                routing_policy_id = try(grand_child_prim.routing_policy_id, null)
              } if grand_child_prim != null
              } : null
            } : null
            if child_primitive.type == "bgp_peering_ip_endpoint" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
        try(child_prim.name) => {
          neighbor_asn   = try(child_prim.neighbor_asn, null)
          ttl            = try(child_prim.ttl, null)
          bfd_enabled    = try(child_prim.bfd_enabled, false)
          password       = try(child_prim.password, null)
          keepalive_time = try(child_prim.keepalive_time, null)
          hold_time      = try(child_prim.hold_time, null)
          local_asn      = try(child_prim.local_asn, null)
          ipv4_address   = try(child_prim.ipv4_address, null)
          ipv6_address   = try(child_prim.ipv6_address, null)
          routing_policies   = try(child_prim.routing_policies, null)
        } if child_prim != null
        } : null

        dynamic_bgp_peerings = length([
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name             = try(child_primitive.name, null)
              ttl              = try(child_primitive.data.ttl, null)
              bfd_enabled      = try(child_primitive.data.bfd_enabled, false)
              password         = try(child_primitive.data.password, null)
              keepalive_time   = try(child_primitive.data.keepalive_time, null)
              hold_time        = try(child_primitive.data.hold_time, null)
              ipv4_enabled     = try(child_primitive.data.ipv4_enabled, true)
              ipv6_enabled     = try(child_primitive.data.ipv6_enabled, false)
              local_asn        = try(child_primitive.data.local_asn, null)
              ipv4_peer_prefix = try(child_primitive.data.ipv4_peer_prefix, null)
              ipv6_peer_prefix = try(child_primitive.data.ipv6_peer_prefix, null)
            } : null
            if child_primitive.type == "dynamic_bgp_peering" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
          child_prim if child_prim != null
          ]) > 0 ? {
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name             = try(child_primitive.name, null)
              ttl              = try(child_primitive.data.ttl, null)
              bfd_enabled      = try(child_primitive.data.bfd_enabled, false)
              password         = try(child_primitive.data.password, null)
              keepalive_time   = try(child_primitive.data.keepalive_time, null)
              hold_time        = try(child_primitive.data.hold_time, null)
              ipv4_enabled     = try(child_primitive.data.ipv4_enabled, true)
              ipv6_enabled     = try(child_primitive.data.ipv6_enabled, false)
              local_asn        = try(child_primitive.data.local_asn, null)
              ipv4_peer_prefix = try(child_primitive.data.ipv4_peer_prefix, null)
              ipv6_peer_prefix = try(child_primitive.data.ipv6_peer_prefix, null)
              routing_policies = length([
                for grand_child_prim in [
                  for grand_child_primitive in try(local.flattened_primitives, []) :
                  try(contains(try(child_primitive.data.child_primitives, []), grand_child_primitive.name), false) ?
                  {
                    name              = try(grand_child_primitive.name, null)
                    routing_policy_id = try(local.routing_policy_ids["${grand_child_primitive.bp}.${grand_child_primitive.data.routing_policy}"], null)
                  } : null
                  if grand_child_primitive.type == "routing_policy" && grand_child_primitive.is_a_root_primitive == false && grand_child_primitive.bp == primitive.bp && grand_child_primitive.ct == primitive.ct
                ] :
                grand_child_prim if grand_child_prim != null
                ]) > 0 ? {
                for grand_child_prim in [
                  for grand_child_primitive in try(local.flattened_primitives, []) :
                  try(contains(try(child_primitive.data.child_primitives, []), grand_child_primitive.name), false) ?
                  {
                    name              = try(grand_child_primitive.name, null)
                    routing_policy_id = try(local.routing_policy_ids["${grand_child_primitive.bp}.${grand_child_primitive.data.routing_policy}"], null)
                  } : null
                  if grand_child_primitive.type == "routing_policy" && grand_child_primitive.is_a_root_primitive == false && grand_child_primitive.bp == primitive.bp && grand_child_primitive.ct == primitive.ct
                ] :
              try(grand_child_prim.name) => {
                routing_policy_id = try(grand_child_prim.routing_policy_id, null)
              } if grand_child_prim != null
              } : null
            } : null
            if child_primitive.type == "dynamic_bgp_peering" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
        try(child_prim.name) => {
          ttl            = try(child_prim.ttl, null)
          bfd_enabled    = try(child_prim.bfd_enabled, false)
          password       = try(child_prim.password, null)
          keepalive_time = try(child_prim.keepalive_time, null)
          hold_time      = try(child_prim.hold_time, null)
          ipv4_enabled   = try(child_prim.ipv4_enabled, null)
          ipv6_enabled   = try(child_prim.ipv6_enabled, null)
          local_asn      = try(child_prim.local_asn, null)
          ipv4_peer_prefix   = try(child_prim.ipv4_peer_prefix, null)
          ipv6_peer_prefix   = try(child_prim.ipv6_peer_prefix, null)
          routing_policies   = try(child_prim.routing_policies, null)
        } if child_prim != null
        } : null

        static_routes = length([
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name              = try(child_primitive.name, null)
              share_ip_endpoint = try(child_primitive.data.share_ip_endpoint, false)
              network           = try(child_primitive.data.network, null)
            } : null
            if child_primitive.type == "static_route" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
          child_prim if child_prim != null
          ]) > 0 ? {
          for child_prim in [
            for child_primitive in try(local.flattened_primitives, []) :
            try(contains(try(primitive.data.child_primitives, []), child_primitive.name), false) ?
            {
              name              = try(child_primitive.name, null)
              share_ip_endpoint = try(child_primitive.data.share_ip_endpoint, false)
              network           = try(child_primitive.data.network, null)
            } : null
            if child_primitive.type == "static_route" && child_primitive.is_a_root_primitive == false && child_primitive.bp == primitive.bp && child_primitive.ct == primitive.ct
          ] :
        try(child_prim.name) => {
          share_ip_endpoint = try(child_prim.share_ip_endpoint, null)
          network = try(child_prim.network, null)
        } if child_prim != null
        } : null

      } : null
    ] :
    try(prim.name) => {
      routing_zone_id      = try(prim.routing_zone_id, null)
      vlan_id              = try(prim.vlan_id, null)
      l3_mtu               = try(prim.l3_mtu, null)
      ipv4_addressing_type = try(prim.ipv4_addressing_type, null)
      ipv6_addressing_type = try(prim.ipv6_addressing_type, null)
      bgp_peering_generic_systems = try(prim.bgp_peering_generic_systems, null)
      bgp_peering_ip_endpoints = try(prim.bgp_peering_ip_endpoints, null)
      dynamic_bgp_peerings = try(prim.dynamic_bgp_peerings, null)
      static_routes = try(prim.static_routes, null)
    } if prim != null
  } : null
}


# Groups of interfaces sharing common link tags
data "apstra_datacenter_interfaces_by_link_tag" "interfaces_by_link_tag" {
  depends_on = [
    apstra_datacenter_generic_system.generic_systems,
    apstra_datacenter_connectivity_template_interface.ct_interface,
  ]
  # local.flattened_bindings_by_link_tag is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and ct keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_bindings_by_link_tag) ? {
    for binding in try(local.flattened_bindings_by_link_tag, []) : "${binding.bp}.${binding.ct}" => binding
  } : null
  blueprint_id = local.blueprint_ids[each.value.bp]
  system_type  = try(each.value.system_type, null)
  system_role  = try(each.value.system_role, null)
  tags         = each.value.tags
}


# Map of Apstra object IDs representing all Interfaces, keyed by Interface name (e.g., xe-0/0/0)
# The local variable "apstra_datacenter_interfaces_by_if_name" utilizes this map to identify the Interface IDs 
# associated with each Interface name specified in the "bindings_by_if_name" lists in each ct within the <bp>.yml data.
data "apstra_datacenter_interfaces_by_system" "interfaces_by_system" {
  depends_on = [
    apstra_datacenter_generic_system.generic_systems,
    apstra_datacenter_connectivity_template_interface.ct_interface,
  ]
  # local.flattened_bindings_by_if_name is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and ct keys to
  # produce a single unique key per instance.
  for_each = can(local.flattened_bindings_by_if_name) ? {
    for binding in try(local.flattened_bindings_by_if_name, []) : "${binding.bp}.${binding.ct}.${binding.initial_device_name}" => binding
  } : null
  blueprint_id = local.blueprint_ids[each.value.bp]
  system_id    = local.switch_ids["${apstra_datacenter_blueprint.blueprints[each.value.bp].id}.${each.value.initial_device_name}"]

}

# Groups of interfaces belonging to a common system identified by their port name
# This is a subset of the data from data "apstra_datacenter_interfaces_by_system" "interfaces_by_system" focused on assigned connectivity template endpoints.
# The resulting structure is formatted as a map with analogous keys to data "apstra_datacenter_interfaces_by_link_tag" named "interfaces_by_link_tag."

locals {
  apstra_datacenter_interfaces_by_if_name = try(
    zipmap(
      [for binding in try(local.flattened_bindings_by_if_name, []) : "${binding.bp}.${binding.ct}.${binding.initial_device_name}"],
      [for binding in try(local.flattened_bindings_by_if_name, []) : {
        blueprint_id = local.blueprint_ids[binding.bp]
        ids = toset(flatten([
          for int in binding.interfaces :
          data.apstra_datacenter_interfaces_by_system.interfaces_by_system["${binding.bp}.${binding.ct}.${binding.initial_device_name}"]["if_map"]["${int}"]
          ]
        ))
      }]
    ),
    null
  )
}


# Connectivity Template assignment

resource "apstra_datacenter_connectivity_template_assignments" "connectivity_template_assignments" {
  # local.flattened_connectivity_templates is a list, so we must now project it into a map
  # where each key is unique. We'll combine the bp and the ct keys to
  # produce a single unique key per instance.
  # We will iterate only over those CTs that have the 'bindings' attribute.
  # When bindings are based on tags, it will only iterate over those CTs which set of tags are assigned to at least one link of one of the generic systems.
  for_each = {
    for ct in local.flattened_connectivity_templates : "${ct.bp}.${ct.name}" => ct
    if contains(local.ct_with_bindings, "${ct.bp}.${ct.name}")

  }
  blueprint_id             = local.blueprint_ids[each.value.bp]
  connectivity_template_id = apstra_datacenter_connectivity_template_interface.ct_interface["${each.value.bp}.${each.value.name}"].id
  application_point_ids = distinct(concat(
    can(each.value.bindings.by_link_tag) ? flatten([
      try(data.apstra_datacenter_interfaces_by_link_tag.interfaces_by_link_tag["${each.value.bp}.${each.value.name}"].ids, toset([]))
    ]) : [],
    can(each.value.bindings.by_if_name) ? flatten([
      for int_group in try(each.value.bindings.by_if_name, []) : [
        try(local.apstra_datacenter_interfaces_by_if_name["${each.value.bp}.${each.value.name}.${int_group.initial_device_name}"].ids, toset([]))
      ]
    ]) : []
  ))
}

# Update the subinterfaces in the Routing Zones to set the correct IP addresses to the endpoints

resource "terraform_data" "update_external_links_trigger" {
  count = local.blueprint_list != null ? 1 : 0
  input = local.flattened_primitives_ip_link
}

resource "terraform_data" "update_external_links" {
  count = local.blueprint_list != null ? 1 : 0
  lifecycle {
    replace_triggered_by = [
      terraform_data.update_external_links_trigger
    ]
  }
  depends_on = [
    apstra_datacenter_connectivity_template_assignments.connectivity_template_assignments,
  ]
  provisioner "local-exec" {
    command = "python3 ../python/apstra_update_external_links.py"
  }
}
