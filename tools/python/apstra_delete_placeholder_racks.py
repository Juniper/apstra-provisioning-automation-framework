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
    Description: This script deletes the placeholder racks from each blueprint.
'''

# ---------------------------------------------------------------------------- #
#                                    Imports                                   #
# ---------------------------------------------------------------------------- #
from utils import *

# ---------------------------------------------------------------------------- #
#                                   Functions                                  #
# ---------------------------------------------------------------------------- #

def delete_racks(racks_by_blueprint):
    """
    Deletes specified racks from each blueprint.

    Args:
        racks_by_blueprint (dict): A dictionary where blueprint names are keys
                                   and lists of rack names to delete are values.
    """
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        sm = Scope_Manager()
        bp_list = sm.get('blueprints')

        for bp_name in bp_list:
            if bp_name in racks_by_blueprint:
                racks_to_delete = racks_by_blueprint[bp_name]

                for rack_name in racks_to_delete:
                    rack_id = get_rack_id(bp_name, rack_name)
                    
                    if rack_id:
                        if delete_rack(bp_name, rack_name):
                            logger.info("🗑️  Deleted rack '%s' from blueprint '%s'", rack_name, bp_name)
            else:
                logger.info("ℹ️ No placeholder racks found for blueprint '%s'.", bp_name)

    except Exception as e:
        logger.error("❌ An unexpected error occurred while deleting placeholder racks: %s", e)
        raise


if __name__ == "__main__":
    placeholder_racks = get_placeholder_racks()  # Returns a dictionary

    if placeholder_racks:
        # Format rack names if necessary (modify as per requirement)
        for bp_name in placeholder_racks:
            placeholder_racks[bp_name] = [rack.lower().replace("-", "_") + "_001" for rack in placeholder_racks[bp_name]]

        delete_racks(placeholder_racks)