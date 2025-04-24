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
    Description: This script pulls the Device Model files from Apstra and stores them in YAML format
'''

# ---------------------------------------------------------------------------- #
#                                    Imports                                   #
# ---------------------------------------------------------------------------- #
from utils import *

# ---------------------------------------------------------------------------- #
#                                   Functions                                  #
# ---------------------------------------------------------------------------- #

def get_device_models():
    '''
    Pull Device Model files from Apstra and store them in YAML format.
    '''
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        sm = Scope_Manager()
        blueprints_path = sm.get('blueprints_path')
        blueprints = sm.get('blueprints')
        device_model_path = sm.get('device_model_path')
        if not os.path.exists(device_model_path):
            os.makedirs(device_model_path)
        devices = get_device_info(blueprints, blueprints_path)
        for bp_name in devices:
            bp_dm_dir = os.path.join(device_model_path, bp_name)
            if not os.path.exists(bp_dm_dir):
                os.makedirs(bp_dm_dir)
            for device in devices[bp_name]:
                bp_device_hostname = devices[bp_name][device]['bp_device_hostname']
                device_key = devices[bp_name][device]['device_key']
                if not bp_device_hostname or not device_key:
                    logger.warning("Missing hostname or device key for device %s in blueprint %s", device, bp_name)
                    continue
                dm_filename = f"{bp_device_hostname}.yml"
                bp_dm_path = os.path.join(bp_dm_dir, dm_filename)
                dm_dict = get_dev_model(device_key)
                json_data = json.loads(dm_dict)
                yaml_data = yaml.safe_dump(json_data, default_flow_style=False)
                create_output_file(yaml_data, bp_dm_path)
                logger.info("Device Model downloaded from Apstra: %s", bp_dm_path)
    except Exception as e:
        logger.error("An error occurred while pulling Device Models: %s", e)

if __name__ == "__main__":
    get_device_models()


