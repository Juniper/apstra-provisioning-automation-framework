#!/usr/bin/env python3.7
# coding: utf-8

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

'''
    Description: This script searches through blueprint data to identify connectivity templates that have bindings defined based on tags. 
    It then identifies those connectivity templates whose set of tags is assigned to at least one link of one of the generic systems.
    
    The resulting list of connectivity templates is intended for use with the Apstra Terraform provider resource "apstra_datacenter_connectivity_template_assignments".
    It ensures that only connectivity templates with at least one application point are iterated over when allocating them.
'''

# ---------------------------------------------------------------------------- #
#                                    Imports                                   #
# ---------------------------------------------------------------------------- #
from utils import *

def create_ct_with_bindings():
    '''
    Creates a list of connectivity templates with bindings based on tags that are assigned to at least one link of one of the generic systems.
    '''
    scope_manager = Scope_Manager()
    blueprints = scope_manager.get('blueprints')
    ct_with_bindings_path = scope_manager.get('ct_with_bindings_path')

    list_ct_with_bindings = []
    for bp_name in blueprints:
        # print("-"*20)
        # print(bp_name)
        # print("-"*20)
        bp_data = yamldecode(os.path.join(scope_manager.get('blueprints_path'), f'{bp_name}.yml'))
        for ct in bp_data.get("connectivity_templates", []):
            if "bindings" in ct and "by_link_tag" in ct["bindings"]:
                ct_has_any_binding = False
                for primitive in ct.get("primitives", []):
                    if primitive.get("is_a_root_primitive", []) and "data" in primitive:
                        ct_tags = ct.get("bindings", {}).get("by_link_tag", {}).get("tags", [])
                        for gs in bp_data.get("generic_systems", []):
                            for link in gs.get("links", []):
                                if set(ct_tags).issubset(set(link.get("tags", []))):
                                    ct_has_any_binding = True
            if ct_has_any_binding:
                list_ct_with_bindings.append(bp_name + "." + ct.get("name"))
            # else:
            #     print(ct.get("name", None))
            #     print(ct_tags)
    dict_ct_with_bindings = {ct_with_bindings_listname: list_ct_with_bindings}
    merged_yaml = merge_yaml_files(
        dict_ct_with_bindings
    )
    output_file = os.path.join(ct_with_bindings_path, ct_with_bindings_filename)
    create_output_file(merged_yaml, output_file)

if __name__ == '__main__':
    logger.info("Executing apstra_create_ct_with_bindings.py script")
    create_ct_with_bindings()
