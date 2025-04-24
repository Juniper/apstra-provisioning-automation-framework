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
    Description: This script automates the installation of Terraform. 
    It reads the version number from an external YAML file and executes the necessary shell commands
    to install and configure Terraform.

    Library Pre-requirements:
    - PyYAML: for parsing YAML files.
    - subprocess: for executing shell commands within the container.

    Installation of dependencies can be done using:
    pip install pyyaml
'''

import subprocess
import yaml

# Define file names as variables for better maintainability
yaml_file = 'requirements.yaml'

# Load the version from the YAML file
try:
    with open(yaml_file) as f:
        data = yaml.safe_load(f)
    terraform_version = data['terraform_version']
except FileNotFoundError:
    print(f"Error: {yaml_file} not found.")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error parsing YAML file: {e}")
    sys.exit(1)

# List of commands to execute
commands = [
    f"curl -sO https://releases.hashicorp.com/terraform/{terraform_version}/terraform_{terraform_version}_linux_amd64.zip",
    f"unzip terraform_{terraform_version}_linux_amd64.zip",
    "mv terraform /usr/bin",
    f"rm terraform_{terraform_version}_linux_amd64.zip"
]

# Execute each command in order
for i, command in enumerate(commands, start=1):
    print(f"Step {i}: Executing -> {command}")
    subprocess.run(command, shell=True, check=True)
    print(f"Step {i}: Completed.\n{'-'*40}")