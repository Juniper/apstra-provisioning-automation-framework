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
    Description: This script uploads the Cabling Map YAML files to Apstra.
'''

# ---------------------------------------------------------------------------- #
#                                    Imports                                   #
# ---------------------------------------------------------------------------- #
from utils import *

# ---------------------------------------------------------------------------- #
#                                   Functions                                  #
# ---------------------------------------------------------------------------- #

def upload_cabling_maps(blueprints, output_cabling_map_path):
    '''
    Upload Cabling Map files to Apstra.
    '''
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        for bp_name in blueprints:
            bp_cm_dir = os.path.join(output_cabling_map_path,bp_name)
            cm_filename = f"out_cm_{bp_name}.yml"
            # Check if the Cabling Map YAML file exists
            if cm_filename not in os.listdir(bp_cm_dir):
                raise FileNotFoundError(f"No Cabling Map found in the expected location: {cm_filename}")
            
            # Overwrite / Create JSON file from YAML file
            yaml_filename = os.path.join(bp_cm_dir, cm_filename)
            json_filename = os.path.join(bp_cm_dir, f"{bp_name}.json")
            if not yaml2json(yaml_filename, json_filename):
                raise RuntimeError("Failed to convert YAML to JSON.")
            
            # Read JSON file
            with open(json_filename, 'r') as f:
                cm_json = f.read()
            time.sleep(1)
            
            # Upload Cabling Map to Apstra
            if (upload_cabling_map(bp_name, cm_json)):
                rprint(f"Cabling Map uploaded to Apstra: {yaml_filename}")
            else:
                raise RuntimeError("Failed to upload Cabling Map to Apstra.")
            
            # Delete JSON file
            os.remove(json_filename)
    
    except FileNotFoundError as e:
        logger.error("An error occurred while uploading Cabling Maps: %s", e)
    except RuntimeError as e:
        logger.error("An error occurred while uploading Cabling Maps: %s", e)
    except Exception as e:
        logger.error("An unexpected error occurred while uploading Cabling Maps: %s", e)

if __name__ == "__main__":
    sm = Scope_Manager()
    output_cabling_map_path = sm.get('wip_execution_0_cabling_map_path')
    if len(sys.argv) == 2:
        blueprints = sys.argv[1].strip('[]').split(', ')
        if isinstance(blueprints, list):
            upload_cabling_maps(blueprints, output_cabling_map_path)
    elif len(sys.argv) == 1:
        upload_cabling_maps(sm.get('blueprints'), output_cabling_map_path)
