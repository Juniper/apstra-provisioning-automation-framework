# ********************************************************

# Project: Apstra Provisioning Automation Framework

# Copyright (c) Juniper Networks, Inc., 2025. All rights reserved.

# Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

# SPDX-License-Identifier: Apache-2.0

# Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

# ********************************************************
output "parent_projects" {
  value = local.parent_projects
}

# ----- Output variables // Retrieved from module: private

# output "aos_user" {
#   description = "AOS GUI username"
#   # value       = var.aos_username
#   value     = local.aos_login.username
#   sensitive = true
# }

# output "aos_pwd" {
#   description = "AOS GUI password"
#   # value       = var.aos_password
#   value     = local.aos_login.password
#   sensitive = true
# }

# output "aos_ip" {
#   description = "AOS Server IP"
#   # value       = var.aos_ip
#   value     = local.aos_login.ip
#   sensitive = true
# }


# ----- Output variables // Retrieved from module: blueprints (originally from module design)

# Mapping of each LD with its corresponding ID
output "logical_devices" {
  description = "Mapping of each LD with its corresponding ID"
  value       = module.blueprints.logical_devices
}

# Mapping of each IM with its corresponding ID
output "interface_maps" {
  description = "Mapping of each IM with its corresponding ID"
  value       = module.blueprints.interface_maps
}

# Mapping of each template name with its corresponding ID
output "rack_templates" {
  description = "Mapping of each rack template with its corresponding ID"
  value       = module.blueprints.rack_templates
}

# Mapping of each rack type with its corresponding ID
output "racks" {
  description = "Mapping of each rack type with its corresponding"
  value       = module.blueprints.racks
}

# Mapping of each configlet name with its corresponding ID
output "configlets" {
  description = "Mapping of each configlet with its corresponding ID"
  value       = module.blueprints.configlets
}

# Mapping of each property set name with its corresponding ID and keys
output "property_sets" {
  description = "Mapping of each property set with its corresponding ID and keys"
  value       = module.blueprints.property_sets
}

output "update_property_sets_trigger" {
  value = module.blueprints.update_property_sets_trigger
}

# ----- Output variables // Retrieved from module: blueprints (originally from module resources)

# Mapping of each resource name with its corresponding ID

output "asn_pool_resources" {
  description = "Mapping of each ASN pool with its corresponding ID"
  value       = module.blueprints.asn_pool_resources
}
output "vni_pool_resources" {
  description = "Mapping of each VNI pool with its corresponding ID"
  value       = module.blueprints.vni_pool_resources
}
output "ipv4_pool_resources" {
  description = "Mapping of each IPv4 pool with its corresponding ID"
  value       = module.blueprints.ipv4_pool_resources
}
output "ipv6_pool_resources" {
  description = "Mapping of each IPv6 pool with its corresponding ID"
  value       = module.blueprints.ipv6_pool_resources
}

# ----- Output variables // Retrieved from module: blueprints

output "ct_with_bindings_from_parent_project" {
  value = module.blueprints.ct_with_bindings_from_parent_project
}
output "ct_with_bindings_from_local_project" {
  value = module.blueprints.ct_with_bindings_from_local_project
}
output "ct_with_bindings" {
  value = module.blueprints.ct_with_bindings
}

# output "flattened_primitives_ip_link" {
#   value = module.blueprints.flattened_primitives_ip_link
# }

# output "asn_pool_ids" {
#   description = "Mapping of each ASN resource name with its corresponding ID"
#   value = module.blueprints.asn_pool_ids
# }

# output "vni_pool_ids" {
#   description = "Mapping of each VNI resource name with its corresponding ID"
#   value = module.blueprints.vni_pool_ids
# }

# output "ipv4_pool_ids" {
#   description = "Mapping of each IPv4 resource name with its corresponding ID"
#   value = module.blueprints.ipv4_pool_ids
# }

# output "resource_pool_ids" {
#   description = "Mapping of each resource name with its corresponding ID"
#   value       = module.blueprints.resource_pool_ids
# }

# output "ipv4_pool_ids_from_parent_project" {
#   value = module.blueprints.ipv4_pool_ids_from_parent_project
# }

# output "template_ids" {
#   description = "Mapping of each template name with its corresponding ID"
#   value       = module.blueprints.template_ids
# }

# output "rack_ids_from_local_project" {
#   value = module.blueprints.rack_ids_from_local_project
# }
# output "rack_ids_from_parent_project" {
#   value = module.blueprints.rack_ids_from_parent_project
# }
# output "rack_ids" {
#   value = module.blueprints.rack_ids
# }

# output "configlet_ids_from_local_project" {
#   value = module.blueprints.configlet_ids_from_local_project
# }
# output "configlet_ids_from_parent_project" {
#   value = module.blueprints.configlet_ids_from_parent_project
# }
# output "configlet_ids" {
#   value = module.blueprints.configlet_ids
# }

