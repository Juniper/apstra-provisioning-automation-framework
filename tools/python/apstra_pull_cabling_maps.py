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
    Description: This script pulls the Cabling Map files from Apstra and stores them in YAML format
'''

# ---------------------------------------------------------------------------- #
#                                    Imports                                   #
# ---------------------------------------------------------------------------- #
from utils import *

# ---------------------------------------------------------------------------- #
#                                   Functions                                  #
# ---------------------------------------------------------------------------- #

def get_cabling_maps():
    '''
    Pull Cabling Map files from Apstra and store them in YAML format.
    '''
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        sm = Scope_Manager()
        input_cabling_map_path = sm.get('wip_execution_0_cabling_map_path')
        blueprints = sm.get('blueprints')
        if not os.path.exists(input_cabling_map_path):
            os.makedirs(input_cabling_map_path)
        for bp_name in blueprints:
            bp_cm_dir = os.path.join(input_cabling_map_path, bp_name)
            if not os.path.exists(bp_cm_dir):
                os.makedirs(bp_cm_dir)
            cm_filename = f"in_cm_{bp_name}.yml"
            bp_cm_path = os.path.join(bp_cm_dir, cm_filename)
            cm_dict = get_cabling_map(bp_name)
            json_data = json.loads(cm_dict)
            yaml_data = yaml.safe_dump(json_data, default_flow_style=False)
            create_output_file(yaml_data, bp_cm_path)
            rprint(f"Cabling Map downloaded from Apstra: {bp_cm_path}")

    except Exception as e:
        logger.error("An error occurred while pulling Cabling Maps: %s", e)

if __name__ == "__main__":
    get_cabling_maps()


