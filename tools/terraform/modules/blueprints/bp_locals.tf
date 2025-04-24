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

# ----- Local variables // Module: blueprints

locals {

  # Mapping of each resource name with its corresponding ID
  # for those resources created within the local project
  asn_pool_ids_from_local_project = {
    for asn_pool_name, asn_pool_data in module.resources.asn_pool_resources :
    asn_pool_name => asn_pool_data.id
  }
  vni_pool_ids_from_local_project = {
    for vni_pool_name, vni_pool_data in module.resources.vni_pool_resources :
    vni_pool_name => vni_pool_data.id
  }
  ipv4_pool_ids_from_local_project = {
    for ipv4_pool_name, ipv4_pool_data in module.resources.ipv4_pool_resources :
    ipv4_pool_name => ipv4_pool_data.id
  }

  # Mapping of each resource name with its corresponding ID
  # for those resources received from the parent projects
  asn_pool_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for asn_pool_name, asn_pool_data in try(project_data.outputs.asn_pool_resources, {}) :
      asn_pool_name => asn_pool_data.id
    }
  ]...)
  vni_pool_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for vni_pool_name, vni_pool_data in try(project_data.outputs.vni_pool_resources, {}) :
      vni_pool_name => vni_pool_data.id
    }
  ]...)
  ipv4_pool_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for ipv4_pool_name, ipv4_pool_data in try(project_data.outputs.ipv4_pool_resources, {}) :
      ipv4_pool_name => ipv4_pool_data.id
    }
  ]...)

  resource_pool_ids = merge(
    local.asn_pool_ids_from_local_project,
    local.vni_pool_ids_from_local_project,
    local.ipv4_pool_ids_from_local_project,
    local.asn_pool_ids_from_parent_project,
    local.vni_pool_ids_from_parent_project,
    local.ipv4_pool_ids_from_parent_project
  )

  # Mapping of each template name with its corresponding ID
  # for those templates created within the local project
  template_ids_from_local_project = {
    for template_name, template_data in module.design.rack_templates :
    template_name => template_data.id
  }

  # Mapping of each template name with its corresponding ID
  # for those templates received from the parent projects
  template_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for template_name, template_data in try(project_data.outputs.rack_templates, {}) :
      template_name => template_data.id
    }
  ]...)

  template_ids = merge(
    local.template_ids_from_local_project,
    local.template_ids_from_parent_project
  )

  # Mapping of each rack name with its corresponding ID
  # for those racks created within the local project
  rack_ids_from_local_project = {
    for rack_name, rack_data in module.design.racks :
    rack_name => rack_data.id
  }

  # Mapping of each rack name with its corresponding ID
  # for those racks received from the parent projects
  rack_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for rack_name, rack_data in try(project_data.outputs.racks, {}) :
      rack_name => rack_data.id
    }
  ]...)

  rack_ids = merge(
    local.rack_ids_from_local_project,
    local.rack_ids_from_parent_project
  )

  # Mapping of each property set name with its corresponding ID
  # for those property sets created within the local project
  property_set_ids_from_local_project = {
    for property_set_name, property_set_data in module.design.property_sets :
    property_set_name => property_set_data.id
  }

  # Mapping of each property set name with its corresponding ID
  # for those property sets received from the parent projects
  property_set_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for property_set_name, property_set_data in try(project_data.outputs.property_sets, {}) :
      property_set_name => property_set_data.id
    }
  ]...)

  property_set_ids = merge(
    local.property_set_ids_from_local_project,
    local.property_set_ids_from_parent_project
  )

  # Mapping of each initial interface map name with its corresponding ID
  # for those initial interface maps created within the local project
  interface_map_ids_from_local_project = {
    for interface_map_name, interface_map_data in module.design.interface_maps :
    interface_map_name => interface_map_data.id
  }

  # Mapping of each initial interface map name with its corresponding ID
  # for those initial interface maps received from the parent projects
  interface_map_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for interface_map_name, interface_map_data in try(project_data.outputs.interface_maps, {}) :
      interface_map_name => interface_map_data.id
    }
  ]...)

  interface_map_ids = merge(
    local.interface_map_ids_from_local_project,
    local.interface_map_ids_from_parent_project
  )

  # Mapping of each configlet name with its corresponding ID
  # for those configlets created within the local project
  configlet_ids_from_local_project = {
    for configlet_name, configlet_data in module.design.configlets :
    configlet_name => configlet_data.id
  }

  # Mapping of each configlet name with its corresponding ID
  # for those configlets received from the parent projects
  configlet_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for configlet_name, configlet_data in try(project_data.outputs.configlets, {}) :
      configlet_name => configlet_data.id
    }
  ]...)

  configlet_ids = merge(
    local.configlet_ids_from_local_project,
    local.configlet_ids_from_parent_project
  )

  # Mapping of each vrf name with its corresponding ID
  # for those vrfs created within the local project
  vrf_ids_from_local_project = {
    for vrf_name, vrf_data in apstra_datacenter_routing_zone.vrfs :
    vrf_name => vrf_data.id
  }

  # Mapping of each vrf name with its corresponding ID
  # for those vrfs received from the parent projects
  vrf_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for vrf_name, vrf_data in try(project_data.outputs.vrf_ids, {}) :
      vrf_name => vrf_data
    }
  ]...)

  vrf_ids = merge(
    local.vrf_ids_from_local_project,
    local.vrf_ids_from_parent_project
  )

  # Mapping of each routing policy name with its corresponding ID
  # for those routing policies created within the local project
  routing_policy_ids_from_local_project = {
    for routing_policy_name, routing_policy_data in apstra_datacenter_routing_policy.routing_policies :
    routing_policy_name => routing_policy_data.id
  }

  # Mapping of each routing policy name with its corresponding ID
  # for those routing policies received from the parent projects
  routing_policy_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for routing_policy_name, routing_policy_data in try(project_data.outputs.routing_policy_ids, {}) :
      routing_policy_name => routing_policy_data
    }
  ]...)

  routing_policy_ids = merge(
    local.routing_policy_ids_from_local_project,
    local.routing_policy_ids_from_parent_project
  )

  # Mapping of each vn name with its corresponding ID
  # for those vns created within the local project
  vn_ids_from_local_project = {
    for vn_name, vn_data in apstra_datacenter_virtual_network.virtual_networks :
    vn_name => vn_data.id
  }

  # Mapping of each vn name with its corresponding ID
  # for those vns received from the parent projects
  vn_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for vn_name, vn_data in try(project_data.outputs.vn_ids, {}) :
      vn_name => vn_data
    }
  ]...)

  vn_ids = merge(
    local.vn_ids_from_local_project,
    local.vn_ids_from_parent_project
  )

  # YAML file decoded and made into a terraform list
  blueprint_list = try(yamldecode(file("${var.blueprints_path}/${var.blueprints_filename}"))["blueprints"], [])

  # Map storing the YAML contents of each blueprint file
  blueprints = try({
    for bp_name in try(local.blueprint_list, []) :
    bp_name => yamldecode(file("${var.blueprints_path}/${bp_name}.yml"))
    if can(file("${var.blueprints_path}/${bp_name}.yml"))
    # if can(file("${var.blueprints_path}/${bp_name}.yml")) && can(yamldecode(file("${var.blueprints_path}/${bp_name}.yml")).template)
    # if blueprint_data.template != null
  }, {})

  # Map storing the YAML contents of each blueprint file ONLY for those blueprints to be created in the local project
  blueprints_to_create = try({
    for bp_name in try(local.blueprint_list, []) :
    bp_name => yamldecode(file("${var.blueprints_path}/${bp_name}.yml"))
    # bp_name => "bla"
    # if can(file("${var.blueprints_path}/${bp_name}.yml")) && yamldecode(file("${var.blueprints_path}/${bp_name}.yml")).template != null
    if can(file("${var.blueprints_path}/${bp_name}.yml")) && can(yamldecode(file("${var.blueprints_path}/${bp_name}.yml")).template)
    # if blueprint_data.template != null
  }, {})

  blueprints_not_to_create = { for k, v in local.blueprints : k => v if !contains(keys(local.blueprints_to_create), k) }


  # Mapping of each blueprint name with its corresponding ID
  # for those blueprints created within the local project
  blueprint_ids_from_local_project = {
    for blueprint_name, blueprint_data in apstra_datacenter_blueprint.blueprints :
    blueprint_name => blueprint_data.id
  }

  # Mapping of each blueprint with its corresponding ID
  # for those blureprints received from the parent projects
  blueprint_ids_from_parent_project = merge([
    for project, project_data in var.parent_project_outputs : {
      for blueprint_name, blueprint_id in try(project_data.outputs.blueprint_ids, {}) :
      blueprint_name => blueprint_id
    }
  ]...)


  blueprint_ids = merge(
    local.blueprint_ids_from_local_project,
    local.blueprint_ids_from_parent_project
  )

  # Combine all the "switches" lists from every <bp>.yml file, and append the corresponding bp name to each list member. 
  switches_to_bp_allocation = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for device in try(blueprint_data.switches, []) :
      merge(
        { bp = blueprint_key },
        device
      )
    ]
  ])

  # Mapping of each initial switch name with its corresponding ID
  switch_ids = can(apstra_datacenter_device_allocation.devices) ? {
    for switch_key, switch_data in apstra_datacenter_device_allocation.devices :
    "${switch_data.blueprint_id}.${switch_data.node_name}" => switch_data.node_id
  } : {}

  # Mapping of each blueprint switch name with its corresponding ID
  bp_switch_ids = try({
  for switch_key, switch_data in apstra_datacenter_device_allocation.devices :
    "${switch_data.blueprint_id}.${switch_data.system_attributes["name"]}" => switch_data.node_id
  }, {})

  # Combine all the "generic_systems" lists from every <bp>.yml file, and append the corresponding bp name to each list member.
  flattened_generic_systems = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for generic_system in try(blueprint_data.generic_systems, []) :
      merge(
        { bp = blueprint_key },
        generic_system
      )
    ]
  ])

  # Combine all the "spines" lists from every <bp>.yml file, and append the corresponding bp name to each list member.
  flattened_spines = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for spine in try(blueprint_data.spines, []) :
      merge(
        { bp = blueprint_key },
        spine
      )
    ]
  ])

  # Combine all the "routing_policies" lists from every <bp>.yml file, and append the corresponding bp name to each list member.
  flattened_routing_policies = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for routing_policy in try(blueprint_data.routing_policies, []) :
      merge(
        { bp = blueprint_key },
        routing_policy
      )
    ]
  ])


  # Combine all the "vrfs" lists from every <bp>.yml file, and append the corresponding bp name to each list member.
  flattened_vrfs = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for vrf_type, vrf_data in try(blueprint_data.vrfs, {}) : [
        for vrf in try(vrf_data, []) :
        merge(
          { bp = blueprint_key },
          { vrf_type = vrf_type },
          vrf
        )
      ]
    ]
  ])

  flattened_resources = concat(
    # Resources under the "resources" stanza in <bp>.yml : attribute "vrf" = "n/a" (fabric-wide resources)
    flatten([
      for blueprint_key, blueprint_data in local.blueprints : [
        for resource in try(blueprint_data.resources, []) :
        merge(
          { bp = blueprint_key },
          { vrf = "n/a" },
          resource
        )
      ]
    ]),
    # Resources under the "vrfs" stanza in <bp>.yml: attribute "vrf" = routing_zone_name 
    flatten([
      for blueprint_key, blueprint_data in local.blueprints : [
        for vrf_type, vrf_data in try(blueprint_data.vrfs, {}) : [
          for vrf in try(vrf_data, []) : [
            for resource in try(vrf.resources, []) :
            merge(
              { bp = blueprint_key },
              { vrf = try(vrf.name, null) },
              resource
            )
          ]
        ]
      ]
    ])
  )

  # Combine all the "vn_bindings" lists from every <bp>.yml file, and append the corresponding bp name to each list member.
  flattened_vn_bindings = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for vn in try(blueprint_data.virtual_networks, []) : [
        for binding in try(vn.bindings, []) :
        merge(
          { bp = blueprint_key },
          { vn = vn.name },
          binding
        )
      ]
    ]
  ])

  # Combine all the "vns" lists from every <bp>.yml file, and append the corresponding bp name to each list member.
  flattened_vns = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for virtual_network in try(blueprint_data.virtual_networks, []) :
      merge(
        { bp = blueprint_key },
        # { id = index(try(blueprint_data.virtual_networks, []), virtual_network) },
        virtual_network
      )
    ]
  ])

  # Combine all the "racks" lists from every <bp>.yml file, and append the corresponding bp name to each list member.
  flattened_racks = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for rack in try(blueprint_data.racks, []) :
      merge(
        { bp = blueprint_key },
        rack
      )
    ]
  ])

  ct_with_bindings_from_local_project = distinct(flatten([
    for blueprint_key, blueprint_data in local.blueprints_to_create : [
      for ct in try(blueprint_data.connectivity_templates, []) : [
        for primitive in lookup(ct, "primitives", []) : [
          for gs in lookup(blueprint_data, "generic_systems", []) : [
            for link in lookup(gs, "links", []) : [
              "${blueprint_key}.${ct.name}"
            ]
            if contains(keys(link), "tags") && (toset(lookup(ct.bindings.by_link_tag, "tags", [])) == setintersection(lookup(link, "tags", []), lookup(ct.bindings.by_link_tag, "tags", [])))
          ]
        ]
        if lookup(primitive, "is_a_root_primitive", false) && contains(keys(primitive), "data")
      ]
      if contains(try(keys(ct.bindings), []), "by_link_tag")
    ]
  ]))

  ct_with_bindings_from_parent_project = distinct(flatten([
    for blueprint_key, blueprint_data in local.blueprints_not_to_create : [
      for ct in try(blueprint_data.connectivity_templates, []) : [
        for primitive in lookup(ct, "primitives", []) : [
          for project, project_data in var.parent_project_outputs : [
            for gs in try(project_data.outputs.flattened_generic_systems, []) : [
              for link in lookup(gs, "links", []) : [
                "${blueprint_key}.${ct.name}"
              ]
              if contains(keys(link), "tags") && (toset(lookup(ct.bindings.by_link_tag, "tags", [])) == setintersection(lookup(link, "tags", []), lookup(ct.bindings.by_link_tag, "tags", [])))
            ]
            if blueprint_key == lookup(gs, "bp", null)
          ]
        ]
        if lookup(primitive, "is_a_root_primitive", false) && contains(keys(primitive), "data")
      ]
      # if contains(keys(ct), "bindings") && contains(try(keys(ct.bindings), []), "by_link_tag")
      if contains(try(keys(ct.bindings), []), "by_link_tag")
    ]
  ]))

  ct_with_bindings = concat(
    local.ct_with_bindings_from_local_project,
    local.ct_with_bindings_from_parent_project
  )

  # Combine all the "by_link_tag" lists from every ct within each <bp>.yml file, and append the corresponding bp and ct names to each list.
  flattened_bindings_by_link_tag = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for ct in try(blueprint_data.connectivity_templates, []) : [
        merge(
          { bp = blueprint_key },
          { ct = ct.name },
          ct.bindings.by_link_tag
        )
      ]
      if can(ct.bindings.by_link_tag)
    ]
  ])

  # Combine all the "by_if_name" members from every ct within every <bp>.yml file, and append the corresponding ct and bp names to each list member.
  flattened_bindings_by_if_name = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for ct in try(blueprint_data.connectivity_templates, []) : [
        for binding in try(ct.bindings.by_if_name, []) :
        merge(
          { bp = blueprint_key },
          { ct = ct.name },
          binding
        )
      ]
      if can(ct.bindings.by_if_name)
    ]
  ])

  # Combine all the "primitive" lists from every connectivity template from every <bp>.yml file, and append the corresponding bp and ct names to each list member.
  flattened_primitives = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for connectivity_template in try(blueprint_data.connectivity_templates, []) : [
        for primitive in try(connectivity_template.primitives, []) :
        merge(
          { bp = blueprint_key },
          { ct = connectivity_template.name },
          primitive
        )
      ]
    ]
  ])

  # Combine all the IP LINK type "primitive" lists from every connectivity template from every <bp>.yml file, and append the corresponding bp and ct names to each list member.
  flattened_primitives_ip_link = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for connectivity_template in try(blueprint_data.connectivity_templates, []) : [
        for primitive in try(connectivity_template.primitives, []) :
        merge(
          { bp = blueprint_key },
          { ct = connectivity_template.name },
          primitive
        )
        if primitive.type == "ip_link"
      ]
    ]
  ])


  # Combine all the "connectivity_template" lists from every <bp>.yml file, and append the corresponding bp name to each list member.
  flattened_connectivity_templates = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for connectivity_template in try(blueprint_data.connectivity_templates, []) :
      merge(
        { bp = blueprint_key },
        connectivity_template
      )
    ]
  ])

  # Combine all the "configlet" lists from every <bp>.yml file, and append the corresponding bp name to each list member.
  flattened_configlets = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for configlet in try(blueprint_data.import_configlets, []) :
      merge(
        { bp = blueprint_key },
        configlet
      )
    ]
  ])

  # Combine all the "imported_property_set" lists from every <bp>.yml file, and append the corresponding bp name to each list member.
  flattened_property_sets = flatten([
    for blueprint_key, blueprint_data in local.blueprints : [
      for property_set in try(blueprint_data.import_property_sets, []) :
      merge(
        { bp = blueprint_key },
        property_set
      )
    ]
  ])

}