output "interface_map_ids_from_local_project" {
  value = module.blueprints.interface_map_ids_from_local_project
}
output "interface_map_ids_from_parent_project" {
  value = module.blueprints.interface_map_ids_from_parent_project
}
output "interface_map_ids" {
  value = module.blueprints.interface_map_ids
}

output "template_ids_from_local_project" {
  value = module.blueprints.template_ids_from_local_project
}
output "template_ids_from_parent_project" {
  value = module.blueprints.template_ids_from_parent_project
}
output "template_ids" {
  value = module.blueprints.template_ids
}
output "flattened_vns" {
  value = module.blueprints.flattened_vns
}

# output "switches_to_bp_allocation" {
#   value = module.blueprints.switches_to_bp_allocation
# }

# output "switch_ids" {
#   description = "Mapping of each switch name with its corresponding ID"
#   value       = module.blueprints.switch_ids
# }
# output "bp_switch_ids" {
#   value       = module.blueprints.bp_switch_ids
# }

output "blueprint_ids_from_local_project" {
  value = module.blueprints.blueprint_ids_from_local_project
}

output "blueprint_ids_from_parent_project" {
  value = module.blueprints.blueprint_ids_from_parent_project
}
output "blueprint_ids" {
  value = module.blueprints.blueprint_ids
}

output "blueprints_to_create" {
  value = module.blueprints.blueprints_to_create
}

output "blueprints_not_to_create" {
  value = module.blueprints.blueprints_not_to_create
}

output "vrf_ids_from_local_project" {
  value = module.blueprints.vrf_ids_from_local_project
}
output "vrf_ids_from_parent_project" {
  value = module.blueprints.vrf_ids_from_parent_project
}
output "vrf_ids" {
  value = module.blueprints.vrf_ids
}

output "routing_policy_ids_from_local_project" {
  value = module.blueprints.routing_policy_ids_from_local_project
}
output "routing_policy_ids_from_parent_project" {
  value = module.blueprints.routing_policy_ids_from_parent_project
}
output "routing_policy_ids" {
  value = module.blueprints.routing_policy_ids
}

output "vn_ids_from_local_project" {
  value = module.blueprints.vn_ids_from_local_project
}
output "vn_ids_from_parent_project" {
  value = module.blueprints.vn_ids_from_parent_project
}
output "vn_ids" {
  value = module.blueprints.vn_ids
}

# output "vn_ids" {
#   description = "Mapping of each virtual network name with its corresponding ID"
#   value       = module.blueprints.vn_ids
# }

# output "resources" {
#   description = "Mapping of each vrf name with its corresponding ID"
#   value       = module.blueprints.resources
# }

# output "device_allocation" {
#   description = "Device allocation resource"
#   value       = module.blueprints.device_allocation
# }

# output "all_interface_ids" {
#   description = "All Interface IDs"
#   value       = module.blueprints.all_interface_ids
# }

# output "interface_ids" {
#   description = "Interface IDs"
#   value       = module.blueprints.interface_ids
# }

# output "flattened_resources" {
#   description = "Flattened view of resources from the blueprints map utilizing the tuple format: [ bp - role - resource_pool ]"
#   value       = module.blueprints.flattened_resources
# }

# output "flattened_switches" {
#   description = "Flattened view of switches from the blueprints map"
#   value       = module.blueprints.flattened_switches
# }

output "flattened_generic_systems" {
  description = "Flattened view of generic systems from the blueprints map"
  value       = module.blueprints.flattened_generic_systems
}

# output "generic_systems" {
#   value = module.blueprints.generic_systems
# }

# output "logical_devices" {
#   description = "Mapping of each LD with its corresponding ID"
#   value       = module.blueprints.logical_devices
# }

# output "logical_device_names" {
#   description = "logical_device_names"
#   value       = module.blueprints.logical_device_names
# }

# output "interface_map_names" {
#   description = "interface_map_names"
#   value       = module.blueprints.interface_map_names
# }

# output "ipv4_pools" {
#   description = "IPv4 pools decoded from YAML"
#   value       = module.blueprints.ipv4_pools
# }

# output "switch_groups" {
#   description = "Switch groups"
#   value       = module.blueprints.switch_groups
# }

# output "vn_binding_constructors" {
#   description = "VN binding constructors"
#   value       = module.blueprints.vn_binding_constructors
# }

# output "flattened_primitives" {
#   description = "Mapping of each virtual network name with its corresponding ID"
#   value       = module.blueprints.flattened_primitives
# }

# output "flattened_connectivity_templates" {
#   description = "Flattened view of connectivity templates"
#   value       = module.blueprints.flattened_connectivity_templates
# }

# output "connectivity_template_assignments" {
#   description = "Connectivity Template assignments"
#   value       = module.blueprints.connectivity_template_assignments
# }

