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
    Description: This script updates IP addressing of external links.
'''

# ---------------------------------------------------------------------------- #
#                                    Imports                                   #
# ---------------------------------------------------------------------------- #
from utils import *

# ---------------------------------------------------------------------------- #
#                                   Functions                                  #
# ---------------------------------------------------------------------------- #


def update_external_links():
    '''
    Update IP addressing of external links
    '''
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        sm = Scope_Manager()
        blueprints_path = sm.get('blueprints_path')
        blueprints = sm.get('blueprints')

        for bp_name in blueprints:
            subinterfaces = get_subinterfaces(bp_name)['subinterfaces']
            bp_data = yamldecode(os.path.join(blueprints_path, f'{bp_name}.yml'))
            for ct in bp_data.get('connectivity_templates', []):
                for primitive in ct.get('primitives', []):
                    if primitive.get('type', None) == 'ip_link':
                        if 'links' in primitive.get('data', None):
                            vrf = primitive.get('data', {}).get('vrf', None)
                            vlan_id = primitive.get('data', {}).get('vlan_id', None)
                            for link in primitive['data']['links']:
                                if 'endpoint_1' in link:
                                    hostname_1 = link['endpoint_1'].get('hostname', None)
                                    if_name_1 = link['endpoint_1'].get('if_name', None)
                                    ipv4_addr_1 = link['endpoint_1'].get('ipv4_addr', None)
                                if 'endpoint_2' in link:
                                    hostname_2 = link['endpoint_2'].get('hostname', None)
                                    if_name_2 = link['endpoint_2'].get('if_name', None)
                                    ipv4_addr_2 = link['endpoint_2'].get('ipv4_addr', None)
                                for subif in subinterfaces:
                                    # Find the subinterfaces with a certain vlan ID, RZ name and endpoint hostnames
                                    if (subif.get('sz_label', None) == vrf or (subif.get('sz_label', None) == 'Default routing zone' and vrf == 'default')) and subif.get('vlan_id', None) == vlan_id and hostname_1 in subif.get('link_id', None) and hostname_2 in subif.get('link_id', None):
                                        if if_name_1 != None or if_name_2 != None and len(subif.get('endpoints', [])) == 2:
                                            interfaces_match = True
                                            # Find the subinterfaces belonging to certain port names
                                            for endpoint in subif.get('endpoints', []):
                                                if endpoint.get('system', None).get('label', None) == hostname_1 and if_name_1 != None:
                                                    if not endpoint.get('interface', None).get('if_name', None) == if_name_1:
                                                        interfaces_match = False
                                                if endpoint.get('system', None).get('label', None) == hostname_2 and if_name_2 != None:
                                                    if not endpoint.get('interface', None).get('if_name', None) == if_name_2:
                                                        interfaces_match = False
                                            if interfaces_match:
                                                if subif.get('endpoints', [])[0].get('system', None).get('label', None) == hostname_1 and subif.get('endpoints', [])[1].get('system', None).get('label', None) == hostname_2:
                                                    endpoint_1_id = subif.get('endpoints', [])[0].get('subinterface', None).get('id', None)
                                                    endpoint_1_if_name = subif.get('endpoints', [])[0].get('subinterface', None).get('if_name', None)
                                                    endpoint_2_id = subif.get('endpoints', [])[1].get('subinterface', None).get('id', None)
                                                    endpoint_2_if_name = subif.get('endpoints', [])[1].get('subinterface', None).get('if_name', None)
                                                elif subif.get('endpoints', [])[1].get('system', None).get('label', None) == hostname_1 and subif.get('endpoints', [])[0].get('system', None).get('label', None) == hostname_2:
                                                    endpoint_1_id = subif.get('endpoints', [])[1].get('subinterface', None).get('id', None)
                                                    endpoint_1_if_name = subif.get('endpoints', [])[1].get('subinterface', None).get('if_name', None)
                                                    endpoint_2_id = subif.get('endpoints', [])[0].get('subinterface', None).get('id', None)
                                                    endpoint_2_if_name = subif.get('endpoints', [])[0].get('subinterface', None).get('if_name', None)
                                                
                                                ip_dict = {
                                                    endpoint_1_id : { 'ipv4_addr' : ipv4_addr_1 },
                                                    endpoint_2_id : { 'ipv4_addr' : ipv4_addr_2 },
                                                }
                                                try:
                                                    if update_subinterfaces(bp_name, ip_dict):
                                                        rprint(f"Updated IP address in blueprint '{bp_name}': '{hostname_1}' '{endpoint_1_if_name}' set to [bold magenta]'{ipv4_addr_1}'")
                                                        rprint(f"Updated IP address in blueprint '{bp_name}': '{hostname_2}' '{endpoint_2_if_name}' set to [bold magenta]'{ipv4_addr_2}'")
                                                    else:
                                                        logger.error("Failed to update IP address in blueprint '%s': '%s' '%s' ('%s') - '%s' '%s' ('%s')", bp_name, hostname_1, endpoint_1_if_name, ipv4_addr_1, hostname_2, endpoint_2_if_name, ipv4_addr_2)
                                                except Exception as e:
                                                    logger.error("An unexpected error occurred while deleting rack '%s' from blueprint '%s': %s", rack_name, bp_name, e)
    except Exception as e:
        logger.error("An unexpected error occurred while updating external link IP addressing: %s", e)
        raise

if __name__ == "__main__":
    update_external_links()