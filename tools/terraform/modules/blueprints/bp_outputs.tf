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

# ----- Output variables // Module: blueprints


# output "vrfs" {
#   description = "All RZs"
#   value       = data.apstra_datacenter_routing_zone.vrfs
# }


# output "flattened_resources" {
#   description = "Flattened view of resources from the blueprints map utilizing the tuple format: [ bp - role - resource_pool ]"
#   value       = local.flattened_resources
# }

# output "flattened_switches" {
#   description = "Flattened view of switches from the blueprints map"
#   value       = local.flattened_switches
# }

output "flattened_generic_systems" {
  description = "Flattened view of generic systems from the blueprints map"
  value       = local.flattened_generic_systems
}

# output "flattened_primitives_ip_link" {
#   value       = local.flattened_primitives_ip_link
# }

# output "generic_systems" {
#   value = local.generic_systems
# }

# output "asn_pool_ids" {
#   description = "Mapping of each ASN resource name with its corresponding ID"
#   value = local.asn_pool_ids
# }

# output "vni_pool_ids" {
#   description = "Mapping of each VNI resource name with its corresponding ID"
#   value = local.vni_pool_ids
# }

# output "ipv4_pool_ids" {
#   description = "Mapping of each IPv4 resource name with its corresponding ID"
#   value       = local.ipv4_pool_ids
# }

output "interface_map_ids" {
  value = local.interface_map_ids
}
output "interface_map_ids_from_parent_project" {
  value = local.interface_map_ids_from_parent_project
}
output "interface_map_ids_from_local_project" {
  value = local.interface_map_ids_from_local_project
}

output "template_ids" {
  value = local.template_ids
}

output "template_ids_from_parent_project" {
  value = local.template_ids_from_parent_project
}
output "template_ids_from_local_project" {
  value = local.template_ids_from_local_project
}
output "flattened_vns" {
  value = local.flattened_vns
}
# output "resource_pool_ids" {
#   description = "Mapping of each resource name with its corresponding ID"
#   value       = local.resource_pool_ids
# }

output "rack_ids_from_local_project" {
  value = local.rack_ids_from_local_project
}
output "rack_ids_from_parent_project" {
  value = local.rack_ids_from_parent_project
}
output "rack_ids" {
  value = local.rack_ids
}

# output "configlet_ids_from_local_project" {
#   value = local.configlet_ids_from_local_project
# }
# output "configlet_ids_from_parent_project" {
#   value = local.configlet_ids_from_parent_project
# }
# output "configlet_ids" {
#   value = local.configlet_ids
# }

# output "switches_to_bp_allocation" {
#   value = local.switches_to_bp_allocation
# }

# output "switch_ids" {
#   description = "Mapping of each switch name with its corresponding ID"
#   value = local.switch_ids
# }
# output "bp_switch_ids" {
#   value = local.bp_switch_ids
# }


output "blueprint_ids_from_local_project" {
  value = local.blueprint_ids_from_local_project
}
output "blueprint_ids_from_parent_project" {
  value = local.blueprint_ids_from_parent_project
}
output "blueprint_ids" {
  value = local.blueprint_ids
}
output "blueprints_to_create" {
  value = local.blueprints_to_create
}

output "blueprints_not_to_create" {
  value = local.blueprints_not_to_create
}

output "vrf_ids_from_local_project" {
  value = local.vrf_ids_from_local_project
}
output "vrf_ids_from_parent_project" {
  value = local.vrf_ids_from_parent_project
}
output "vrf_ids" {
  value = local.vrf_ids
}


output "routing_policy_ids_from_local_project" {
  value = local.routing_policy_ids_from_local_project
}
output "routing_policy_ids_from_parent_project" {
  value = local.routing_policy_ids_from_parent_project
}
output "routing_policy_ids" {
  value = local.routing_policy_ids
}

output "vn_ids_from_local_project" {
  value = local.vn_ids_from_local_project
}
output "vn_ids_from_parent_project" {
  value = local.vn_ids_from_parent_project
}
output "vn_ids" {
  value = local.vn_ids
}

# output "vn_ids" {
#   description = "Mapping of each virtual network name with its corresponding ID"
#   value       = local.vn_ids
# }

# output "resources" {
#   description = "Mapping of each vrf name with its corresponding ID"
#   value       = apstra_datacenter_device_allocation.resources
# }

# output "device_allocation" {
#   description = "Device allocation resource"
#   value       = apstra_datacenter_device_allocation.devices
# }

# output "all_interface_ids" {
#   description = "All Interface IDs"
#   value       = data.apstra_datacenter_interfaces_by_system.interface_ids
# }

# output "interface_ids" {
#   description = "Interface IDs"
#   value       = local.flattened_interface_groups_by_if_name
# }

# output "switch_groups" {
#   description = "Switch groups"
#   value       = data.apstra_datacenter_systems.switch_groups
# }
# output "flattened_vn_bindings" {
#   description = "VN bindings"
#   value       = local.flattened_vn_bindings
# }

