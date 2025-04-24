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
    Description:
        Automates the installation of Python packages listed in a YAML file. 
        Uses Jinja2 templating to generate a `pip install` command dynamically.
    
    Library Pre-requirements:
        - PyYAML: for parsing YAML files.
        - Jinja2: for templating and generating installation commands.
    
    Install dependencies using:
        pip install pyyaml jinja2
'''

import yaml
from jinja2 import Environment, FileSystemLoader
import subprocess

# Define file names as variables for better maintainability
yaml_file = 'requirements.yaml'
template_file = 'docker_install_requirements.j2'

# Load YAML data
with open(yaml_file) as f:
    data = yaml.safe_load(f)

# Load Jinja2 template
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template(template_file)

# Render template with data
output = template.render(libraries=data['libraries'])

# Print the output for debugging
# print("Generated pip install command:")
# print(output)

# Execute the pip install command
try:
    subprocess.run(output, shell=True, check=True)
    print("Installation completed successfully.")
except subprocess.CalledProcessError as e:
    print(f"An error occurred during installation: {e}")
