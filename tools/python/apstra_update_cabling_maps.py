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
    Description: This script updates Cabling Map files obtained from Apstra based on the <bp>.yml interface data in order to preserve the expected interface mapping. 
    Additionally, it offers the option to:
    - Fetch Cabling Map files from Apstra if the "pull_cabling_maps" argument is provided.
    - Upload modified Cabling Map files to Apstra if the "push_cabling_maps" argument is provided.

    Furthermore, it automatically creates backups of the last five JSON output files generated for comparison and rollback purposes.
'''

# ---------------------------------------------------------------------------- #
#                                    Imports                                   #
# ---------------------------------------------------------------------------- #
from utils import *

def update_cabling_maps():
    try:

        scope_manager = Scope_Manager()
        blueprints_path = scope_manager.get('blueprints_path')
        blueprints = scope_manager.get('blueprints')
        input_cabling_map_path = scope_manager.get('wip_execution_0_cabling_map_path')
        output_cabling_map_path = scope_manager.get('wip_execution_0_cabling_map_path')

        if not os.path.exists(output_cabling_map_path):
            os.makedirs(output_cabling_map_path)
        bps_with_updated_cabling_map = []
        for bp_name in blueprints:
            bp_in_cm_dir = os.path.join(input_cabling_map_path, bp_name)
            cm_filename = f"in_cm_{bp_name}.yml"
            # Check if the original Cabling Map YAML file exists
            if cm_filename not in os.listdir(bp_in_cm_dir):
                raise FileNotFoundError(f"No YAML Cabling Map found in the expected location: {cm_filename}")
            in_cm_data = yamldecode(os.path.join(bp_in_cm_dir, cm_filename))
            out_cm_data = {'links' : []}
            bp_data = yamldecode(os.path.join(blueprints_path, f'{bp_name}.yml'))

            eval_leaf_spine = 'spines' in bp_data
            eval_leaf_gs = 'generic_systems' in bp_data
            if eval_leaf_spine or eval_leaf_gs:

                # Leaf - Spine
                if eval_leaf_spine:
                    rprint(f"Modifying the Cabling Maps:  Leaf <> Spine links.")
                    for spine in bp_data.get('spines', None):
                        spine_hostname = spine['hostname']
                        for link in spine['links']:
                            spine_if_name = link['spine_if_name']
                            spine_ip = link.get('spine_ip', None)
                            leaf_hostname = link['target_switch_hostname']
                            leaf_if_name = link['target_switch_if_name']
                            leaf_ip = link.get('target_switch_ip', None)
                            # Iterate over the cabling map until finding the link with the endpoint hostnames which mach those in the Terraform YAML file
                            for cm_link in in_cm_data['links']:
                                if cm_link['role'] == 'spine_leaf':
                                    # endpoints order: [spine, leaf]
                                    # if cm_link['endpoints'][0]['system']['label'] == spine_hostname and cm_link['endpoints'][1]['system']['label'] == leaf_hostname and (cm_link['endpoints'][0]['interface']['if_name'] == spine_if_name or cm_link['endpoints'][1]['interface']['if_name'] == leaf_if_name):
                                    if cm_link['endpoints'][0]['system']['label'] == spine_hostname and cm_link['endpoints'][1]['system']['label'] == leaf_hostname:
                                        out_cm_data['links'].append({
                                            'endpoints': [
                                                {'interface' : {
                                                        'id' : cm_link['endpoints'][0]['interface']['id'],
                                                        'if_name' : spine_if_name,
                                                        # 'ipv4_addr' : spine_ip,
                                                }},
                                                {'interface' : {
                                                        'id' : cm_link['endpoints'][1]['interface']['id'],
                                                        'if_name' : leaf_if_name,
                                                        # 'ipv4_addr' : leaf_ip,
                                                }},
                                            ]
                                        })

                                        if spine_ip is not None and leaf_ip is not None:
                                            out_cm_data['links'][-1]['endpoints'][0]['interface'].update({'ipv4_addr' : spine_ip})
                                            out_cm_data['links'][-1]['endpoints'][1]['interface'].update({'ipv4_addr' : leaf_ip})                    

                                    # endpoints order: [leaf, spine]
                                    # elif cm_link['endpoints'][1]['system']['label'] == spine_hostname and cm_link['endpoints'][0]['system']['label'] == leaf_hostname and (cm_link['endpoints'][1]['interface']['if_name'] == spine_if_name or cm_link['endpoints'][0]['interface']['if_name'] == leaf_if_name):
                                    elif cm_link['endpoints'][1]['system']['label'] == spine_hostname and cm_link['endpoints'][0]['system']['label'] == leaf_hostname:
                                        out_cm_data['links'].append({
                                            'endpoints': [
                                                {'interface' : {
                                                        'id' : cm_link['endpoints'][0]['interface']['id'],
                                                        'if_name' : leaf_if_name,
                                                        # 'ipv4_addr' : leaf_ip,
                                                }},
                                                {'interface' : {
                                                        'id' : cm_link['endpoints'][1]['interface']['id'],
                                                        'if_name' : spine_if_name,
                                                        # 'ipv4_addr' : spine_ip,
                                                }},
                                            ]
                                        })

                                        if spine_ip is not None and leaf_ip is not None:
                                            out_cm_data['links'][-1]['endpoints'][0]['interface'].update({'ipv4_addr' : leaf_ip})
                                            out_cm_data['links'][-1]['endpoints'][1]['interface'].update({'ipv4_addr' : spine_ip})                    

                # Leaf - Generic System
                if eval_leaf_gs:
                    rprint(f"Modifying the Cabling Maps:  Leaf <> Generic System links.")
                    for gs in bp_data.get('generic_systems', None):
                        gs_hostname = gs['name']
                        for link in gs['links']:
                            gs_if_name = link['generic_system_if_name']
                            leaf_hostname = link['target_switch_hostname']
                            leaf_if_name = link['target_switch_if_name']
                            # Iterate over the cabling map until finding the link with the endpoint hostnames which mach those in the Terraform YAML file
                            for cm_link in in_cm_data['links']:
                                if cm_link['role'] == 'to_generic':
                                    # endpoints order: [generic system, leaf]
                                    if cm_link['endpoints'][0]['system']['label'] == gs_hostname and cm_link['endpoints'][1]['system']['label'] == leaf_hostname and cm_link['endpoints'][1]['interface']['if_name'] == leaf_if_name:
                                        out_cm_data['links'].append({
                                            'endpoints': [
                                                {'interface' : {
                                                        'id' : cm_link['endpoints'][0]['interface']['id'],
                                                        'if_name' : gs_if_name,
                                                }},
                                                {'interface' : {
                                                        'id' : cm_link['endpoints'][1]['interface']['id'],
                                                        'if_name' : leaf_if_name,
                                                }},
                                            ]
                                        })
                                    # endpoints order: [leaf, generic system]
                                    elif cm_link['endpoints'][1]['system']['label'] == gs_hostname and cm_link['endpoints'][0]['system']['label'] == leaf_hostname and cm_link['endpoints'][0]['interface']['if_name'] == leaf_if_name:
                                        out_cm_data['links'].append({
                                            'endpoints': [
                                                {'interface' : {
                                                        'id' : cm_link['endpoints'][0]['interface']['id'],
                                                        'if_name' : leaf_if_name,
                                                }},
                                                {'interface' : {
                                                        'id' : cm_link['endpoints'][1]['interface']['id'],
                                                        'if_name' : gs_if_name,
                                                }},
                                            ]
                                        })

                merged_yaml = merge_yaml_files(
                    out_cm_data
                )
                bp_out_cm_dir = os.path.join(output_cabling_map_path, bp_name)
                if not os.path.exists(bp_out_cm_dir):
                    os.makedirs(bp_out_cm_dir)
                output_file = os.path.join(bp_out_cm_dir, f'out_cm_{bp_name}.yml')
                create_output_file(merged_yaml, output_file)

                rprint(f"Updated Cabling Map: {output_file}")
                bps_with_updated_cabling_map.append(bp_name)
            else:
                rprint(f"No need to update Cabling Map for blueprint {bp_name}")
        return bps_with_updated_cabling_map
    except FileNotFoundError as e:
        logger.error("An error occurred while retrieving original Cabling Maps: %s", e)
    except yaml.YAMLError as e:
        logger.error("Error decoding YAML file: %s", e)
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)

def run_pull_cabling_maps_script():
    '''
    Execute the script apstra_pull_cabling_maps.py located in the same directory.
    '''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_directory, "apstra_pull_cabling_maps.py")
    if os.path.exists(script_path):
        os.system(f"python3 {script_path}")
    else:
        logger.error("apstra_pull_cabling_maps.py script not found. Exiting.")
        sys.exit(1)

def run_push_cabling_maps_script(bps_with_updated_cabling_map):
    '''
    Execute the script apstra_push_cabling_maps.py located in the same directory.
    '''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_directory, "apstra_push_cabling_maps.py")
    if os.path.exists(script_path):
        os.system(f"python3 {script_path} '{str(bps_with_updated_cabling_map)}'")
    else:
        logger.error("apstra_push_cabling_maps.py script not found. Exiting.")
        sys.exit(1)

if __name__ == '__main__':

    if "pull_cabling_maps" in sys.argv:
        rprint(f"Executing apstra_pull_cabling_maps.py script.")
        run_pull_cabling_maps_script()
    
    bps_with_updated_cabling_map = update_cabling_maps()
    if "push_cabling_maps" in sys.argv and len(bps_with_updated_cabling_map) > 0:
        rprint(f"Executing apstra_push_cabling_maps.py script.")
        run_push_cabling_maps_script(bps_with_updated_cabling_map)