# output "vn_bindings" {
#   description = "VN bindings"
#   value       = data.apstra_datacenter_systems.vn_bindings
# }

# output "vn_binding_constructors" {
#   description = "VN binding constructors"
#   value       = data.apstra_datacenter_virtual_network_binding_constructor.vn_binding_constructors
# }

# output "virtual_networks" {
#   description = "VNs"
#   value       = apstra_datacenter_virtual_network.virtual_networks
# }


# output "flattened_primitives" {
#   description = "Flattened view of connectivity template primitives"
#   value       = local.flattened_primitives
# }

# output "flattened_connectivity_templates" {
#   description = "Flattened view of connectivity templates"
#   value       = local.flattened_connectivity_templates
# }

# output "flattened_primitives_static_route" {
#   description = "Flattened view of connectivity template primitives - type Static Route"
#   value       = local.flattened_primitives_static_route
# }

output "ct_with_bindings_from_parent_project" {
  value = local.ct_with_bindings_from_parent_project
}
output "ct_with_bindings_from_local_project" {
  value = local.ct_with_bindings_from_local_project
}
output "ct_with_bindings" {
  value = local.ct_with_bindings
}

# output "primitive_virtual_network_multiple" {
#   description = "Connectivity template primitives - type Virtual Network (Multiple)"
#   value       = data.apstra_datacenter_ct_virtual_network_multiple.virtual_network_multiple
# }

# output "flattened_app_points_interface_groups_by_link_tag" {
#   description = "Flattened view of application points within interface groups "
#   value       = local.flattened_app_points_interface_groups_by_link_tag
# }

# output "connectivity_tamplates" {
#   description = "Connectivity Template"
#   value       = apstra_datacenter_connectivity_template.connectivity_tamplates
# }

# output "interface_groups_by_if_name" {
#   description = "Groups of interfaces in a common system"
#   value       = data.apstra_datacenter_interfaces_by_system.interface_groups_by_if_name
# }

# output "interface_groups_by_if_name" {
#   description = "Groups of interfaces in a common system"
#   value       = data.apstra_datacenter_interfaces_by_system.interface_ids
# }

# output "interfaces_by_link_tag" {
#   description = "Groups of interfaces sharing a common link tag"
#   value       = data.apstra_datacenter_interfaces_by_link_tag.interfaces_by_link_tag
# }

# output "flattened_bindings_by_if_name" {
#   description = "Flattened group of interfaces belonging to a common switch"
#   value       = local.flattened_bindings_by_if_name
# }
# output "interfaces_by_system" {
#   description = "Groups of interfaces belonging to a common switch"
#   value       = data.apstra_datacenter_interfaces_by_system.interfaces_by_system
# }

# output "interfaces_by_if_name" {
#   description = "Groups of particular interfaces belonging to a common switch"
#   value       = local.apstra_datacenter_interfaces_by_if_name
# }

# output "connectivity_template_assignments" {
#   description = "Connectivity Template assignments"
#   value       = apstra_datacenter_connectivity_template_assignments.connectivity_template_assignments
# }


# ----- Output variables // Retrieved from module: design

# Mapping of each LD with its corresponding ID
output "logical_devices" {
  description = "Mapping of each LD with its corresponding ID"
  value       = module.design.logical_devices
}

# Mapping of each IM with its corresponding ID
output "interface_maps" {
  description = "Mapping of each IM with its corresponding ID"
  value       = module.design.interface_maps
}

# Mapping of each template name with its corresponding ID
output "rack_templates" {
  description = "Mapping of each rack template with its corresponding ID"
  value       = module.design.rack_templates
}

# Mapping of each rack type with its corresponding ID
output "racks" {
  description = "Mapping of each rack type with its corresponding"
  value       = module.design.racks
}

# Mapping of each configlet name with its corresponding ID
output "configlets" {
  description = "Mapping of each configlet with its corresponding ID"
  value       = module.design.configlets
}

# Mapping of each property set name with its corresponding ID and keys
output "property_sets" {
  description = "Mapping of each property set with its corresponding ID and keys"
  value       = module.design.property_sets
}

output "update_property_sets_trigger" {
  value = terraform_data.update_property_sets_trigger
}

# ----- Output variables // Retrieved from module: resources

# Mapping of each resource name with its corresponding ID

output "asn_pool_resources" {
  description = "Mapping of each ASN pool with its corresponding ID"
  value       = module.resources.asn_pool_resources
}
output "vni_pool_resources" {
  description = "Mapping of each VNI pool with its corresponding ID"
  value       = module.resources.vni_pool_resources
}
output "ipv4_pool_resources" {
  description = "Mapping of each IPv4 pool with its corresponding ID"
  value       = module.resources.ipv4_pool_resources
}
output "ipv6_pool_resources" {
  description = "Mapping of each IPv6 pool with its corresponding ID"
  value       = module.resources.ipv6_pool_resources
}