# output "flattened_primitives_static_route" {
#   description = "Flattened view of connectivity template primitives - type Static Route"
#   value       = module.blueprints.flattened_primitives_static_route
# }

# output "primitive_virtual_network_multiple" {
#   description = "Connectivity template primitives - type Virtual Network (Multiple)"
#   value       = module.blueprints.primitive_virtual_network_multiple
# }

# output "flattened_app_points_interface_groups_by_link_tag" {
#   description = "Flattened view of application points within interface groups "
#   value       = module.blueprints.flattened_app_points_interface_groups_by_link_tag
# }

# output "flattened_vn_bindings" {
#   description = "VN bindings"
#   value       = module.blueprints.flattened_vn_bindings
# }

# output "vn_bindings" {
#   description = "VN bindings"
#   value       = module.blueprints.vn_bindings
# }

# output "vn_binding_constructors" {
#   description = "VN binding constructors"
#   value       = module.blueprints.vn_binding_constructors
# }

# output "virtual_networks" {
#   description = "VNs"
#   value       = module.blueprints.virtual_networks
# }

# output "connectivity_tamplates" {
#   description = "Connectivity Template"
#   value       = module.blueprints.connectivity_tamplates
# }

# output "interface_groups_by_if_name" {
#   description = "Groups of interfaces in a common system"
#   value       = module.blueprints.interface_groups_by_if_name
# }

# output "interfaces_by_link_tag" {
#   description = "Groups of interfaces sharing a common link tag"
#   value       = module.blueprints.interfaces_by_link_tag
# }

# output "flattened_bindings_by_if_name" {
#   description = "Flattened group of interfaces belonging to a common switch"
#   value       = module.blueprints.flattened_bindings_by_if_name
# }

# output "interfaces_by_system" {
#   description = "Groups of interfaces belonging to a common switch"
#   value       = module.blueprints.interfaces_by_system
# }

# output "interfaces_by_if_name" {
#   description = "Groups of specific interfaces belonging to a common switch"
#   value       = module.blueprints.interfaces_by_if_name
# }

# output "connectivity_tamplates_assignments" {
#   description = "Connectivity Template assignment"
#   value       = module.blueprints.connectivity_tamplates_assignments
# }

# output "connectivity_template_assignments" {
#   description = "Connectivity Template assignment"
#   value       = module.blueprints.connectivity_template_assignments
# }

# output "racks" {
#   description = "Racks"
#   value       = module.blueprints.racks
# }

# output "mapped_racks" {
#   description = "Racks"
#   value       = module.blueprints.mapped_racks
# }

# output "all_tags" {
#   description = "all_tags"
#   value       = module.blueprints.all_tags
# }

# output "rack_ids" {
#   description = "Rack IDs"
#   value       = module.blueprints.rack_ids
# }

# output "resource_racks" {
#   description = "Resource racks"
#   value       = module.blueprints.resource_racks
# }

# output "property_set" {
#   description = "Property set data"
#   value       = module.blueprints.property_set
# }

# output "data_property_sets" {
#   description = "Property set data"
#   value       = module.blueprints.data_property_sets
# }

# output "property_set_ids_and_keys" {
#   description = "Property set ids and keys"
#   value       = module.blueprints.property_set_ids
# }

# ! Pending: device ack

# output "agent_profiles" {
#   description = "List of Agent Profile IDs"
#   value       = module.blueprints.agent_profiles
# }
# output "agent_profiles_id_junos" {
#   description = "Agent Profile map filtered for Junos boxes."
#   value       = module.blueprints.agent_profiles_id_junos
# }

# output "apstra_managed_devices" {
#   description = "Junos devices managed by Apstra to be acknowledged"
#   value       = module.blueprints.apstra_managed_devices
# }

# output "im_bindings" {
#   description = "Interface Map LD - DP bindings"
#   value       = module.blueprints.im_bindings
# }

# output "tag" {
#   description = "Apstra tag"
#   value       = module.blueprints.tag
# }

# output "leaf_tags" {
#   description = "Leaf tags"
#   value       = module.blueprints.leaf_tags
# }

# output "generic_system_tags" {
#   description = "Generic System tags"
#   value       = module.blueprints.generic_system_tags
# }

# output "all_tags" {
#   description = "All tags"
#   value       = module.blueprints.all_tags
# }

# output "vrfs" {
#   description = "All RZs"
#   value       = module.blueprints.vrfs
# }

# output "resources" {
#   value = module.blueprints.resources
# }

# output "resources" {
#   value = module.blueprints.resources
# }

# output "output_my_script" {
#   value = module.blueprints.output_my_script
# }

# output "output_my_script" {
#   value = [
#     for result in data.external.my_script : result
#   ]
#   depends_on = [
#     apstra_blueprint_deployment.deploy,
#   ]
