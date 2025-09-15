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
    Description: This script serves as a utility module containing a variety of Python imports and functions designed to facilitate common tasks and operations in other scripts.

    Dependencies:
    - The script requires Python 3.7 or later.
    - Ensure the necessary Python modules are installed.
    - Ensure the necessary files containing necessary configuration variables exist in their proper locations.
'''

# ---------------------------------------------------------------------------- #
#                                    Imports                                   #
# ---------------------------------------------------------------------------- #
import os
import re
import argparse
import yaml
import sys
import requests
import logging
import urllib3
import json
import difflib
import ipaddress
import shutil
import tarfile
import tempfile
import time
import subprocess
import hashlib
import csv
import pty
import shlex

# from tf import *
from collections.abc import Mapping, Iterable
from datetime import datetime, timezone
from deepdiff import DeepDiff

import rich.repr
from rich import print as rprint
from rich.logging import RichHandler
from rich.pretty import Pretty
from rich.panel import Panel
from rich.console import Console
from rich.prompt import Prompt
from rich.prompt import Confirm
from rich.table import Table, Column
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.syntax import Syntax

from pprint import pprint

from aos.client import AosClient
from aos.design import AosConfiglets
from aos.design import AosPropertySets

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# def yamldecode(file_path):
#     '''
#     Decode a YAML file and return its contents as a dictionary.

#     Args:
#         file_path (str): Path to the YAML file.

#     Returns:
#         dict: Contents of the YAML file as a dictionary.
#     '''
#     with open(file_path, 'r') as file:
#         return yaml.safe_load(file)


# ---------------------------------------------------------------------------- #
#                                    Classes                                   #
# ---------------------------------------------------------------------------- #
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

class Tee:
    '''
    A class to duplicate stdout/stderr output to both console and a file.
    '''
    def __init__(self, file_path):
        self.file = open(file_path, "w", encoding="utf-8", buffering=1)
        self.original_stdout = sys.stdout
        sys.stdout = self  # Redirect sys.stdout to this instance
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.file.write(f"\n{'=' * 22} NEW EXECUTION {'=' * 23}\n")
        self.file.write(f"{'=' * 10} Logging Started at {now} {'=' * 10}\n")
        self.file.flush()
        os.fsync(self.file.fileno())  # Force OS to write data

    def write(self, data):
        clean_data = remove_ansi_escape_sequences(data)
        self.original_stdout.write(data)
        self.original_stdout.flush()
        self.file.write(clean_data)
        self.file.flush()
        os.fsync(self.file.fileno())  # Ensure immediate disk write

    def flush(self):
        self.original_stdout.flush()
        if not self.file.closed:
            self.file.flush()
            os.fsync(self.file.fileno())  # Force filesystem sync

    def close(self):
        sys.stdout = self.original_stdout  # Restore original stdout
        self.file.close()

    def __del__(self):
        try:
            self.close()
        except Exception as e:
            print(f"Exception ignored in __del__: {e}", file=sys.__stderr__)

    def __enter__(self):
        return self  # Allow use with `with` statement

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

class Scope_Manager:

    def __init__(self, terraform_command='no_command', new_scope=None):
        '''
        Initialize all scope parameters to '-', update them with values from the global scope file (it is a global variable defined in utils.py),
        then update them with values passed as input arguments to the script, and finally update file paths based on the updated scope parameters.

        Args:
            terraform_command (str, optional): The Terraform command to be executed. Defaults to 'no_command'.
            new_scope (dict, optional): The new scope information made up of input arguments. Defaults to None.
        '''

        # 1/4 - Initialize all scope parameters to '-'
        self.initialize_vars(terraform_command)

        # 2/4 - Update them with values from the global scope file (it is a global variable defined in utils.py)
        scope = yamldecode(scope_file_path)
        if scope:
            self.update_vars(scope)

        # 3/4 - Update them with values passed as input arguments to the script and update file paths based on the updated scope parameters.
        if new_scope is not None:
            self.update_vars(new_scope)
        else:
            self.update_vars(scope)

        # 3/4 - Update the terraform command and the scope file with the value passed as an input argument to the script if it does not match the previous value.
        if terraform_command != self.terraform_command:
            self.terraform_command = terraform_command
            self.update_vars({'terraform_command' : terraform_command})

    def initialize_vars(self, terraform_command):
        '''
        Initialize all scope parameters to '-'.

        Args:
            terraform_command (str): The Terraform command to be executed.
        '''

        self.terraform_command = terraform_command
        self.aos_target = '-'
        self.customer = '-'
        self.domain = '-'
        self.project = '-'
        self.pre_commit_action = '-'
        self.pre_commit_comment = '-'
        self.post_commit_action = '-'
        self.post_commit_comment = '-'
        self.exit_code = 'INIT'
        self.post_rollback = False
        self.first_execution_reverted = False
        self.interactive = True

    def get_aos_token (self):
        '''
        Authenticate with the AOS API and retrieve the authentication token.

        '''
        try:
            aos_ip = self.get('aos_ip')
            aos_username = self.get('aos_username')
            aos_password = self.get('aos_password')
            url = f'https://{aos_ip}/api/user/login'
            data = json.dumps({"username": aos_username, "password": aos_password})
            headers = {'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
            response = requests.post(url, data=data, headers=headers, verify=False)
            response.raise_for_status()
            self.aos_token = response.json()['token']
        except Exception as e:
            logger.error(f'❌ Error: Authentication failed - {e}')

    def get_project_execution_history(self):
        '''
        Retrieves the execution history for a specific project.

        Returns:
            list: Execution history data if available, otherwise None.
        '''
        try:
            execution_data = generate_execution_history(
                all_customers=False, customer=self.customer, domain=self.domain, project=self.project
            )

            if execution_data:
                return execution_data

            # logger.warning(f"❌ No execution history found for project '{self.project}' in domain '{self.domain}' (Customer: {self.customer}).")
            return None

        except Exception as e:
            logger.error(f"❌ Error retrieving execution history for project '{self.project}': {e}")
            return None

    def get_project_rollback_history(self):
        '''
        Filters and sorts the project execution history by 'execution_id' in descending order.
        Excludes any executions with invalid exit codes and saves the filtered and sorted list
        to self.project_execution_history_for_rollback.

        This function assumes that self.project_execution_history is a list of dictionaries, where each dictionary
        contains execution data with necessary fields like 'execution_id', 'exit_code', etc.
        '''

        try:

            # If no execution history is available, set an empty list
            if not hasattr(self, 'project_execution_history') or not self.project_execution_history:
                self.project_execution_history_for_rollback = []
                return

            # Retrieve the execution history of this project from the object attribute (expected to be a list of dictionaries)
            project_execution_history = self.project_execution_history

            # Filter executions with valid exit_code (must be in the list of successful exit codes)
            # and exclude the current execution ID
            filtered_executions = [
                execution for execution in project_execution_history
                if execution.get('exit_code') in list_successful_exit_codes and execution.get('execution_id') != self.execution_id
            ]

            # Sort the filtered executions by 'execution_id' in descending order (assuming it's a string)
            sorted_filtered_executions = sorted(
                filtered_executions,
                key=lambda execution: execution.get('execution_id', ''),
                reverse=True
            )

            # Save the sorted and filtered executions to the attribute for rollback
            self.project_execution_history_for_rollback = sorted_filtered_executions

        except Exception as e:
            logger.error(f"❌ Error in get_project_rollback_history: {e}")
            self.project_execution_history_for_rollback = []

    def print_project_rollback_history(self):
        '''
        Prints the filtered and sorted project execution history for rollback,
        with an added column 'id' (1, 2, 3, ...) for each execution.

        This function uses the rich library to display a table with clear formatting
        for the user to easily identify each execution.
        Returns:
            int: Number of executions displayed in the table.
        '''

        try:
            # Retrieve the project execution history for rollback (list of dictionaries)
            execution_history = self.project_execution_history_for_rollback

            # If no execution history is available, print a message and return
            if not execution_history:
                logger.info("No valid executions found for rollback.")
                return 0

            # Create a Table object
            table = Table(
                title="PROJECT EXECUTION HISTORY",
                box=box.HEAVY_EDGE,
            )
            table.show_header = True
            table.title_justify = "center"
            table.title_style = "cyan underline"

            # Add the ID column
            table.add_column(header="ID", justify="center", style="cyan")

            # Add the relevant execution history columns
            for column in list_execution_history_relevant_fields:
                table.add_column(header=column, justify="center", style="magenta")

            # Add rows to the table
            for idx, execution in enumerate(execution_history, start=1):
                # Include the ID column and fill in the row with values from the execution
                # row = [str(idx)] + [execution.get(col, "-") for col in columns]
                row = [str(idx)] + [execution.get(col, "-") for col in list_execution_history_relevant_fields]
                table.add_row(*row)

            # Print the table
            print("\n")
            print_panel_deploy_handling_plan(table, "ROLLBACK")

            return idx  # Return the number of executions displayed

        except Exception as e:
            logger.error(f"❌ Error in print_project_rollback_history: {e}")
            return 0  # Return 0 in case of an error

    def prompt_rollback_execution_choice(self, number_of_executions: int) -> int:
        '''
        Prompts the user to select an execution ID for rollback.

        Displays a message indicating the rollback process, then continuously prompts
        the user until a valid numeric choice within the range (1 to number_of_executions) is entered.

        Args:
            number_of_executions (int): The total number of available executions for rollback.

        Returns:
            int: The selected execution ID (1-based index).
        '''
        try:
            print("\n")
            logger.info(
                '⏪ Rolling back to a previous execution.\n'
                'The table above lists all available executions for rollback.\n'
            )

            while True:
                try:
                    # Prompt user input
                    choice = int(input('🔢 Please enter the ID number (first column) of the execution you want to restore: '))

                    # Validate input range
                    if 1 <= choice <= number_of_executions:
                        return choice
                    else:
                        logger.error(
                            f'❌ Invalid selection: {choice}. Please enter a valid ID from the table between 1 and {number_of_executions}.'
                        )

                except ValueError:
                    logger.error('❌ Invalid input. Please enter a number.')

        except Exception as e:
            logger.error(f"❌ Error in prompt_rollback_execution_choice: {e}")
            return -1  # Return an invalid choice in case of an unexpected failure

    def get_rollback_execution_choice(self, choice):
        '''
        Retrieves the execution corresponding to the user's choice, finds its associated folder,
        and updates a set of rollback-related variables for later use.

        Args:
            choice (int or str): The ID selected by the user (1-based index) or "last" for the most recent execution.

        Updates:
            self.rollback_data (dict or None): The selected execution dictionary if valid, else None.
            self.first_execution_reverted (bool): True if no previous executions in the project. False otherwise.
            self.wip_execution_rollback_path (str or None): The path to the rollback execution folder if found, else None.
            self.wip_execution_rollback_yaml_path (str or None): Path to the YAML subfolder within the rollback folder.
            self.wip_execution_rollback_tfstate_path (str or None): Path to the Terraform state subfolder.
            self.wip_execution_rollback_tfstate_file (str or None): Full path to the project's Terraform state file.
            self.wip_execution_rollback_input_tgz_file (str or None): Full path to the input.tgz file.
        '''
        try:

            number_of_executions = len(self.project_execution_history_for_rollback)

            # -- Initialize rollback execution folder paths
            self.wip_execution_rollback_path = None
            self.wip_execution_rollback_yaml_path = None
            self.wip_execution_rollback_tfstate_path = None
            self.wip_execution_rollback_tfstate_file = None
            self.wip_execution_rollback_input_tgz_file = None
            self.rollback_data = None
            self.first_execution_reverted = False

            # -- Convert "last" to choice = 1 (most recent execution)
            if choice == "last":
                if number_of_executions == 0:
                    self.first_execution_reverted = True
                    return
                else:
                    choice = 1

            # -- Validate that the selected choice is within the valid range
            if not isinstance(choice, int) or not (1 <= choice <= number_of_executions):
                logger.error(f"❌ Invalid selection: {choice}. Please enter a valid ID from the table between 1 and {number_of_executions}, or 'last'.")
                return

            # -- Retrieve and store the selected execution (list is 0-based, choice is 1-based)
            self.rollback_data = self.project_execution_history_for_rollback[choice - 1]
            rollback_execution_id = self.rollback_data["execution_id"]
            print("\n")
            logger.info(f"🆔 APAF Execution ID for rollback: {rollback_execution_id}")
            logger.info(f"Created on 📅 {self.rollback_data['local_creation_date']} at ⏰ {self.rollback_data['local_creation_time']}\n")


            # -- Search for the folder containing the matching execution_id
            for root, dirs, files in os.walk(self.wip_path):
                if execution_data_filename in files:
                    execution_file_path = os.path.join(root, execution_data_filename)

                    try:
                        # -- Read the YAML execution file
                        with open(execution_file_path, "r", encoding="utf-8") as file:
                            execution_data = yaml.safe_load(file)

                        # -- Check if execution_id matches the selected rollback execution
                        if execution_data.get("execution_id") == rollback_execution_id:
                            self.wip_execution_rollback_path = root
                            self.wip_execution_rollback_yaml_path = os.path.join(root, "yaml")
                            self.wip_execution_rollback_tfstate_path = os.path.join(root, "tfstate")
                            self.wip_execution_rollback_tfstate_file = os.path.join(self.wip_execution_rollback_tfstate_path, f"{self.project}.tfstate")
                            self.wip_execution_rollback_input_tgz_file = os.path.join(self.wip_execution_rollback_yaml_path, "input.tgz")
                            logger.info(f"📂 Rollback execution folder in {self.wip_path}: {root}")
                            break  # -- Stop searching once found

                    except Exception as e:
                        logger.error(f"❌ Error reading {execution_file_path}: {e}")
                        self.wip_execution_rollback_path = None
                        self.wip_execution_rollback_yaml_path = None
                        self.wip_execution_rollback_tfstate_path = None
                        self.wip_execution_rollback_tfstate_file = None
                        self.wip_execution_rollback_input_tgz_file = None

            # -- Warn if no matching execution folder was found
            if not self.wip_execution_rollback_path:
                logger.warning(f"❌ No matching execution folder found for the selected rollback execution_id: {rollback_execution_id}")
                self.wip_execution_rollback_path = None
                self.wip_execution_rollback_yaml_path = None
                self.wip_execution_rollback_tfstate_path = None
                self.wip_execution_rollback_tfstate_file = None
                self.wip_execution_rollback_input_tgz_file = None

        except Exception as e:
            logger.error(f"❌ Error in get_rollback_execution_choice: {e}")

    def update_vars(self, new_scope, update_execution_data_file=False):
        '''
        Update the scope with new scope information.

        Args:
            new_scope (dict): The new scope information.
            update_execution_data_file (bool): Whether to update the execution_data file with the updated vars or not.

        Returns:
            None
        '''
        try:
            for var, new_value in new_scope.items():
                if hasattr(self, var):
                    setattr(self, var, new_value)

            self.update_paths()

            self.get_aos_token()

            self.update_scope_file(update_execution_data_file)

        except Exception as e:
            logger.error(f"❌ Error updating scope variables: {e}")

    def update_paths(self):
        '''
        Update file paths based on the current scope parameters.
        '''
        try:

            # Use the appropriate file paths based on the updated scope parameters

            self.customer_path = os.path.join(customers_path, self.customer)
            self.customers_list = get_direct_subdirectories(customers_path)
            if self.align_customer():
                self.customer_path = os.path.join(customers_path, self.customer)
                self.customers_list = get_direct_subdirectories(customers_path)

            self.domains_path = os.path.join(self.customer_path, "domains")
            self.domain_path = os.path.join(self.domains_path, self.domain)
            self.domains_list = get_direct_subdirectories(self.domains_path)
            if self.align_domain():
                self.domains_path = os.path.join(self.customer_path, "domains")
                self.domain_path = os.path.join(self.domains_path, self.domain)
                self.domains_list = get_direct_subdirectories(self.domains_path)

            self.projects_path = os.path.join(self.domain_path, "projects")
            self.project_path = os.path.join(self.projects_path, self.project)
            self.projects_list = get_direct_subdirectories(self.projects_path)
            if self.align_project():
                self.projects_path = os.path.join(self.domain_path, "projects")
                self.project_path = os.path.join(self.projects_path, self.project)
                self.projects_list = get_direct_subdirectories(self.projects_path)

            self.input_path = os.path.join(self.project_path, "input")
            self.output_path = os.path.join(self.project_path, "output")

            self.files = yamldecode(os.path.join(self.input_path, "_main", "files.yml"))
            
            self.parent_projects_path = os.path.join(self.input_path, self.files["parent_projects"]["directory"])
            self.parent_projects_filename = os.path.join(self.parent_projects_path, self.files["parent_projects"]["filename"])
            
            self.parent_projects_list = []  # Initialize with an empty list if the key doesn't exist
            if os.path.exists(self.parent_projects_filename):
                self.parent_projects_dict = yamldecode(self.parent_projects_filename)
                if "parent_projects" in self.parent_projects_dict:
                    self.parent_projects_list = self.parent_projects_dict["parent_projects"]
            
            self.archive_dir = os.path.join(self.output_path, self.files["archive"]["directory"])

            self.executions_dir = os.path.join(self.output_path, self.files["executions"]["directory"])

            self.input_tgz_reverted_path = os.path.join(self.output_path, self.files["input_tgz_reverted_path"]["directory"])
            self.input_tgz_reverted_file = os.path.join(self.input_tgz_reverted_path, self.files["input_tgz_reverted_path"]["filename"])

            self.project_log_path = os.path.join(self.output_path, self.files["project_log"]["directory"])
            self.project_log_file = os.path.join(self.project_log_path, self.files["project_log"]["filename"])

            self.snapshot_dir_name = self.files["apstra_snapshot"]["directory"]
            self.apstra_snapshot_path = os.path.join(self.output_path, self.snapshot_dir_name)

            self.execution_0_path = os.path.join(self.executions_dir, "execution_0")
            self.execution_0_log_path = os.path.join(self.execution_0_path, "log")
            self.execution_0_log_file = os.path.join(self.execution_0_log_path, "00_full_execution.log")
            self.execution_0_error_file = os.path.join(self.execution_0_log_path, "00_full_execution_error.log")

            self.blocked_executions_path = os.path.join(self.executions_dir, "__blocked__")

            self.wip_path = os.path.join(self.executions_dir, "__wip__")
            self.wip_log_file = os.path.join(self.wip_path, "full_execution.log")
            self.wip_error_file = os.path.join(self.wip_path, "full_execution_error.log")

            self.wip_execution_0_path = os.path.join(self.wip_path, "execution_0")
            self.wip_execution_0_tfstate_path = os.path.join(self.wip_execution_0_path, "tfstate")
            self.wip_execution_0_tfstate_file = os.path.join(self.wip_execution_0_tfstate_path, f"{self.project}.tfstate")
            self.wip_execution_0_tfstate_rollback_file = os.path.join(self.wip_execution_0_tfstate_path, f"{self.project}.tfstate.rollback")
            self.wip_execution_0_tfstate_reverted_file = os.path.join(self.wip_execution_0_tfstate_path, f"{self.project}.tfstate.reverted")
            self.wip_execution_0_cabling_map_path = os.path.join(self.wip_execution_0_path, "cabling_maps")

            self.wip_execution_0_yaml_path = os.path.join(self.wip_execution_0_path, "yaml")
            self.wip_execution_0_input_tgz_file = os.path.join(self.wip_execution_0_yaml_path, "input.tgz")
            self.wip_execution_0_input_tgz_rollback_file = os.path.join(self.wip_execution_0_yaml_path, "input.tgz.rollback")
            self.wip_execution_0_input_tgz_reverted_file = os.path.join(self.wip_execution_0_yaml_path, "input.tgz.reverted")
            self.wip_execution_0_snapshot_path = os.path.join(self.wip_execution_0_path, self.snapshot_dir_name)
            self.wip_execution_0_log_path = os.path.join(self.wip_execution_0_path, "log")

            self.wip_execution_0_tfplan_path = os.path.join(self.wip_execution_0_path, "tfplan")

            self.wip_execution_0_tfplan_file_bin = os.path.join(self.wip_execution_0_tfplan_path, 'tfplan.bin')
            self.wip_execution_0_tfplan_file_txt = os.path.join(self.wip_execution_0_tfplan_path, 'tfplan.txt')
            self.wip_execution_0_tfplan_file_json = os.path.join(self.wip_execution_0_tfplan_path, 'tfplan.json')
            self.wip_execution_0_tfplan_file_summary = os.path.join(self.wip_execution_0_tfplan_path, 'tfplan_summary.txt')

            self.wip_execution_0_tfplan_generation_log = os.path.join(self.wip_execution_0_log_path, '01_tfplan_generation.log')
            self.wip_execution_0_tfplan_generation_error = os.path.join(self.wip_execution_0_log_path, '01_tfplan_generation_error.log')

            self.wip_execution_0_tfplan_all_log = os.path.join(self.wip_execution_0_log_path, "tfplan_execution_all.log")
            self.wip_execution_0_tfplan_log = os.path.join(self.wip_execution_0_log_path, "02_tfplan_execution.log")
            self.wip_execution_0_tfplan_output = os.path.join(self.wip_execution_0_log_path, "02_tfplan_execution_output.log")
            self.wip_execution_0_tfplan_error = os.path.join(self.wip_execution_0_log_path, "02_tfplan_execution_error.log")

            self.wip_execution_0_tfplan_generation_log_rollback = os.path.join(self.wip_execution_0_log_path, '03_rollback_tfplan_generation.log')
            self.wip_execution_0_tfplan_generation_error_rollback = os.path.join(self.wip_execution_0_log_path, '03_rollback_tfplan_generation_error.log')

            self.wip_execution_1_path = os.path.join(self.wip_path, "execution_1")
            self.wip_execution_1_yaml_path = os.path.join(self.wip_execution_1_path, "yaml")
            self.wip_execution_1_tfstate_path = os.path.join(self.wip_execution_1_path, "tfstate")
            self.wip_execution_1_tfstate_file = os.path.join(self.wip_execution_1_tfstate_path, f"{self.project}.tfstate")
            self.wip_execution_1_input_tgz_file = os.path.join(self.wip_execution_1_yaml_path, "input.tgz")

            self.wip_execution_data_path = self.wip_execution_0_path

            self.aos_data = yamldecode(os.path.join(self.domain_path, self.files["credentials"]["directory"], self.files["credentials"]["filename"]))
            self.aos_targets_list = [item['target'] for item in self.aos_data['aos']]
            if self.align_aos_target():
                self.aos_data = yamldecode(os.path.join(self.domain_path, self.files["credentials"]["directory"], self.files["credentials"]["filename"]))
                self.aos_targets_list = [item['target'] for item in self.aos_data['aos']]
            self.aos_ip, self.aos_username, self.aos_password = get_aos_variables(self.aos_data, self.aos_target)

            self.blueprints_path = os.path.join(self.input_path, self.files["blueprints"]["directory"])
            self.blueprints_filename = self.files["blueprints"]["filename"]
            self.blueprints = yamldecode(os.path.join(self.blueprints_path, self.blueprints_filename)).get('blueprints', [])

            self.design_path = os.path.join(self.input_path, self.files["design"]["directory"])
            self.design_filename = self.files["design"]["filename"]

        except Exception as e:
            logger.error(f"❌ Error updating paths: {e}")

    def update_scope_file(self, update_execution_data_file=False):
        '''
        Update the scope file with new scope information.

        Returns:
            None
        '''
        try:
            # scope_file_path = os.path.join(scope_path, scope_filename)
            if os.path.exists(scope_file_path):
                with open(scope_file_path, 'r') as file:            # Load the YAML data from the file
                    scope_data = yaml.safe_load(file)
                    scope_data['aos_target'] = self.aos_target
                    scope_data['customer'] = self.customer
                    scope_data['domain'] = self.domain
                    scope_data['project'] = self.project
                    scope_data['pre_commit_action'] = self.pre_commit_action
                    scope_data['pre_commit_comment'] = self.pre_commit_comment
                    scope_data['post_commit_action'] = self.post_commit_action
                    scope_data['post_commit_comment'] = self.post_commit_comment
                    scope_data['post_rollback'] = self.post_rollback
                    scope_data['interactive'] = self.interactive
                    scope_data['first_execution_reverted'] = self.first_execution_reverted
                    scope_data['terraform_command'] = self.terraform_command
                with open(scope_file_path, 'w') as file:
                    yaml.dump(scope_data, file)
                # logger.info("Scope file updated successfully.")
                if update_execution_data_file == True:
                    self.handle_execution_data_file("update", scope_data)
            else:
                logger.info("Scope file does not exist.")
        except Exception as e:
            logger.error(f"❌ Error updating scope file '{scope_file_path}': {e}")

    def blocked_executions(self):
        '''
        Checks if the executions are blocked by the existence of a particular directory.
        If it does, warns the user that unresolved issues persist and blocks new executions.
        The user is prompted to confirm if the issues are resolved and remove the directory.

        Returns:
            bool: True if executions remain blocked (directory exists and was not removed),
              False if the directory is removed or does not exist.
        '''

        try:
            directory_path = self.get('blocked_executions_path')

            if not directory_path:
                logger.error("❌ No directory path provided for blocked executions.")
                return True  # Assume blocked as a safeguard

            if not os.path.exists(directory_path):
                return False  # Directory does not exist, no block

            if not os.path.isdir(directory_path):
                logger.error(f"❌ The provided path is not a directory: {directory_path}")
                return True  # Consider executions blocked

            # Directory exists: warn the user and prompt for action
            logger.warning(
                f"❗❗Persistent issues detected! The directory {directory_path} exists, "
                "indicating unresolved errors even after rollback.\n"
                " 🚧 New executions are blocked until these issues are manually reviewed and fixed.\n"
            )
            
            if self.prompt_unblock_executions():
                remove_directory(directory_path)
                return False
            else:
                logger.info(f"🚫 Execution remains blocked. Directory {directory_path} was not removed.")
                return True

        except Exception as e:
            logger.error(f"❌ An error occurred while handling the blocked executions directory: {e}")
            return True

    def handle_execution_data_file(self, action, *dicts):
        '''
        Create, update, or read a YAML file in the specified path directory
        containing relevant data of the execution.

        Args:
            action (str): Either "create", "update", or "read".
            *dicts (dict): Dictionaries to update in the YAML file.
                            Can contain 'scope' dictionary and other data.

        Returns:
            dict | None: Returns the dictionary if action is "read", otherwise None.
        '''

        try:
            yaml_file = os.path.join(self.wip_execution_data_path, execution_data_filename)

            if not os.path.exists(self.wip_execution_data_path):
                os.makedirs(self.wip_execution_data_path)
            if action == "create":

                # Create the next attributes ONLY at this creation stage:
                local_now = datetime.now()
                self.local_creation_date = local_now.strftime("%d/%m/%Y")
                self.local_creation_time = local_now.strftime("%H:%M:%S")

                utc_now = datetime.now(timezone.utc)
                self.utc_creation_date = utc_now.strftime("%d/%m/%Y")
                self.utc_creation_time = utc_now.strftime("%H:%M:%S")
                self.utc_seconds_since_epoch = utc_now.timestamp()

                self.execution_id = f"apaf_id_{int(self.utc_seconds_since_epoch)}"

                self.project_execution_history = self.get_project_execution_history()
                # self.rollback_execution_id = self.get_rollback_execution_id()

                data = {
                    'local_creation_date': self.local_creation_date,
                    'local_creation_time': self.local_creation_time,
                    'utc_creation_date': self.utc_creation_date,
                    'utc_creation_time': self.utc_creation_time,
                    'execution_id': self.execution_id,
                    # 'rollback_execution_id': self.rollback_execution_id,
                    'exit_code': self.exit_code,
                }
                for d in dicts:
                    data.update(d)
                with open(yaml_file, 'w') as file:
                    yaml.dump(data, file)
                print("\n")
                logger.info(f"🆔 Assigned APAF Execution ID: {self.execution_id}")
            elif action == "update":
                update_yaml(yaml_file, *dicts)
            elif action == "read":
                if os.path.exists(yaml_file):
                    with open(yaml_file, 'r') as file:
                        return yaml.safe_load(file) or {}  # Return parsed YAML content or empty dict
                else:
                    logger.error(f"❌ YAML file '{yaml_file}' not found.")
                    return {}
            else:
                raise ValueError(f" ❌ Invalid action: '{action}'. Expected 'create' or 'update'.")
        except FileNotFoundError as e:
            logger.error(f"❌ Error: The path '{self.wip_execution_data_path}' does not exist. {e}")
        except PermissionError as e:
            logger.error(f"❌ Error: Permission denied while accessing '{self.wip_execution_data_path}'. {e}")
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred: {e}")

        return None

    def get(self, attribute, default=None):
        '''
        Get the value of an attribute if it exists, otherwise return the default value.

        Args:
            attribute (str): The attribute name.
            default: The default value to return if the attribute does not exist. Defaults to None.

        Returns:
            The value of the attribute or the default value.
        '''
        return getattr(self, attribute, default)

    def commit_wip_executions(self):
        '''
        Moves all 'execution_*' files from 'wip_path' to 'wip_execution_0_log_path' (if it exists).
        Copies the entire contents of 'wip_path' into a clean version of 'executions_dir'.
        If 'wip_path' is a subdirectory of 'executions_dir', it is safely removed after the copy.

        Returns:
            None
        '''
        try:

            executions_dir = self.get('executions_dir')
            wip_path = self.get('wip_path')
            wip_execution_0_log_path = self.get('wip_execution_0_log_path')

            if not executions_dir or not wip_path:
                raise ValueError("Both 'executions_dir' and 'wip_path' must be specified.")

            # Step 1: Move execution_* files to execution_0 (if it exists)
            if os.path.exists(wip_execution_0_log_path) and os.path.isdir(wip_execution_0_log_path):
                for file_name in os.listdir(wip_path):
                    source = os.path.join(wip_path, file_name)
                    destination = os.path.join(wip_execution_0_log_path, file_name)
                    if file_name.startswith('execution_') and os.path.isfile(source):
                        shutil.move(source, destination)
                        logging.info(f"✅ Moved {file_name} from {wip_path} to {wip_execution_0_log_path}.")
            else:
                logging.warning(f"⚠️ {wip_execution_0_log_path} directory not found. No files moved.")

            # Step 2: If wip_path is inside executions_dir, move it out temporarily
            temp_location = None
            wip_temp_path = None
            wip_inside_executions = os.path.commonpath([executions_dir, wip_path]) == executions_dir

            if wip_inside_executions:
                with tempfile.TemporaryDirectory(dir=os.path.dirname(executions_dir)) as temp_location:

                    wip_temp_path = os.path.join(temp_location, os.path.basename(wip_path))
                    shutil.move(wip_path, temp_location)
                    logging.info(f"✅ Temporarily moved in-progress executions to {temp_location} to avoid deletion.")

                    # Step 3: Clean executions_dir
                    clean_up_directory(executions_dir)

                    # Step 4: Move wip_path back if it was moved
                    shutil.move(wip_temp_path, executions_dir)
                    wip_path = os.path.join(executions_dir, os.path.basename(wip_path))
                    logging.info(f"✅ Moved in-progress executions back to {executions_dir}.")

            else:
                # If wip_path is not inside executions_dir, proceed normally
                # Step 3: Clean executions_dir
                clean_up_directory(executions_dir)

            # Copy all contents from wip_path to executions_dir
            for item in os.listdir(wip_path):
                source = os.path.join(wip_path, item)
                destination = os.path.join(executions_dir, item)

                if os.path.isdir(source):
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)

            logging.info(f"✅ Successfully committed in-progress executions: contents from {wip_path} moved to {executions_dir}.")

        except Exception as e:
            logging.error(f"❌ Failed to commit in-progress executions: {e}")

    def exit_manager(self, exit_code = None):
        '''
        Manages the finalization process before exiting the framework, including cleanup, logging,
        and organizing execution files.

        Args:
            exit_code (str): Identifier for the exit condition, determining the handling process. Defaults to None.
        '''

        # Update the status code
        if exit_code:
            exit_code = exit_code.upper()
            self.exit_code = exit_code

            execution_data_file = os.path.join(self.wip_execution_data_path, execution_data_filename)
            if os.path.exists(execution_data_file):
                self.handle_execution_data_file("update", {'exit_code': exit_code})

            execution_id = self.get("execution_id", "")

            print("\n")  # Blank line for readability

            # Display exit messages
            exit_messages = {
                "USER_SILENT_EXIT": "🤫 Silently exiting without deploying any change to Apstra as requested by the user.\n🌫️  Execution '{execution_id}' vanished without a trace - no clues left behind, no files modified.\n",
                "USER_REVERT": "🔄 Exiting after rolling back the execution as requested by the user.\n📂 Input files rolled back to their previous execution version.\n🌫️  Execution '{execution_id}' vanished without a trace - no clues left behind.\n",
                "TF_PLAN_W_ERRORS": "🔴 Errors encountered during the generation of the Terraform Plan.\n🤫 Silently exiting without deploying any change to Apstra.\n📂 Input files remain unchanged - review them offline.\n🌫️  Execution '{execution_id}' vanished without a trace - no clues left behind, no files modified.\n",
                "TF_PLAN_NO_CHANGES": "🟢 No changes detected in the Terraform Plan.\n🤫 Silently exiting without deploying any change to Apstra.\n🌫️  Execution '{execution_id}' vanished without a trace - no clues left behind, no files modified.\n",
                "TF_PLAN_NO_CHANGES_POST_ROLLBACK": "🟢 No changes detected in the Terraform Plan.\n📝 The post-rollback execution '{execution_id}' has been saved even when no Terraform Plan changes were detected (tfstate remains unaltered from the last saved execution) to ensure a copy of the reverted execution's input folder TGZ is readily available.\n",
                "USER_TF_EXEC_ABORTED": "🤚 Changes detected in the Terraform Plan, but it will be disregarded.\n🤫 Silently exiting without deploying any change to Apstra as requested by the user.\n🌫️  Execution '{execution_id}' vanished without a trace - no clues left behind, no files modified.\n",
                "TF_EXEC_NOT_APPLY_DESTROY": "🤫 Silently exiting without deploying any change to Apstra because neither a Terraform apply nor a Terraform destroy was performed.\n🌫️  Execution '{execution_id}' vanished without a trace - no clues left behind, no files modified.\n",
                "TF_EXEC_W_ERRORS_REVERT": "🔄 Exiting after rolling back the execution to solve the errors encountered during the execution of the Terraform Plan.\n📂 Input files rolled back to their previous execution version.\n🌫️  Execution '{execution_id}' vanished without a trace - no clues left behind.\n",
                "TF_EXEC_W_ERRORS_DESTROY": "🔄 Exiting the 'terraform destroy' execution to solve the errors encountered during the execution of the Terraform Plan.\n📂 Input files rolled back to their previous execution version.\n🌫️  Execution '{execution_id}' vanished without a trace - no clues left behind.\n",
                "USER_TF_EXEC_COMMIT": "🟢 Exiting leaving the changes committed in Apstra.\n💾 The execution '{execution_id}' has been saved.\n",
                "USER_TF_EXEC_DESTROY": "🟢 Finishing the 'terraform destroy' execution.\n💾 The execution '{execution_id}' has been saved.\n",
                "BLOCKED_EXECUTIONS": "🔴 Some errors persist after rolling back to a previous execution.\n🛠️  Please review offline and take the necessary manual actions before launching a new execution.\nExecution '{execution_id}' vanished without a trace - no clues left behind.\n",
            }

            try:
                # Log info upon the exit_code
                if exit_code in exit_messages:
                    logger.info(exit_messages[exit_code].format(execution_id=execution_id))
                    remove_file(self.wip_execution_0_input_tgz_rollback_file)

                    # If this is a post-rollback execution and ends with an error code:
                    if exit_code in {
                        "BLOCKED_EXECUTIONS",
                    }:
                        # Block any new execution until manually solving the issues
                        logger.warning("❗❗Some errors persist even after rolling back to a previous execution.\n🛠️ Please review offline and take the necessary manual actions before launching a new execution.\n")
                        os.makedirs(self.blocked_executions_path, exist_ok=True)
                        copy_file(tmp_exec_log_file, self.blocked_executions_path)

                    # If this is a post-rollback execution that does not end with an error code:
                    elif self.post_rollback:
                        logger.info(
                            f"📦 A copy of the reverted execution's input folder TGZ is available at {self.wip_execution_0_input_tgz_reverted_file} for easy retrieval if needed.\n"
                            f"✅🔄 Rollback process fully completed! Terraform run successfully the post-rollback execution to realign the Apstra deployment.\n"
                        )

                    # Move execution files to final directories only for specific successful exit codes
                    # or if this is a silent exit (no tf plan changes) in a post-rollback execution
                    successful_execution = exit_code in {
                        "USER_TF_EXEC_COMMIT",
                        "USER_TF_EXEC_DESTROY",
                        "TF_PLAN_NO_CHANGES_POST_ROLLBACK"
                    }
                    if successful_execution:
                        # Before leaving, copy back the contents of the "wip" directory to the "executions" folder with all its contents
                        self.commit_wip_executions()
                        # Copy the tmp_exec_log_file and tmp_exec_error_file to the proper location
                        copy_file(tmp_exec_log_file, self.execution_0_log_file)

                    # Remove wip_path
                    remove_directory(self.get('wip_path'))

                    # For the particular case of the Terraform Destroy, archive all the executions in a TGZ before finishing
                    if exit_code in ["USER_TF_EXEC_DESTROY"]:
                        self.manage_execution_dirs('destroy_final_stage')

                    # Farewell message and exit if this is not the rollback stage
                    display_farewell_message(execution_id)

                    # Trigger a follow-up execution for rollback exit codes.
                    if not self.first_execution_reverted and exit_code in {
                        "USER_REVERT",
                        "TF_EXEC_W_ERRORS_REVERT",
                    }:
                        # Append the tmp_exec_log_file to the customer-wide log file.
                        self.handle_project_log()
                        # Remove the "tmp_log" directory
                        remove_directory(tmp_exec_log_path)

                        # Warn about the new execution to be launched
                        print("\n","="*120,"\n")  # Visual separator
                        rprint("\n[bold green]🚀🔄 Launching a brand new execution of the framework to complete the rollback 🔄🚀\n[/bold green]")

                        # Run a brand new execution of the framework with the retrieved execution data
                        run_apaf_terraform({
                            'command': 'a',
                            'post_rollback': True,
                            'interactive': False,
                        })

                    else:
                        # Set the post-rollback scope variable to False
                        self.update_vars({
                            'post_rollback': False,
                            'interactive': True,
                        })

                        # Append the tmp_exec_log_file to the customer-wide log file.
                        self.handle_project_log(10)

                        # Remove the "tmp_log" directory
                        remove_directory(tmp_exec_log_path)

                        # Remove the folder to allocate the "temporary reverted input tgz file"
                        remove_directory(self.input_tgz_reverted_path)

                        # Remove the executions folder if exists and empty
                        if os.path.isdir(self.executions_dir) and not os.listdir(self.executions_dir):
                            remove_directory(self.executions_dir)

                else:
                    logger.warning(f'❌ Unexpected exit_code provided: {exit_code}.\nValid values: {exit_messages}')

                sys.exit(0)

            except Exception as e:
                logger.error(f'❌ Error during cleanup: {e}')

    def save_apstra_snapshot(self, max_apstra_snapshots=10, tgz_old_apstra_snapshots=True):
        '''
        Ensures the device snapshot directory is properly maintained.

        - If `self.apstra_snapshot_path` does not exist, create it.
        - If `tgz_old_apstra_snapshots` is True and `self.apstra_snapshot_path` exists, archive its subfolders.
        - Copy `self.snapshot_stage_path` contents into a subfolder of `self.apstra_snapshot_path` named `{timestamp}_apstra_snapshot`.
        - If the number of archived snapshots exceeds `max_apstra_snapshots - 1`, remove the oldest ones.
        '''

        try:
            # Ensure snapshot directory exists
            os.makedirs(self.apstra_snapshot_path, exist_ok=True)

            print("\n")

            # Archive old snapshots if required
            if tgz_old_apstra_snapshots:
                for item in os.listdir(self.apstra_snapshot_path):
                    item_path = os.path.join(self.apstra_snapshot_path, item)
                    if os.path.isdir(item_path):
                        tgz_path = f"{item_path}.tgz"
                        create_tgz_from_dir(item_path, tgz_path)
                        try:
                            remove_directory(item_path)  # Remove original folder after archiving
                            logger.info(f"📦 Archived and removed old snapshot: {item}")
                        except Exception as e:
                            logger.error(f"❌ Error removing directory {item_path}: {e}")

            # Create new snapshot directory
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            snapshot_dir = os.path.join(self.apstra_snapshot_path, f"{timestamp}_apstra_snapshot")
            os.makedirs(snapshot_dir, exist_ok=True)

            # Copy contents from snapshot_stage_path to new snapshot folder
            if os.path.exists(self.snapshot_stage_path):
                for item in os.listdir(self.snapshot_stage_path):
                    src = os.path.join(self.snapshot_stage_path, item)
                    dst = os.path.join(snapshot_dir, item)
                    try:
                        if os.path.isdir(src):
                            shutil.copytree(src, dst)
                        else:
                            shutil.copy2(src, dst)
                        logger.info(f"📁 Copied {src} → {dst}")
                    except Exception as e:
                        logger.error(f"❌ Error copying {src} to {dst}: {e}")

            # Enforce max snapshots limit
            try:
                tgz_snapshots = sorted(
                    [f for f in os.listdir(self.apstra_snapshot_path) if f.endswith('.tgz')],
                    key=lambda x: x.split('_')[0]  # Sorting based on timestamp
                )

                while len(tgz_snapshots) > max_apstra_snapshots - 1:
                    oldest_snapshot = tgz_snapshots.pop(0)
                    os.remove(os.path.join(self.apstra_snapshot_path, oldest_snapshot))
                    logger.info(f"🗑️ Removed old snapshot: {oldest_snapshot}")

            except Exception as e:
                logger.error(f"❌ Error managing old snapshots: {e}")

        except Exception as e:
            logger.critical(f"🚨 Critical error in save_apstra_snapshot: {e}")

    def build_table_scope(self):
        '''
        Display the scope information in a table format

        Returns:
            Table: A Rich Table object with the scope information.

        Raises:
            Exception: If any error occurs during the processing or display of the scope.

        '''
        try:
            self.validate_scope()

            table = Table(
                Column(header="Feature", justify="right", style="cyan"),
                Column(header="Value", justify="center", style="magenta"),
                title="SCOPE",
                box=box.HEAVY_EDGE,
            )
            table.show_header = False
            table.title_justify = "center"
            table.title_style = "cyan underline"

            table.add_row("AOS Target", self.aos_target)
            table.add_row("Customer", self.customer)
            table.add_row("Domain", self.domain)
            table.add_row("Project", self.project)

            return table

        except Exception as e:
            logger.error(f"❌ Error printing scope: {e}")

    def build_table_terraform_command(self):
        '''
        Display the Terraform command information in a table format

        Returns:
            Table: A Rich Table object with the Terraform command information.

        Raises:
            Exception: If any error occurs during the processing or display of the Terraform command.

        '''
        try:
            table = Table(
                Column(header="Value", justify="center", style="magenta"),
                title="TERRAFORM COMMAND",
                box=box.HEAVY_EDGE,
            )
            table.show_header = False
            table.title_justify = "center"
            table.title_style = "cyan underline"

            table.add_row(self.terraform_command)

            return(table)

        except Exception as e:
            logger.error(f"❌ Error printing Terraform command: {e}")

    def print_panel_execution_plan(self):
        '''
        Display the execution plan in a formatted panel

        Returns:
            None
        '''
        try:

            table_scope = self.build_table_scope()
            table_terraform_command = self.build_table_terraform_command()

            panel = Panel.fit(
                Columns([
                    table_scope,
                    " "*15,
                    table_terraform_command,
                ]),
                title="[bold]EXECUTION PLAN",
                border_style="red",
                title_align="left",
            )
            rprint(panel)

        except Exception as e:
            logger.error(f"❌ Error displaying execution plan: {e}")

    def print_changes_in_bps(self, bps):
        '''
        Assess changes in multiple blueprints and print a summary of differences.

        Args:
            bps (list): List of blueprint names to assess.

        Raises:
            Exception: If an error occurs during the assessment of blueprint changes.
        '''
        try:
            for bp_name in bps:
                bp_diff_status = get_bp_diff_status(bp_name)
                table_bp_diff_status = build_table_bp_diff_status(bp_diff_status)
                bp_diff = filter_none_values(get_bp_diff(bp_name))
                table_summary_changes = build_table_bp_summary_changes(bp_diff)
                table_changes_count, table_changes = build_table_changes(bp_diff)
                print_panel_bp_diff(bp_name, table_bp_diff_status, table_summary_changes, table_changes_count, table_changes)
        except Exception as e:
            logger.error(f"❌ An error occurred while diffing the changes in the blueprints': {e}")

    def validate_scope(self):
        '''
        Validate the scope parameters.

        Returns:
            None

        '''
        is_valid_aos_target = self.validate_aos_target()
        is_valid_customer = self.validate_customer()
        is_valid_domain = self.validate_domain() if is_valid_customer else False
        is_valid_project = self.validate_project() if is_valid_domain else False

        if not (is_valid_aos_target and is_valid_customer and is_valid_domain and is_valid_project):
            sys.exit()

    def validate_aos_target(self):
        '''
        Validate if the AOS target in the YAML file of AOS targets.

        Returns:
            bool: True if the AOS target is valid, False otherwise.
        '''
        if not any(item == self.aos_target for item in self.aos_targets_list):
            logger.error(f"❌ Invalid AOS Target specified ({self.aos_target}).")
            print_choices(self.aos_targets_list)
            return False
        return True

    def validate_customer(self):
        '''
        Validate the customer in the scope.

        Returns:
            bool: True if the customer is valid, False otherwise.

        '''
        if not any(item == self.customer for item in customers_list):
            logger.error(f"❌ Invalid Customer specified ({self.customer}).")
            print_choices(customers_list)
            return False
        return True

    def validate_domain(self):
        '''
        Validate the domain in the scope.

        Returns:
            bool: True if the domain is valid, False otherwise.

        '''
        if not any(item == self.domain for item in self.domains_list):
            logger.error(f"❌ Invalid Domain specified for Customer {self.customer} ({self.domain}).")
            print_choices(self.domains_list)
            return False
        return True

    def validate_project(self):
        '''
        Validate the project in the scope.

        Returns:
            bool: True if the project is valid, False otherwise.

        '''
        if not any(item == self.project for item in self.projects_list):
            logger.error(f"❌ Invalid Project specified for Domain {self.domain} ({self.project}).")
            print_choices(self.projects_list)
            return False

        return True

    def align_aos_target(self):
        '''
        Align the AOS target in the YAML file of AOS targets to one of the valid options for a specific domain.

        Returns:
            bool: True if the AOS target was not valid and has been changed, False otherwise.

        '''
        if not any(item == self.aos_target for item in self.aos_targets_list):
            logger.info(f'🔄 Customer "{self.customer}", Domain "{self.domain}": Changing AOS target from "{self.aos_target}" to "{self.aos_targets_list[0]}"')
            self.aos_target = self.aos_targets_list[0]
            return True
        return False

    def align_customer(self):
        '''
        Align the customer in the scope to one of the valid options for a specific customer.

        Returns:
            bool: True if the customer was not valid and has been changed, False otherwise.

        '''
        if not any(item == self.customer for item in self.customers_list):
            logger.info(f'🔄 Changing Customer from "{self.customer}" to "{self.customers_list[0]}"')
            self.customer = self.customers_list[0]
            return True
        return False
    
    def align_domain(self):
        '''
        Align the domain in the scope to one of the valid options for a specific customer.

        Returns:
            bool: True if the domain was not valid and has been changed, False otherwise.

        '''
        if not any(item == self.domain for item in self.domains_list):
            logger.info(f'🔄 Customer "{self.customer}": Changing Domain from "{self.domain}" to "{self.domains_list[0]}"')
            self.domain = self.domains_list[0]
            return True
        return False

    def align_project(self):
        '''
        Align the project in the scope to one of the valid options for a specific domain.

        Returns:
            bool: True was the project is not valid and has been changed, False otherwise.

        '''
        if not any(item == self.project for item in self.projects_list):
            logger.info(f'🔄 Customer "{self.customer}", Domain "{self.domain}": Changing Project from "{self.project}" to "{self.projects_list[0]}"')
            self.project = self.projects_list[0]
            return True
        return False

    def update_terraform_backend_config_path(self):
        '''
        Update the Terraform backend configuration path

        Returns:
            str: The updated backend configuration path.

        '''
        try:
            os.chdir(terraform_path)
            subprocess.run([
                "terraform",
                "init",
                "-reconfigure",
                f"-backend-config=path={self.wip_execution_0_tfstate_file}"
            ])
            os.chdir(python_path)
            return self.wip_execution_0_tfstate_file
        except Exception as e:
            logger.error(f"❌ Error updating Terraform backend config path '{self.wip_execution_0_tfstate_file}': {e}")

    def manage_execution_dirs(self, stage, threshold=50):
        '''
        Ensure the creation and management of "executions" folders within a specified directory structure.

        Steps performed by this function:

        - For initial_stage:
            1. Create the "wip" folder if it does not exist.
            2. Rename existing "execution_<x>" folders within the "wip" folder, increasing each <x> by 1.
            3. Remove any folders with <x> greater than the specified threshold.
            4. Ensure that the "execution_0" folder is available for use and create it along with all the necessary subfolders.
            5. Tgz the current input folder and save it in the "yaml" subfolder of "execution_0".
            6. Copy the tfstate files from the previous execution ("execution_1") to "execution_0"
            7. Copy the tgz and tfstate files from the previous execution ("execution_1") to "execution_0" for reference with the suffix ".rollback".

        - For destroy_final_stage:
            1. Create the "archive" folder if it does not exist within the "output" folder.
            2. Tgz the current "executions" folder and save it in the "archive" folder named with the date and time followed by "_archive".
            3. Remove the "executions" folder.
            4. Remove the "cabling_maps" folders

        Args:
            data_path (str): The base path to the data directory.
            stage (str): 'initial_stage' or 'destroy_final_stage'
            threshold (int): The maximum allowed number for "execution_<x>" folders. Defaults to 50.

        Returns:
            None.
        '''

        try:

            if stage == "initial_stage":

                # Create the folder to allocate the "temporary reverted input tgz file" if it doesn't exist
                if not os.path.exists(self.input_tgz_reverted_path):
                    os.makedirs(self.input_tgz_reverted_path)

                # Create the "wip" folder if it doesn't exist
                if not os.path.exists(self.wip_path):
                    os.makedirs(self.wip_path)

                # Get a list of execution folders
                execution_dirs = [
                    f for f in os.listdir(self.wip_path)
                    if f.startswith("execution_") and os.path.isdir(os.path.join(self.wip_path, f))
                ]

                # Sort the folders by their numeric value
                execution_dirs.sort(key=lambda x: int(x.split('_')[1]))

                # Rename the folders, increasing each <x> by 1
                for folder in reversed(execution_dirs):
                    folder_num = int(folder.split('_')[1])
                    new_dir_num = folder_num + 1
                    new_dir_name = f"execution_{new_dir_num}"

                    if new_dir_num > threshold:
                        # Remove folders that exceed the threshold
                        remove_directory(os.path.join(self.wip_path, folder))
                    else:
                        # Rename folders
                        os.rename(os.path.join(self.wip_path, folder),
                                os.path.join(self.wip_path, new_dir_name))

                # The "execution_0" folder is now available for use
                # Create the "execution_0" folder and the required subfolders
                if not os.path.exists(self.wip_execution_0_path):
                    os.makedirs(self.wip_execution_0_path)

                    scope_data = {}
                    scope_data['aos_target'] = self.aos_target
                    scope_data['customer'] = self.customer
                    scope_data['domain'] = self.domain
                    scope_data['project'] = self.project
                    scope_data['pre_commit_action'] = self.pre_commit_action
                    scope_data['pre_commit_comment'] = self.pre_commit_comment
                    scope_data['post_commit_action'] = self.post_commit_action
                    scope_data['post_commit_comment'] = self.post_commit_comment
                    scope_data['post_rollback'] = self.post_rollback
                    scope_data['interactive'] = self.interactive
                    scope_data['first_execution_reverted'] = self.first_execution_reverted
                    scope_data['terraform_command'] = self.terraform_command

                    self.handle_execution_data_file("create", scope_data)

                    os.makedirs(self.wip_execution_0_tfstate_path)
                    os.makedirs(self.wip_execution_0_yaml_path)
                    os.makedirs(self.wip_execution_0_log_path)
                    os.makedirs(self.wip_execution_0_tfplan_path)
                    os.makedirs(self.wip_execution_0_snapshot_path)

                # Save a tgz version of the project's input folder in the "yaml" subfolder
                if os.path.exists(self.input_path) and os.path.exists(self.wip_execution_0_yaml_path):
                    create_tgz_from_dir(self.input_path, self.wip_execution_0_input_tgz_file)

                # Bring some files from the previous execution (if exists)
                if os.path.exists(self.wip_execution_1_path):

                    # Copy the current tfstate (currently in execution_1) to execution_0
                    if os.path.exists(self.wip_execution_1_tfstate_file):
                        shutil.copy2(self.wip_execution_1_tfstate_file, self.wip_execution_0_tfstate_path)
                    # Copy the tgz previous version (currently in execution_1) to execution_0
                    # These files will serve as a reference for comparison
                    if os.path.exists(self.wip_execution_1_input_tgz_file):
                        shutil.copy2(self.wip_execution_1_input_tgz_file, self.wip_execution_0_input_tgz_rollback_file)

                    if self.post_rollback:
                        if os.path.exists(self.input_tgz_reverted_file):
                            copy_file(self.input_tgz_reverted_file, self.wip_execution_0_input_tgz_reverted_file)
                            logger.info(f"📦 Keeping a copy of the reverted project's input folder TGZ at {self.wip_execution_0_input_tgz_reverted_file} for easy retrieval if needed.")
                            remove_directory(self.input_tgz_reverted_path)

            elif stage == "destroy_final_stage":
                logger.info('📦 Executions archived due to Terraform destroy action.')
                # Create the "archive" folder if it does not exist
                if not os.path.exists(self.archive_dir):
                    os.makedirs(self.archive_dir)

                # Create a tgz of the current "executions" folder
                if os.path.exists(self.executions_dir):
                    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    archive_file = os.path.join(self.archive_dir, f"{now}_archive.tgz")
                    create_tgz_from_dir(self.executions_dir, archive_file)
                    logger.info(f'{archive_file}')

                    # Remove the "executions" folder
                    remove_directory(self.executions_dir)

                    # Remove the "cabling_maps" folders
                    remove_directory(self.wip_execution_0_cabling_map_path)

        except Exception as e:
            logger.error(f"❌ An error occurred while managing execution folders: {e}")

    def handle_project_log(self, max_size_mb=10, tgz_backup_files=True):
        '''
        Ensures the project log file is properly maintained.

        - If `self.project_log_file` does not exist, it is created by copying `tmp_exec_log_file`.
        - If `self.project_log_file` exists, `tmp_exec_log_file` is appended to it.
        - If the size of `self.project_log_file` exceeds `max_size_mb`, it is backed up using `rename_backup_files`. Defaults to 10 MB.
        - If `tgz_backup_files` is True, backup files are compressed into a `.tgz` archive. Defaults to True.

        Args:
            max_size_mb (int, optional): Maximum log file size in MB before triggering a backup. Defaults to 10MB.
            tgz_backup_files (bool, optional): If True, compress backup files into a `.tgz` archive.
        '''
        try:
            # Check log file size and rotate if necessary before anything else
            if os.path.exists(self.project_log_file) and os.path.getsize(self.project_log_file) > (max_size_mb * 1024 * 1024):
            # if os.path.exists(self.project_log_file) and os.path.getsize(self.project_log_file) > (max_size_mb):
                rename_backup_files(self.project_log_file, tgz_backup_files=tgz_backup_files)

            # Handle creation or appending of the log file
            if not os.path.exists(self.project_log_file):
                # Create directories if they don't exist and copy the tmp log file to the project log
                os.makedirs(os.path.dirname(self.project_log_file), exist_ok=True)
                shutil.copy(tmp_exec_log_file, self.project_log_file)
            else:
                # Append the content of tmp_exec_log_file to the existing project log file
                with open(self.project_log_file, 'a') as project_log, open(tmp_exec_log_file, 'r') as tmp_log:
                    shutil.copyfileobj(tmp_log, project_log)

        except Exception as e:
            logger.error(f"❌ Error handling project log file: {e}")

    def run_terraform(self, remove_backup = True):
        '''
        Creates the Terraform Plan (only if the command is an apply or a destroy action), executes the specified Terraform command, manages tfstate files,
        and handles the plan's execution and monitoring.

        Args:
            remove_backup (bool, optional): If True, removes the ".backup" tfstate file after execution. Defaults to True.

        Returns:
            None

        Raises:
            Exception: If any error occurs during command execution.

        Workflow:
            1. Change the current directory to the Terraform working directory.
            2. Log the execution of the Terraform command.
            3. Check if any changes are present by running the Terraform plan.
            4. If changes are detected, prompt the user for confirmation before applying the plan.
            5. Apply the plan or exit based on the user's input.
            6. If requested, remove the backup tfstate file after execution.
        '''

        try:
            # Change to the Terraform working directory
            os.chdir(terraform_path)
            print("\n")

            # Set the Terraform apply or destroy command based on the input
            if "terraform apply" in self.terraform_command or "terraform destroy" in self.terraform_command:

                # Generate Terraform plan and check if changes exist
                tfplan_changes = self.generate_terraform_plan()

                # Exit early with the appropriate code if no TF Plan changes are detected
                if not tfplan_changes:
                    exit_code = "TF_PLAN_NO_CHANGES_POST_ROLLBACK" if self.post_rollback else "TF_PLAN_NO_CHANGES"  
                    self.exit_manager(exit_code)

                # Otherwise, create and display the Terraform Plan summary
                create_tfplan_summary(self.wip_execution_0_tfplan_file_json, self.wip_execution_0_tfplan_file_summary)
                print("\n")
                logger.info(f"📄 Displaying the Terraform Plan Summary...")
                print("\n")
                display_tfplan_summary(self.wip_execution_0_tfplan_file_summary)
                logger.info(f"💾 Terraform Plan details available here: {self.wip_execution_0_tfplan_file_txt}")

                # If changes are detected, prompt the user to either proceed with executing the plan or exit.
                while True:
                    rprint('\n:pushpin:')
                    options = [
                        '🚀 Proceed with the Plan and execute Terraform',
                        '🚪 Exit and discard the Terraform Plan',
                    ]

                    # In not interactive mode, unconditionally choose to proceed with the plan (option 1)
                    if self.interactive:
                        opt = display_menu (options)
                    else:
                        opt = 1 # Simulate the automatic choice to proceed with the plan

                    if opt == 1:
                        break
                    elif opt == 2:
                        self.exit_manager("USER_TF_EXEC_ABORTED")
                    else:
                        logger.error(f"❌ Invalid option ({opt}) not within the valid choices. Try again...")

                # Delete blueprints via API before running Terraform destroy to prevent the "At least one rack should remain in the blueprint" error.
                # IMPORTANT: TO BE DONE ONLY if the blueprints have not been created in parent projects.
                if "terraform destroy" in self.terraform_command:
                    for bp_name in (self.get('blueprints') or []):
                        inherited_bp =  False

                        for project in self.parent_projects_list:
                            if project in self.projects_list:
                                project_path = os.path.join(self.projects_path, project)
                                input_path = os.path.join(project_path, "input")
                                files = yamldecode(os.path.join(input_path, "_main", "files.yml"))
                                blueprints_path = os.path.join(input_path, files["blueprints"]["directory"])
                                blueprints_filename = files["blueprints"]["filename"]
                                blueprints = yamldecode(os.path.join(blueprints_path, blueprints_filename)).get('blueprints', [])

                                if blueprints and bp_name in blueprints:
                                    inherited_bp =  True
                                    logger.info(f"🔄 Blueprint '{bp_name}' was not created in this project, it was inherited from {project}. Therefore, it will not be removed as part of this destroy operation.\n")
                                    break  # ✅ Stop checking other projects once found

                        if not inherited_bp:
                            logger.info(f"🔄 Blueprint '{bp_name}' was created in this project and will be deleted as part of the destroy operation.\n")
                            delete_bps([bp_name])

                # Log and apply the Terraform plan based on the command
                print("\n")
                logger.info(f"🚀 Applying the Terraform Plan with the command: '{self.terraform_command}'\n")

                # Set the terraform command to execute next to run the terraform plan.
                # Note that this is an apply action, whether the original command was 'apply' or 'destroy', as that has already been considered when generating the plan.
                terraform_command_tfplan = ["terraform", "apply", self.wip_execution_0_tfplan_file_bin]

            else: # If Terraform action is neither 'apply' nor 'destroy'
                if isinstance(self.terraform_command, str):
                    terraform_command_tfplan = shlex.split(self.terraform_command)  # Convert string to list, preserving quoted arguments

            # Execute Terraform (based on the Terraform Plan if the action was 'apply' or 'destroy', not based on it if it is not)
            result_tfplan_execution = run_command_and_save_stdout_stderr(terraform_command_tfplan, self.wip_execution_0_tfplan_all_log, self.wip_execution_0_tfplan_error)

            # Split the logfile of the execution into two files (logs and outputs) and remove the original logfile
            if os.path.exists(self.wip_execution_0_tfplan_all_log):
                split_file_on_first_match(self.wip_execution_0_tfplan_all_log, "Outputs:", self.wip_execution_0_tfplan_log, self.wip_execution_0_tfplan_output)
                remove_file(self.wip_execution_0_tfplan_all_log)

            # If Terraform action is neither 'apply' nor 'destroy', finish the execution
            if "terraform apply" not in self.terraform_command and "terraform destroy" not in self.terraform_command:
                self.exit_manager("TF_EXEC_NOT_APPLY_DESTROY")

            # If Terraform action is either 'apply' or 'destroy', a Terraform plan has been executed

            # Remove the backup tfstate file if requested (unnecessary since it can be grabbed from previous execution)
            if remove_backup:
                remove_file(f"{self.wip_execution_0_tfstate_file}.backup")

            # Errors in the Terraform execution evaluation:
            if result_tfplan_execution == 0: # No errors during the Terraform execution
                print("\n")
                tfplan_execution_resources = find_first_match_in_file(self.wip_execution_0_tfplan_log,"complete!")

                if tfplan_execution_resources:
                    logger.info(
                        f"🎉 {tfplan_execution_resources}"
                        f"✅ Terraform executed successfully.\n"
                        f"💾 Terraform execution details available here: {self.wip_execution_0_tfplan_log}"
                    )

                    # In interactive mode, prompt the user to press Enter to view the execution results just displayed above
                    if self.interactive:
                        input(" ⏭️  Press enter to continue...\n")

            else: # Errors during the Terraform execution
                logger.error(f"❌ Errors detected during the execution of the Terraform Plan.\n🔹 Details available in: {self.wip_execution_0_tfplan_error}\n🔍 Please review the file for further investigation.\n")
                if self.post_rollback:
                    self.exit_manager("BLOCKED_EXECUTIONS")
                elif "terraform destroy" in self.terraform_command:
                    self.exit_manager("TF_EXEC_W_ERRORS_DESTROY")
                else:
                    # In interactive mode, prompt the user to press Enter to proceed with the Rollback
                    if self.interactive:
                        input("⏭️  Press enter to initiate the rollback process...\n")
                    self.revert_execution(revert_to_last_exec = True)
                    self.exit_manager("TF_EXEC_W_ERRORS_REVERT")

        except Exception as e:
            logger.error(f"❌ An error occurred executing the command: %s", terraform_command_tfplan)
            logger.exception(e)

    def scan_blueprints(self, warning = False):
        '''
        Updates some lists of anomalous statuses retrieved from the provided blueprints for review.

        Args:
            warning (bool): If True, displays warnings for blueprints with anomalies.
       '''

        try:
            # Initialize lists for categorizing blueprints based on their statuses
            self.uncommitted_bps = []
            self.uncommitted_bps_w_errors = []

            warnings_exist =  False
            blueprints = self.get('blueprints',[])
           
            # Finish the execution if there are no blueprints
            if not blueprints:
                return
            
            # Retrieve blueprint data
            self.raw_blueprint_data = get_blueprint_data(blueprints, silent_mode = True)

            # Iterate through the blueprints to gather the facts
            for bp_name in blueprints:
                bp_data = next((bp for bp in self.raw_blueprint_data if bp.get('label', None) == bp_name), None)
                
                if bp_data:

                    # Check if blueprint has uncommitted changes
                    if bp_data.get('has_uncommitted_changes'):
                        self.uncommitted_bps.append({
                            'blueprint': bp_name,
                            'staged_version': bp_data.get('version')
                        })

                    # Check if there are build errors            
                    build_errors = bp_data.get('build_errors_count', 0)
                    if isinstance(build_errors, int) and build_errors > 0:
                        self.uncommitted_bps_w_errors.append({
                            'blueprint': bp_name,
                            'build_errors_count': build_errors
                        })
                        
                    if warning:
                        messages = []

                        # Check if the blueprint has build warnings
                        build_warning_count = bp_data.get('build_warnings_count', 0)
                        if build_warning_count > 0:
                            messages.append(f"Build Warning count: {build_warning_count}")

                        # Check deploy mode summary other than 'deploy'
                        for deploy_mode, number_of_devices in bp_data.get("deploy_modes_summary", {}).items():
                            if deploy_mode != 'deploy' and number_of_devices > 0:
                                messages.append(f"Deployed devices in {deploy_mode.capitalize()} mode: {number_of_devices}")

                        # Check deployment status other than 'succeeded'
                        for deployment_status, state in bp_data.get("deployment_status", {}).items():
                            for result, number_of_devices in state.items():
                                if result != 'num_succeeded' and number_of_devices > 0:
                                    messages.append(f"Deployed devices in {deployment_status[:-7].capitalize()} state with {result[4:].capitalize()} configurations: {number_of_devices}")

                        # Log warnings if any found
                        if messages:
                            warnings_exist =  True
                            logger.warning(f"👀 Warning Messages for Blueprint '{bp_name}':")
                            for message in messages:
                                logger.warning(f"   ➤ {message}")

                    # If warnings were found, prompt exit after checking all blueprints
                    if warnings_exist:
                        print("\n")
                        self.prompt_exit()

        except Exception as e:
            logger.error(f"❌ An error occurred while scanning blueprints: {e}")

    def get_bp_revision_list(self, bp_name):
        '''
        Get a list of revisions eligible to rollback to (time voyager) for a particular blueprint

        Args:
            bp_name (str): Blueprint name.

        Returns:
            str: Blueprint ID.
        '''
        try:
            aos_ip = self.get('aos_ip')
            aos_token = self.get('aos_token')
            bp_id = get_bp_id(bp_name)
            url = f'https://{aos_ip}/api/blueprints/{bp_id}/revisions'
            headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()
            return data['items']
        except Exception as e:
            logger.error(f'❌ Error: Failed to retrieve blueprint revision IDs - {e}')

    def prompt_revert(self):
        '''
        Prompts the user to revert changes. If confirmed, it triggers the execution rollback;
        otherwise, the framework execution finishes, allowing manual review.
        '''

        message = (
            "🔄 Do you want to revert the changes? "
            "If not, the framework execution will end, allowing you to review offline and take necessary actions."
        )

        # In not interactive mode, unconditionally proceed with the rollback
        if not self.interactive:
            self.revert_execution(revert_to_last_exec = True)
            self.exit_manager("USER_REVERT")
        else:
            if prompt_for_confirmation(message) == "yes":
                self.revert_execution(revert_to_last_exec = True)
                self.exit_manager("USER_REVERT")
            else:
                self.exit_manager("USER_SILENT_EXIT")

    def prompt_reconfirm_revert(self):
        '''
        Prompts the user to reconfirm that wants to revert changes. If confirmed, it triggers the execution rollback;
        otherwise, the framework continues.
        '''

        message = (
            "🔄 Please reconfirm that you really want to roll back to a previous state"
        )

        # In not interactive mode, unconditionally proceed with the rollback
        if not self.interactive:
                self.revert_execution(revert_to_last_exec = True)
                self.exit_manager("USER_REVERT")
        else:
            if prompt_for_confirmation(message) == "yes":
                self.revert_execution(revert_to_last_exec = True)
                self.exit_manager("USER_REVERT")
            else:
                return True
            
    def prompt_exit(self):
        '''
        Prompts the user to continue with the framework execution. If confirmed, execution proceeds;
        otherwise, it stops to allow manual review and necessary actions.
        '''

        message = (
            "👉 Would you like to continue with the framework execution taking these warnings into consideration?\n"
            "If not, the execution will stop, giving you the opportunity to review the situation offline and take appropriate actions"
        )

        # If interactive mode is enabled, prompt for confirmation
        if self.interactive:
            if prompt_for_confirmation(message) == "no":
                self.exit_manager("USER_SILENT_EXIT")

    def prompt_save_blueprint_data(self):
        '''
        Prompts the user to retrieve and save device data.
        '''

        message = (
            "📚 Do you want to retrieve and save the current configurations and device contexts of each deployed device?"
        )

        # In not interactive mode, unconditionally proceed without saving the device data
        if self.interactive:
            if prompt_for_confirmation(message) == "yes":
                self.save_device_data()

    def prompt_unblock_executions(self):
        '''
        Prompts the user for removing the execution block and proceed.
        '''

        message = (
            "🤔 🔎 Have you resolved the issues and want to unblock executions?"
        )

        # If interactive mode is enabled, prompt for confirmation
        if self.interactive:
            if prompt_for_confirmation(message) == "yes":
                return True
            else:
                return False

    def prompt_destroy(self):
        '''
        Prompts the user to confirm the 'terraform destroy' action.
        '''

        message = (
            "🤔🧨 'terraform destroy' is an IRREVERSIBLE action that will permanently remove ALL deployed resources in this project.\n"
            "Are you absolutely sure you want to proceed?"
        )

        # If interactive mode is enabled, prompt for confirmation
        if self.interactive:
            if prompt_for_confirmation(message) == "yes":
                logger.info("💥 Proceeding with 'terraform destroy'...")
                return True
            else:
                logger.info("🔄 Returning to the Execution Plan menu so you can modify the Terraform action.")
                return False

    def generate_terraform_plan(self):
        '''
        Executes a Terraform plan based on the given command ('terraform apply' or 'terraform destroy'),
        saves the plan in multiple formats (binary, text, JSON), generates a summary, and displays it.

        Returns:
            bool: A flag indicating whether changes are detected (True) or not (False).
        '''
        try:
            if "terraform apply" in self.terraform_command or "terraform destroy" in self.terraform_command:

                # Log the Terraform plan execution
                logger.info(f"🧩 Generating the Terraform Plan...\n")

                # Execute the Terraform plan with either 'apply' or 'destroy' options
                plan_cmd = ["terraform", "plan", "-out=" + self.wip_execution_0_tfplan_file_bin]
                if "terraform destroy" in self.terraform_command:
                    plan_cmd.insert(2, "-destroy")

                result_tfplan = run_command_and_save_stdout_stderr(plan_cmd, self.wip_execution_0_tfplan_generation_log, self.wip_execution_0_tfplan_generation_error)

                # Generate text and JSON outputs from the plan binary file
                subprocess.check_call(f"terraform show -no-color {self.wip_execution_0_tfplan_file_bin} > {self.wip_execution_0_tfplan_file_txt}", shell=True)
                json_result = subprocess.run(f"terraform show -json {self.wip_execution_0_tfplan_file_bin} > {self.wip_execution_0_tfplan_file_json}", shell=True)

                if json_result.returncode == 0:
                    with open(self.wip_execution_0_tfplan_file_json, "r") as json_file:
                        plan_data = json.load(json_file)

                    # Check for resource changes
                    resource_changes = plan_data.get("resource_changes", [])
                    changes_exist = any(
                        action in resource.get("change", {}).get("actions", [])
                        for resource in resource_changes for action in ["create", "update", "delete"]
                    )

                    # Return the binary plan file path and the changes flag
                    result = changes_exist

                else:
                    logger.error(f"❌ Failed to generate JSON from {self.wip_execution_0_tfplan_file_bin}.")
                    result = False

                if result_tfplan == 0:
                    print("\n")
                    logger.info("✅ Terraform Plan generated successfully")

                else:
                    self.exit_manager("TF_PLAN_W_ERRORS")

                return result

            else:
                logger.warning(f"❌ Invalid Terraform command: {self.terraform_command}. Only 'apply' or 'destroy' are supported.")
                return False

        except Exception as e:
            logger.error(f"❌ Terraform plan execution failed: {str(e)}")

            return False

    def revert_execution(self, revert_to_last_exec = False):
        '''
        Reverts the current execution to a previous execution completed with a convenient exit code.

        Args:
            terraform_command (str): Terraform command to execute (e.g., 'terraform apply' or 'terraform destroy').
            revert_to_last_exec (bool): Either to automatically revert to the last valid execution or to one to be selected by the user.
        '''

        # -- Rollback banner
        logger.info(f"🔄 Starting the rollback process...")

        # Since the changes in the Non-blueprint menus occur at runtime and are neither commit-able nor natively revertible,
        # a comprehensive rollback process has been developed. This process restores the objects to their previous desired versions
        # by comparing the input YAML files from the previous desired execution (execution to revert to) and execution_0 (ongoing execution).

        # -- Retrieve and filter the execution history for rollback
        self.get_project_rollback_history()

        if revert_to_last_exec:
            rollback_choice = "last"
        else:
            # -- Display the rollback execution history and get the number of available executions
            number_of_executions = self.print_project_rollback_history()
            # -- Prompt the user for the previous execution to revert to
            rollback_choice = self.prompt_rollback_execution_choice(number_of_executions)

        # -- Retrieve the details of the selected rollback execution and update a set of rollback-related variables
        self.get_rollback_execution_choice(rollback_choice)

        # Ensure there is a valid rollback execution path
        if not self.first_execution_reverted and (not self.wip_execution_rollback_path or not os.path.exists(self.wip_execution_rollback_path)):
            logger.warning(f"❌ No valid rollback execution path found: {self.wip_execution_rollback_path or 'None'}\nSkipping the rollback process.")
            return

        # -- Steps to copy the tfstate file and tgz of the input folder from the selected rollback execution to 'execution_0' as rollback files
        if not self.first_execution_reverted:
            # Save the current tgz of the input folder in "execution_0" as a "reverted" version.
            if os.path.exists(self.wip_execution_0_input_tgz_file):
                logger.info(f'📦 Saving current tgz of the input folder as a "reverted" version: {self.input_tgz_reverted_file}')
                shutil.copy2(self.wip_execution_0_input_tgz_file, self.input_tgz_reverted_file)

            # Roll back the input folder in "execution_0" to the input folder of the execution to revert to (if it exists).
            # This will be accomplished by extracting the contents of the execution to revert to input folder from the tgz file.
            if os.path.exists(self.wip_execution_0_input_tgz_rollback_file):
                remove_directory(self.input_path)
                logger.info(f'📂 Replacing the input folder by the extracted files from the tgz of the input folder from previous execution: {self.input_path}')
                extract_tgz_to_dir(self.wip_execution_0_input_tgz_rollback_file, self.project_path)

        print("\n")

        # Easy case - just revert pending changes on the blueprints
        if revert_to_last_exec:

            # -- Check for uncommitted blueprints
            self.scan_blueprints()
            if self.uncommitted_bps:
                for bp in self.uncommitted_bps:
                    bp_name = bp.get('blueprint', None)
                    list_bp_revisions = self.get_bp_revision_list(bp_name)
                    if len(list_bp_revisions) > 0:
                        logger.info(f"🔄 Previous revisions available in the Time Voyager of blueprint '{bp_name}'.\n")
                        # -- Previous revisions exist for this bp - remove uncommitted changes in the bp via API
                        revert_bp(bp_name)
                    else:
                        # -- Previous revisions do not exist for this bp - delete bp via API
                        logger.info(f"🔄 No previous revisions available in the Time Voyager of blueprint '{bp_name}'.")
                        delete_bps([bp_name])
        print("\n")

        # -- Identify and list the Apstra sections other than blueprints that have changes compared to the last successful execution (that may exist or not)
        list_non_bp_menus_w_changes, non_bp_diff = get_non_bp_changes_tgz(self.get('wip_execution_0_input_tgz_file'), self.get('wip_execution_0_input_tgz_rollback_file'))
        for menu in list_non_bp_menus_w_changes:
            self.handle_execution_data_file('update', {f'changes_in_{menu}': 'Yes'})

        # -- Remove all the added objects to the Non-blueprint menus in Apstra (to avoid conflicts later on if the framework tries to recreate them)
        if list_non_bp_menus_w_changes and non_bp_diff:
            remove_non_bp_added(non_bp_diff)

    def generate_customer_history_report(self, option):
        '''
        Generates an execution history report based on the specified scope.

        Args:
            option (str): Scope of the report. Valid options:
                        - "all-customers" (all customers)
                        - "customer-wide" (all projects within all domains within a specific customer)
                        - "domain-wide" (all projects within a specific domain within a specific customer)
                        - "project-wide" (specific project within a specific domain within a specific customer)

        Returns:
            None
        '''
        try:

            print("\n")

            # Initialize variables
            all_customers = False
            customer = domain = project = None

            # Process the option
            if option == 'all-customers':
                all_customers = True
            elif option == 'customer-wide':
                customer = self.customer
            elif option == 'domain-wide':
                customer, domain = self.customer, self.domain
            elif option == 'project-wide':
                customer, domain, project = self.customer, self.domain, self.project
            else:
                raise ValueError(f"❌ Invalid option: '{option}'. Please provide a valid scope.")

            # Execute the final function
            generate_and_write_execution_history(all_customers, customer, domain, project)
            print("\n")
            # In interactive mode, prompt the user to press Enter to continue
            if self.interactive:
                input("⏭️  Press enter to continue...\n")

        except Exception as e:
            logger.error(f"❌ Error processing execution option: {e}")

    def save_blueprint_data(self):
        '''
        Fetch and save the data of blueprints from specified blueprints.
        '''

        try:
            # Define stage directory and create it if it doesn't exist
            self.snapshot_stage_path = os.path.join(self.wip_execution_0_snapshot_path, self.execution_stage)
            os.makedirs(self.snapshot_stage_path, exist_ok=True)

            blueprints = self.get('blueprints',[])
           
            # Finish the execution if there are no blueprints
            if not blueprints:
                return
            
            # Retrieve blueprint data
            self.raw_blueprint_data = get_blueprint_data(blueprints, silent_mode = True)

            print("\n")
            logger.info(f"💾 Saving blueprint data for stage '{self.execution_stage}':")

            # Define the file path
            self.raw_blueprint_data_path = os.path.join(self.snapshot_stage_path, f"raw_blueprint_data.yaml")

            # Save blueprint data as a YAML file
            with open(self.raw_blueprint_data_path, "w") as file:
                yaml.dump(self.raw_blueprint_data, file, default_flow_style=False)

            logger.info(f"💾📑 Raw blueprint data successfully saved at: {self.raw_blueprint_data_path}\n")

        except Exception as e:
            logger.error(f"❌ An error occurred while saving blueprint data for stage '{self.blueprint_data_stage}': {e}")

    def save_device_data(self):
        '''
        Fetch and save the data of devices from specified blueprints.
        '''

        try:
            # Define stage directory and create it if it doesn't exist
            self.snapshot_stage_path = os.path.join(self.wip_execution_0_snapshot_path, self.execution_stage)
            os.makedirs(self.snapshot_stage_path, exist_ok=True)

            blueprints = self.get('blueprints',[])
           
            # Finish the execution if there are no blueprints
            if not blueprints:
                return
            
            # Retrieve device data
            self.raw_device_data = get_device_data(self.get('blueprints',[]))

            print("\n")
            logger.info(f"💾 Saving device data for stage '{self.execution_stage}':")

            # Define the file path
            self.raw_device_data_path = os.path.join(self.snapshot_stage_path, f"raw_device_data.yaml")

            # Save device data as a YAML file
            with open(self.raw_device_data_path, "w") as file:
                yaml.dump(self.raw_device_data, file, default_flow_style=False)
            logger.info(f"💾📑 Raw device data successfully saved at: {self.raw_device_data_path}")

            self.save_device_config()
            self.save_device_context()

        except Exception as e:
            logger.error(f"❌ An error occurred while saving device data for stage '{self.execution_stage}': {e}")

    def save_device_config(self):
        '''
        Fetch and save the configuration of some devices.
        '''

        try:

            # Define stage directory and create it if it doesn't exist
            self.device_config_dir = os.path.join(self.snapshot_stage_path, 'device_config')
            os.makedirs(self.device_config_dir, exist_ok=True)

            for device in self.raw_device_data:
                blueprint_name = device.get("blueprint_name")
                hostname = device.get("hostname")
                config_data = device.get("config", {}).get("actual", {}).get("config")

                if not (blueprint_name and hostname and config_data):
                    continue  # Skip if required data is missing

                self.device_config_blueprint_dir = os.path.join(self.device_config_dir, blueprint_name)
                os.makedirs(self.device_config_blueprint_dir, exist_ok=True)  # Ensure blueprint directory exists
                device_config_path = os.path.join(self.device_config_blueprint_dir, f"{hostname}.conf")

                try:
                    with open(device_config_path, "w", encoding="utf-8") as file:
                        file.write(config_data.replace("\\n", "\n"))  # Ensure proper newline formatting
                    logger.info(f"💾🛠️  Config for '{hostname}' (blueprint '{blueprint_name}') successfully saved at: {device_config_path}")
                except Exception as e:
                    logger.warning(f"❌ Failed to save config for '{hostname}' (blueprint '{blueprint_name}'): {e}")


        except Exception as e:
            logger.error(f"❌ An error occurred while saving device config for stage '{stage}': {e}")

    def save_device_context(self):
        '''
        Fetch and save the device context of some devices.
        '''

        try:

            # Define stage directory and create it if it doesn't exist
            self.device_context_dir = os.path.join(self.snapshot_stage_path, 'device_context')
            os.makedirs(self.device_context_dir, exist_ok=True)

            for device in self.raw_device_data:
                blueprint_name = device.get("blueprint_name")
                hostname = device.get("hostname")
                context_data = device.get("config_context", {}).get("context")

                if not (blueprint_name and hostname and context_data):
                    continue  # Skip if required data is missing

                self.device_context_blueprint_dir = os.path.join(self.device_context_dir, blueprint_name)
                os.makedirs(self.device_context_blueprint_dir, exist_ok=True)  # Ensure blueprint directory exists
                device_context_path = os.path.join(self.device_context_blueprint_dir, f"{hostname}.yaml")

                try:
                    with open(device_context_path, "w", encoding="utf-8") as file:
                        yaml.dump(json.loads(context_data), file, default_flow_style=False, sort_keys=False)
                        logger.info(f"💾🔧 Context for '{hostname}' (blueprint '{blueprint_name}') successfully saved at: {device_context_path}")
                except Exception as e:
                    logger.warning(f"❌ Failed to save context for '{hostname}' (blueprint '{blueprint_name}'): {e}")

        except Exception as e:
            logger.error(f"❌ An error occurred while saving device context for stage '{stage}': {e}")

    def save_commit_check(self):
        '''
        Fetch and save the commit check data of devices from specified blueprints.
        '''

        try:
            # Define stage directory and create it if it doesn't exist
            self.commit_check_stage_dir = os.path.join(self.wip_execution_0_snapshot_path, self.commit_check_stage)
            os.makedirs(self.commit_check_stage_dir, exist_ok=True)

            # Retrieve device data if not done before
            if not hasattr(self, "raw_device_data") or not self.raw_device_data:
                devices = get_bp_devices(self.get('blueprints',[]))
            else:
                devices = self.raw_device_data

            self.raw_commit_check = []

            for device in devices:

                blueprint_name = device.get("blueprint_name")
                blueprint_id = device.get("blueprint_id")
                hostname = device.get("hostname")
                device_id = device.get("device_id")

                # Retrieve commit check data
                print("\n")
                logger.info(f"🔍 Retrieving commit check data for '{hostname}' (blueprint '{blueprint_name}') at stage '{self.commit_check_stage}'...")
                if run_commit_check(blueprint_name, device_id, hostname):
                    self.raw_commit_check.append({
                        'blueprint_name': blueprint_name, # Blueprint identifier
                        'blueprint_id': blueprint_id, # Blueprint identifier
                        'hostname': hostname,  # Device hostname
                        'device_id': device_id,  # Unique device identifier
                        'commit_check': get_commit_check_result(blueprint_name, device_id, hostname),  # Full commit check device details
                    })

            # Define the file path
            self.raw_commit_check_path = os.path.join(self.commit_check_stage_dir, f"raw_commit_check_data.yaml")

            # Save commit check data as a YAML file
            with open(self.raw_commit_check_path, "w") as file:
                yaml.dump(self.raw_commit_check, file, default_flow_style=False)

            print("\n")
            logger.info(f"💾📑 Raw commit check data successfully saved at: {self.raw_commit_check_path}")

            self.save_config_diff()
            # self.save_rendered_config()

        except Exception as e:
            logger.error(f"❌ An error occurred while saving commit check data for stage '{self.commit_check_stage}': {e}")

    def save_config_diff(self):
        '''
        Fetch and save the config diff of some devices.
        '''

        try:

            # Define stage directory and create it if it doesn't exist
            self.device_config_diff_dir = os.path.join(self.commit_check_stage_dir, 'device_config_diff')
            os.makedirs(self.device_config_diff_dir, exist_ok=True)

            for device in self.raw_commit_check:
                blueprint_name = device.get("blueprint_name")
                hostname = device.get("hostname")
                config_diff = device.get("commit_check", {}).get("diff_string")
                error = device.get("commit_check", {}).get("error")

                if not (blueprint_name and hostname and (config_diff or error)):
                    continue  # Skip if required data is missing

                self.device_config_blueprint_dir = os.path.join(self.device_config_diff_dir, blueprint_name)
                os.makedirs(self.device_config_blueprint_dir, exist_ok=True)  # Ensure blueprint directory exists
                device_config_diff_path = os.path.join(self.device_config_blueprint_dir, f"{hostname}.diff")

                try:
                    with open(device_config_diff_path, "w", encoding="utf-8") as file:
                        file.write(config_diff.replace("\\n", "\n"))  # Ensure proper newline formatting
                    logger.info(f"💾🆚 Config diff for '{hostname}' (blueprint '{blueprint_name}') successfully saved at: {device_config_diff_path}")

                except Exception as e:
                    logger.warning(f"❌ Failed to save config diff for '{hostname}' (blueprint '{blueprint_name}'): {e}")

        except Exception as e:
            logger.error(f"❌ An error occurred while saving device config diff for stage '{stage}': {e}")

    def save_rendered_config(self):
        '''
        Fetch and save the rendered config of some devices.
        '''

        try:

            # Define stage directory and create it if it doesn't exist
            self.device_rendered_config_dir = os.path.join(self.commit_check_stage_dir, 'device_rendered_config')
            os.makedirs(self.device_rendered_config_dir, exist_ok=True)

            for device in self.raw_commit_check:
                blueprint_name = device.get("blueprint_name")
                hostname = device.get("hostname")
                rendered_config = device.get("commit_check", {}).get("config_string")

                if not (blueprint_name and hostname and rendered_config):
                    continue  # Skip if required data is missing

                self.device_config_blueprint_dir = os.path.join(self.device_rendered_config_dir, blueprint_name)
                os.makedirs(self.device_config_blueprint_dir, exist_ok=True)  # Ensure blueprint directory exists
                device_rendered_config_path = os.path.join(self.device_config_blueprint_dir, f"{hostname}.conf")

                try:
                    with open(device_rendered_config_path, "w", encoding="utf-8") as file:
                        file.write(rendered_config.replace("\\n", "\n"))  # Ensure proper newline formatting
                    logger.info(f"💾🛠️  Rendered config for '{hostname}' (blueprint '{blueprint_name}') successfully saved at: {device_rendered_config_path}")

                except Exception as e:
                    logger.warning(f"❌ Failed to save rendered config for '{hostname}' (blueprint '{blueprint_name}'): {e}")


        except Exception as e:
            logger.error(f"❌ An error occurred while saving device rendered config for stage '{stage}': {e}")

    def print_panel_commit_check(self):
        '''
        Displays a list of devices with configuration differences and allows the user to review them interactively.

        Lists devices with blueprint names and hostnames.

        The user can:
        - Enter specific IDs (comma-separated) to view selected diffs.
        - Type 'all' to display all differences.
        - Press Enter to exit the selection loop.
        - The selection loop repeats until the user presses Enter.
        '''

        try:
            list_devices_diff_error = []
            list_devices_diff = []

            # Gather devices with configuration differences
            for device in self.raw_commit_check:
                blueprint_name = device.get("blueprint_name")
                hostname = device.get("hostname")
                config_diff = device.get("commit_check", {}).get("diff_string")
                error = device.get("commit_check", {}).get("error")

                if blueprint_name and hostname and error:
                    list_devices_diff_error.append({
                        'blueprint_name': blueprint_name,
                        'hostname': hostname,
                        'error': error,
                    })

                elif blueprint_name and hostname and config_diff:
                    list_devices_diff.append({
                        'blueprint_name': blueprint_name,
                        'hostname': hostname,
                        'config_diff': config_diff,
                    })

            if list_devices_diff_error:
                logger.error("❌ Configuration Errors detected during the Commit Check assessment.\n🔹 Details displayed in the next table:\n")

                # Display devices with configuration errors
                title = f'DESCRIPTION OF CONFIGURATION ERRORS PER DEPLOYED DEVICE'
                table = Table(
                    Column(header="Blueprint", justify="center", style="cyan"),
                    Column(header="Hostname", justify="center", style="cyan"),
                    Column(header="Errors", justify="left", style="magenta"),
                    title=title,
                    box=box.HEAVY_EDGE,
                )
                table.show_header = True
                table.title_justify = "center"
                table.title_style = "cyan underline"
                table.show_lines=True
                for device in list_devices_diff_error:

                    table.add_row(device.get('blueprint_name'), device.get('hostname'), Text(device.get('error')))

                    panel = Panel.fit(
                        Columns([
                            table,
                        ]),
                        title=f"[bold]COMMIT CHECK OVERVIEW ",
                        border_style="red",
                        title_align="left",
                        )

                print("\n")
                rprint(panel)
                print("\n")

                # In interactive mode, prompt the user to press Enter to proceed with the Rollback
                if self.interactive:
                    input("⏭️  Press enter to initiate the rollback process...\n")
                self.revert_execution(revert_to_last_exec = True)
                self.exit_manager("TF_EXEC_W_ERRORS_REVERT")

            if not list_devices_diff:
                logger.info("✅ No configuration differences detected across devices.")
                return

            while True:
                # Display the list of devices with consecutive IDs
                print("\n🕵️  Devices with configuration differences:\n")
                for idx, device in enumerate(list_devices_diff, start=1):
                    print(f"{idx}. 🏢 Blueprint: {device['blueprint_name']} | 🔲 Hostname: {device['hostname']}")

                # Prompt the user for selection
                user_input = input(
                    "\n🔢 Enter the IDs of devices to view config differences (comma-separated, e.g., 1,3,5), type 'all' for all, or press Enter to continue: "
                ).strip().lower()

                if not user_input:
                    print("\n")
                    logger.info("✅ Exiting commit check review.")
                    break  # Exit loop when Enter is pressed

                # Handle "all" keyword
                if user_input == "all":
                    selected_ids = set(range(1, len(list_devices_diff) + 1))
                else:
                    # Parse user input into a set of integers
                    try:
                        selected_ids = {int(x.strip()) for x in user_input.split(",") if x.strip().isdigit()}
                    except ValueError as e:
                        logger.error(f"❌ Invalid input: {e}. Please enter numbers separated by commas or 'all'.")
                        continue

                # Display selected configuration differences
                title = f'DESCRIPTION OF CONFIGURATION CHANGES PER DEPLOYED DEVICE'
                table = Table(
                    Column(header="Blueprint", justify="center", style="cyan"),
                    Column(header="Hostname", justify="center", style="cyan"),
                    Column(header="Config Diff", justify="left", style="magenta"),
                    title=title,
                    box=box.HEAVY_EDGE,
                )
                table.show_header = True
                table.title_justify = "center"
                table.title_style = "cyan underline"
                table.show_lines=True

                # Fill the table
                for idx, device in enumerate(list_devices_diff, start=1):
                    if idx in selected_ids:
                        # Ensure multiline diffs render properly
                        table.add_row(device.get('blueprint_name', ''), device.get('hostname', ''), Text(device.get('config_diff', '')))
                        # table.add_row(device.get('blueprint_name'), device.get('hostname'), device.get('config_diff'))

                        panel = Panel.fit(
                            Columns([
                                table,
                            ]),
                            title=f"[bold]COMMIT CHECK OVERVIEW ",
                            border_style="red",
                            title_align="left",
                        )

                print("\n")
                rprint(panel)

        except Exception as e:
            logger.error(f"❌ An error occurred while processing commit checks: {e}")

    def commit_check(self, display=False):
        '''
        Initiates a Commit Check process to evaluate the impact of configuration changes on deployed devices.

        Args:
            display (bool): If True, the configuration differences will be displayed after the check. Defaults to False.

        The function:
        - Prompts the user for confirmation before proceeding.
        - Saves the commit check results.
        - Optionally displays the configuration differences if `display=True`.
        '''

        try:
            print("\n")

            # In not interactive mode, unconditionally proceed to commit check
            if not self.interactive:
                logger.info("🕵️  Starting the commit check process. Assessing configuration changes...")
                self.commit_check_stage = "01_before_committing"
                self.save_commit_check()
            else:
                message = (
                    "🧐 Do you want to initiate a Commit Check process to analyze the impact of these config changes on deployed devices?"
                )
                if prompt_for_confirmation(message) == "yes":
                    logger.info("🕵️  Starting the commit check process. Assessing configuration changes...")
                    self.commit_check_stage = "01_before_committing"
                    self.save_commit_check()
                    if display:
                        logger.info("📜 Displaying configuration differences...\n")
                        self.print_panel_commit_check()
                else:
                    logger.info("🚫 Commit Check process skipped by user.\n")

        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during the Commit Check process: {e}\n")

    def get_revision(self, bp_name, commit_comment):
        '''
        Get the details of a particular revision in the Time Voyager from the AOS API for a given Blueprint.

        Args:
            bp_name (str): Blueprint name.
            commit_comment (str): Commit comment of the searched revision.

        Returns:
            str: Template ID, or None if not found or an error occurs.
        '''
        try:
            list_bp_revisions = self.get_bp_revision_list(bp_name)
            for item in list_bp_revisions:
                if item.get('description') == commit_comment:
                    return item
            return {}
        except Exception as e:
            logger.error(f"❌ Error: Failed to retrieve a revision with the description '{commit_comment} for the blueprint '{bp_name}' - {e}")
            return {}

    def get_permanent_revisions(self, bp_name):
        '''
        Retrieve all revisions that have been marked as permanent (user_saved=True) 
        for a given blueprint from the AOS Time Voyager.

        Args:
            bp_name (str): Blueprint name.

        Returns:
            list: A list of revision dictionaries where 'user_saved' is True.
        '''
        try:
            list_bp_revisions = self.get_bp_revision_list(bp_name)

            if not list_bp_revisions:
                return []

            # Filter revisions where 'user_saved' is explicitly True
            permanent_revisions = [rev for rev in list_bp_revisions if rev.get('user_saved') is True]

            # if not permanent_revisions:
            #     logger.info(f"ℹ️ No permanent revisions found for blueprint '{bp_name}'")

            return permanent_revisions

        except Exception as e:
            logger.error(f"❌ Failed to retrieve permanent revisions for blueprint '{bp_name}': {e}")
            return []

    def remove_revision(self, bp_name, revision):
        '''
        Get the details of a particular revision in the Time Voyager from the AOS API for a given Blueprint.

        Args:
            bp_name (str): Blueprint name.
            commit_comment (str): Commit comment of the searched revision.

        Returns:
            str: Template ID, or None if not found or an error occurs.
        '''
        try:
            aos_ip = self.get('aos_ip')
            aos_token = self.get('aos_token')
            bp_id = get_bp_id(bp_name)
            revision_id = revision.get('revision_id')
            revision_timestamp = revision.get('created_at', None)
            if revision_timestamp:
                dt = datetime.strptime(revision_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                formatted_revision_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_revision_timestamp = "N/A"
            url = f'https://{aos_ip}/api/blueprints/{bp_id}/revisions/{revision_id}'
            headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
            response = requests.delete(url, headers=headers, verify=False)
            response.raise_for_status()
            if response.status_code == 202:                
                logger.info(
                    f"🕰️  Revision '{revision.get('revision_id', 'N/A')}' of blueprint '{bp_name}' removed from the Time Voyager.\n"
                    f"👤 User: '{revision.get('user', 'N/A')}' | 🌐 IP: '{revision.get('user_ip', 'N/A')}' | 🕒 Created at: {formatted_revision_timestamp}\n"
                    f"💬 Description: '{revision.get('description', 'N/A')}'\n"
                )
                return True
            else:
                return False
            

        except Exception as e:
            logger.error(f"❌ Error: Failed to remove revision '{revision_id}' for the blueprint '{bp_name}' - {e}")
            return {}
        
    def get_oldest_revision(self, bp_name):
        '''
        Retrieve the oldest revision (based on creation timestamp) for a given blueprint from the AOS Time Voyager.

        Args:
            bp_name (str): Blueprint name.

        Returns:
            dict: The oldest revision entry, or an empty dict if not found or an error occurs.
        '''
        try:
            list_bp_revisions = self.get_bp_revision_list(bp_name)

            if not list_bp_revisions:
                logger.warning(f"❌ No revisions found for blueprint '{bp_name}'")
                return {}

            # Find the revision with the earliest 'created_at' timestamp
            oldest = min(list_bp_revisions, key=lambda r: r.get('created_at', '9999-12-31T23:59:59Z'))
            return oldest

        except Exception as e:
            logger.error(f"❌ Failed to retrieve the oldest revision for blueprint '{bp_name}': {e}")
            return {}

    def keep_revision(self, bp_name, revision_id, commit_comment):
        '''
        Save a particular revision in the Time Voyager permanently from the AOS API for a given Blueprint.
        Args:
            bp_name (str): Blueprint name.
            revision_id (str): Revision ID of the revision to save permanently.
            commit_comment (str): Commit comment of the searched revision.

        Returns:
            str: Template ID, or None if not found or an error occurs.
        '''
        try:
            aos_ip = self.get('aos_ip')
            aos_token = self.get('aos_token')
            bp_id = get_bp_id(bp_name)
            url = f'https://{aos_ip}/api/blueprints/{bp_id}/revisions/{revision_id}/keep'
            headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
            response = requests.post(url, headers=headers, verify=False)

            # The API call returns a 400 error code regardless of the actual outcome of the operation.
            # A workaround is used to validate the true result of the operation.

            # response.raise_for_status()
            # if response.status_code == 202:
            #     logger.info(f'Revision "{revision_id}" of blueprint "{bp_name}" saved in the Time Voyager permanently.')
            #     return True
            # else:
            #     return False

            revision = self.get_revision(bp_name, commit_comment)
            if revision.get("user_saved", False):
                logger.info(f"💾 Revision '{revision_id}' of blueprint '{bp_name}' in the Time Voyager saved permanently.\n")
                return True
            else:
                raise Exception(f"Revision '{revision_id}' of blueprint '{bp_name}' in the Time Voyager NOT saved permanently.\n")
        except Exception as e:
            logger.error(f'❌ Error: Failed to save revision "{revision_id}" of blueprint "{bp_name}" in the Time Voyager permanently - {e}')
            return False
        
    def deploy_bp(self, bp_name, version, deploy_comment):
        '''
        Deploy the given staging version from the AOS API for a given blueprint.

        Args:
            bp_name (str): The name of the blueprint to commit.
            version (int): Staged version to deploy.
            deploy_comment (str): Comment associated with the Deployment/Commit.
        '''

        print("\n")
        logger.info(f"🔄 Committing changes for blueprint '{bp_name}' version '{version}'")

        try:
            aos_ip = self.get('aos_ip')
            aos_token = self.get('aos_token')
            bp_id = get_bp_id(bp_name)
            url = f'https://{aos_ip}/api/blueprints/{bp_id}/deploy'

            # Retrieve the original execution_id that was stored in the execution_data file at the start of execution.
            # Do not use self.execution_id, as it updates every time the Scope_Manager class is instantiated.
            execution_id = self.handle_execution_data_file("read", {}).get('execution_id', None)

            if execution_id:
                deploy_comment_w_execution_id = "(" + execution_id +") " + deploy_comment
            else:
                deploy_comment_w_execution_id = deploy_comment

            data = json.dumps({
                'version': version,
                'description': deploy_comment_w_execution_id
            })

            headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

            max_retries = 3
            retry_delay = 5  # seconds
            max_poll_attempts = 10  # Number of times to poll for process completion
            poll_delay = 3  # seconds between poll attempts

            commit_completed = False

            # Retry mechanism for initial request
            for attempt in range(1, max_retries + 1):
                if commit_completed:
                    break
                response = requests.put(url, headers=headers, data=data, verify=False)

                if response.status_code == 202:

                    logger.info("⏳ Initial commit request accepted. Polling for completion...")
                    # Poll until the process completes
                    for poll_attempt in range(1, max_poll_attempts + 1):
                        poll_response = requests.put(url, headers=headers, data=data, verify=False)

                        if poll_response.status_code == 202:
                            logger.info(f"🟢 Polling attempt {poll_attempt}/{max_poll_attempts}: Commit process completed")
                            # logger.info(f"🎯 Changes for blueprint '{bp_name}' version '{version}' committed\n")
                            commit_completed = True
                            break
                        elif poll_response.status_code == 409:
                            logger.info(f"⏳ Polling attempt {poll_attempt}/{max_poll_attempts}: Process ongoing, retrying in {poll_delay} seconds...")
                            time.sleep(poll_delay)
                        else:
                            # Process finished successfully or unexpected status
                            poll_response.raise_for_status()
                    
                    # If polling exhausts without success
                    if not commit_completed:
                        raise Exception("❌ Commit process did not complete within the polling limit.")

                elif response.status_code == 409:
                    logger.info(f"⏳ Attempt {attempt}/{max_retries}: Process ongoing, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    # Raise an exception for other unexpected HTTP errors
                    response.raise_for_status()

            if commit_completed:
                deploy_status = get_deploy_status(bp_name)
                if deploy_status.get('state', None) != 'success':
                    logger.error(
                        f"❌ Failed to commit changes for blueprint '{bp_name}' (version {version}).\n"
                        f"Reason: {deploy_status.get('error', 'Unknown error')}.\n"
                        f"💡 This likely happened because someone else made changes to the blueprint while this execution was running.\n"
                    )
                    if self.interactive:
                        input("⏭️  Press enter to initiate the rollback process...\n")
                
                revision = self.get_revision(bp_name, deploy_comment_w_execution_id)
                if revision:
                    revision_timestamp = revision.get('created_at', None)
                    if revision_timestamp:
                        dt = datetime.strptime(revision_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                        formatted_revision_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        formatted_revision_timestamp = "N/A"
                    print("\n")
                    logger.info(
                        f"🕰️  Revision '{revision.get('revision_id', 'N/A')}' of blueprint '{bp_name}' saved to the Time Voyager.\n"
                        f"👤 User: '{revision.get('user', 'N/A')}' | 🌐 IP: '{revision.get('user_ip', 'N/A')}' | 🕒 Created at: {formatted_revision_timestamp}\n"
                        f"💬 Description: '{revision.get('description', 'N/A')}'\n"
                    )
                    
                    permanent_revisions = self.get_permanent_revisions(bp_name)
                    if len(permanent_revisions) >= max_permanent_revisions:
                        logger.info(
                            f"🧮 Time Voyager quota check for blueprint '{bp_name}': {len(permanent_revisions)} out of {max_permanent_revisions} permanent slots used.\n"
                            f"🧹 Removing the oldest saved revision to make room for the most recent one."
                        )
                        oldest_revision = self.get_oldest_revision(bp_name)
                        self.remove_revision(bp_name, oldest_revision)

                    self.keep_revision(bp_name, version, deploy_comment_w_execution_id)

                return
            
            # If all retries fail, raise an exception
            raise Exception("Max retries reached. Could not commit the blueprint due to persistent conflicts.")

        except Exception as e:
            logger.error(f"❌ An error occurred while committing changes for blueprint '{bp_name}' version '{version}': {e}\n")


# ---------------------------------------------------------------------------- #
#                                    Logging                                   #
# ---------------------------------------------------------------------------- #

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    # datefmt="[%X]",
    datefmt='%Y-%m-%d - %H:%M:%S',
    handlers=[RichHandler()]
)

logger = logging.getLogger("rich")

# ---------------------------------------------------------------------------- #
#                                  Functions                                   #
# ---------------------------------------------------------------------------- #

def display_welcome_banner():
    '''
    Displays a welcome message for the Apstra Provisioning Automation Framework.
    Includes an ASCII art banner and a formatted greeting.
    '''
    try:
        print("\r")
        print("                                                                👋😊\n\n")
        rprint("[bold green]                                                   W E L C O M E   T O   T H E[/bold green]\n"
              "                             [bold green] A[/bold green] P S T R A   [bold green] P[/bold green] R O V I S I O N I N G   [bold green] A[/bold green] U T O M A T I O N  [bold green]  F[/bold green] R A M E W O R K\n")
        print('''
                                                                .+#+.
                                                                :@@@@@-
                                                            .#%%#:@@@@@-    .+%@%=.
                                                        .%@@@@%.-+-.     =@@@@@:
                    :+==================-.               .*@@@@+#@@@#.    :%@@@%.             :===================+
                    :+                                     .==.=@@@@@+.--. .::..                                 :+
                    :+                                   .#@@@@*+@@@++@@@@#.                                     :+
                    :+                                   .%@@@@%:##*:#@@@@%.                                     :+
                    :+                                    .+%%+-@@@@@==%%+.                                      :+
                    :+                                         .@@@@@:                                           :+
                    :+                                          .---.                  .=###*.                   :+
                    :+                                                                .##*...                    :+
                    :+                                                                .##:                       :+
                    :+                                                                .##:                       :+
                    :+                       .===:....   .:: .-==-.      .:==-..... ..:##:...                    :+
                    :+                    .-###++*###+   -#*##++*##+.  .+##*++####. .*######:                    :+
                    :+                    -##:    .##+   -##:    .*#=  +#*.    -##.   .##:                       :+
                    :+                    =#*     .*#+   -#*      =##  ##-     :##.   .##:                       :+
                    :+                    -##+.  .-##+   -##-.  .:##-  +##:.  .+##.   .##:                       :+
                    :+                     .######*##+   -#**######-   .=######*##.   .##:                       :+
                    :+                       ....        -#*  ...         ....                                   :+
                    :+                                   -#*                                                     :+
                    :+                                   :*+                                                     :+
                    :+                                                                                           :+
                    :+                                                                                           :+
                    :+                                                                                           :+
                    :+                                                                                           :+
                    :+                                                                                           :+
                    :+....................                                                    ...................:+
                    ......................                                                    .....................
        ''')
    except Exception as e:
        print(f"Error displaying welcome message: {e}")

def display_farewell_message(execution_id = None):
    '''
    Displays a farewell message for the Apstra Provisioning Automation Framework.

    The message includes the current timestamp and, if provided, the execution ID.
    '''
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if execution_id:
            message = f"[bold green]Execution {execution_id} completed on {now}![/bold green] :sunglasses:"
        else:
            message = f"[bold green]Execution completed on {now}![/bold green] :sunglasses:"

        rprint(f"\n{message}\n")
        rprint("\n[bold green]See you![/bold green] :waving_hand:\n")

    except Exception as e:
        print(f"Error displaying farewell message: {e}")

def find_first_match_in_file(filepath, regex):
    '''
    Searches for the first occurrence of a regex in a file.

    Args:
        filepath (str): The path to the file.
        regex (str): The regex pattern to search for.

    Returns:
        str: The complete line containing the first match, or None if no match is found.
    '''
    try:
        # Open the file for reading
        with open(filepath, 'r') as file:
            # Read through each line
            for line in file:
                # Search for the regex in the line
                match = re.search(regex, line)
                if match:
                    return line  # Return the complete line containing the match

        # Return None if no match is found
        return None

    except FileNotFoundError:
        logger.error(f"❌ Error: The file at {filepath} was not found.")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return None

def split_file_on_first_match(input_filepath, pattern, output_before_filepath, output_after_filepath):
    '''
    Splits an input file into two output files based on the first occurrence of a regex pattern.

    Args:
        input_filepath (str): Path to the input file.
        pattern (str): The regex pattern to match.
        output_before_filepath (str): File to store content before the first match.
        output_after_filepath (str): File to store content from the first match onward.
    '''
    regex = re.compile(pattern)
    match_found = False

    try:
        with open(input_filepath, 'r') as input_file, \
             open(output_before_filepath, 'w') as before_file, \
             open(output_after_filepath, 'w') as after_file:

            for line in input_file:
                if not match_found and regex.search(line):
                    match_found = True  # First match found, switch to writing in 'after_file'
                if match_found:
                    after_file.write(line)
                else:
                    before_file.write(line)

    except FileNotFoundError:
        logger.error(f"❌ Error: File '{input_filepath}' not found.")
    except PermissionError:
        logger.error(f"❌ Error: Permission denied when accessing one of the files.")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

def clean_up_directory(folder_path):
    '''
    Cleans up the specified directory by removing it (along with its contents)
    and recreating it as an empty directory.

    Args:
        folder_path (str): Path to the folder to clean up.

    '''
    try:

        # Remove the folder and all its contents
        remove_directory(folder_path)

        # Recreate the folder as empty
        os.makedirs(folder_path, exist_ok=True)

    except Exception as e:
        logger.error(f"❌ Error while cleaning up the directory {folder_path}: {e}")

def replace_directory_contents(directory_a, directory_b):
    '''
    Removes all contents of directory A and replaces them with the contents of directory B.

    Args:
        directory_a (str): The path to directory A (to be replaced).
        directory_b (str): The path to directory B (contents to be copied).
    '''
    try:
        # Ensure directory A exists, create if not
        if not os.path.exists(directory_a):
            os.makedirs(directory_a)
        else:
            # Now clean up directory A (removes contents but leaves directory structure)
            clean_up_directory(directory_a)


        # Copy contents of directory B into directory A
        for item in os.listdir(directory_b):
            source = os.path.join(directory_b, item)
            destination = os.path.join(directory_a, item)

            # Prevent copying directory_a into itself if it's inside directory_b
            if os.path.commonpath([os.path.abspath(source), os.path.abspath(directory_a)]) == os.path.abspath(directory_a):
                continue

            if os.path.isfile(source):
                shutil.copy2(source, destination)
            elif os.path.isdir(source):
                shutil.copytree(source, destination)

        print("\n")
        logger.info(f"✅ Directory '{directory_a}' has been replaced with contents from '{directory_b}'.")

    except Exception as e:
        logger.error(f"❌ Error while replacing directory contents: {e}")

def parse_input_args():
    '''
    Parses the input arguments from the command line and returns them as a dictionary.
    Each argument should be in the form key=value.
    '''
    try:
        return dict(arg.split('=') for arg in sys.argv[1:])
    except ValueError as e:
        logger.error(f"❌ Error: Invalid input argument format. Ensure arguments are in the form key=value.")
        sys.exit(1)

def move_file(source_file_path, destination_file_path):
    '''
    Move a file from source to destination.
    If the destination directory does not exist, it will be created.
    If the destination file already exists, it will be overwritten.

    Args:
        source_file_path (str): Path to the source file.
        destination_file_path (str): Path where the file should be moved.
    '''
    try:
        # Check if the source file exists
        if not os.path.isfile(source_file_path):
            # logger.warning(f"❌ Source file {source_file_path} does not exist. Skipping operation.")
            return  # Exit the function early if the source file doesn't exist

        # Check if the directory of the destination file exists
        destination_dir = os.path.dirname(destination_file_path)
        if not os.path.isdir(destination_dir):
            # logger.warning(f"🔧 Destination directory {destination_dir} does not exist. Creating it.")
            os.makedirs(destination_dir)

        # Move the file (override if the destination exists)
        shutil.move(source_file_path, destination_file_path)
        logger.info(f"✅ File moved successfully to {destination_file_path}.")

    except PermissionError as perm_error:
        logger.error(f"❌ Permission error: {perm_error}")

    except Exception as e:
        logger.error(f"❌ Error while moving file: {e}")

def copy_file(source_file_path, destination_file_path):
    '''
    Copy a file from source to destination.
    If the destination directory does not exist, it will be created.
    If the destination file already exists, it will be overwritten.

    Args:
        source_file_path (str): Path to the source file.
        destination_file_path (str): Path where the file should be copied.
    '''
    try:
        # Check if the source file exists
        if not os.path.isfile(source_file_path):
            logger.warning(f"❌ Source file {source_file_path} does not exist. Skipping operation.")
            return  # Exit the function early if the source file doesn't exist

        # Check if the directory of the destination file exists
        destination_dir = os.path.dirname(destination_file_path)
        if not os.path.isdir(destination_dir):
            logger.warning(f"🔧 Destination directory {destination_dir} does not exist. Creating it.")
            os.makedirs(destination_dir)

        # Copy the file (override if the destination exists)
        shutil.copy2(source_file_path, destination_file_path)  # copy2 preserves metadata
        logger.info(f"✅ File copied successfully to {destination_file_path}.")

    except PermissionError as perm_error:
        logger.error(f"❌ Permission error: {perm_error}")

    except Exception as e:
        logger.error(f"❌ Error while copying file: {e}")

def run_command_and_save_stdout_stderr(command, stdout_file, stderr_file):
    '''
    Runs a shell command, displays stdout and stderr in real-time,
    and saves them to separate log files. Removes empty log files
    and cleans ANSI escape sequences if necessary.

    Args:
        command (list or str): The shell command to execute.
        stdout_file (str): Path to the file where stdout will be saved.
        stderr_file (str): Path to the file where stderr will be saved.

    Returns:
        int: The exit code of the command.
    '''
    try:
        # Open the output files for writing
        with open(stdout_file, 'w') as out_file, open(stderr_file, 'w') as err_file:

            # Start the subprocess with real-time output capturing
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Read stdout and stderr line by line
            for line in process.stdout:
                sys.stdout.write(line)  # Print to console in real-time
                out_file.write(line)  # Write to stdout file

            for line in process.stderr:
                sys.stderr.write(line)  # Print to console in real-time
                err_file.write(line)  # Write to stderr file

            # Wait for the process to complete
            process.wait()

        for filename in [stdout_file, stderr_file]:
            if os.path.exists(filename):
                if os.path.getsize(filename) == 0:
                    os.remove(filename)  # Remove empty file
                else:
                    remove_ansi_escape_sequences(filename) # Remove ANSI escape sequences from the file

        # # Check the exit code and return it
        # if process.returncode != 0:
        #     logger.error(f"❌ Command failed with exit code {process.returncode}", file=sys.stderr)
        # else:
        #     logger.info("✅ Command executed successfully")

        return process.returncode

    except FileNotFoundError:
        logger.error(f"❌ Error: Command '{command}' not found.", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1

def remove_ansi_escape_sequences(text_or_file):
    '''
    Removes ANSI escape sequences from a given text string or a file.

    ANSI escape sequences are used for terminal formatting (colors, bold, underlines, etc.).
    This function can either process a text string directly or clean a file if a filename is provided.

    Args:
        text_or_file (str): Either a text string or a filename.

    Returns:
        str: A cleaned string if input was text. If a filename was given, the function updates the file.
    '''

    # Regular expression pattern to match ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    if os.path.isfile(text_or_file):
        # Process the file
        with open(text_or_file, 'r', encoding='utf-8') as file:
            content = file.read()

        cleaned_content = ansi_escape.sub('', content)

        with open(text_or_file, 'w', encoding='utf-8') as file:
            file.write(cleaned_content)

        return f"ANSI escape sequences removed from '{text_or_file}'"

    # Process as a text string
    return ansi_escape.sub('', text_or_file)

def copy_from_pattern(input_file, output_file, pattern):
    '''
    Reads an input file, finds the first occurrence of the given regex pattern,
    and copies from that point to the end of the file into the output file.

    The output file is only created if there is content to write.

    Args:
        input_file (str): Path to the input file.
        output_file (str): Path to the output file.
        pattern (str): Regex pattern to search for.
    Returns:
        bool: True if the pattern was found and content copied, False otherwise.
    '''
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

        match_found = False
        content_to_write = []

        for line in lines:
            if not match_found and re.search(pattern, line):
                match_found = True
            if match_found:
                content_to_write.append(line)

        # Only create the output file and write content if there is something to write
        if match_found:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                outfile.writelines(content_to_write)
            # print(f"✅ Successfully copied content from '{input_file}' to '{output_file}' starting from pattern '{pattern}'.")
        else:
            # If no match was found, don't create the output file
            if os.path.exists(output_file):
                os.remove(output_file)
            # print(f"⚠️ Warning: Pattern '{pattern}' not found in '{input_file}'. Output file has been deleted.")

        return match_found

    except Exception as e:
        # Log or print the error message if needed
        print(f"❌ An error occurred: {e}")
        return False

def create_tfplan_summary(tfplan_file_json, tfplan_summary):
    '''
    Parses a Terraform plan JSON file and generates a summary of the changes, adding
    more details like the Terraform version, the Date/Time of execution, provider versions,
    and more.

    Args:
        tfplan_file_json (str): The JSON file containing Terraform plan data.
        tfplan_summary (str): The file to save the summary.

    Returns:
        None
    '''
    try:
        # Load the Terraform JSON plan
        with open(tfplan_file_json, "r") as f:
            plan_data = json.load(f)

        # Extract Terraform version and execution timestamp from metadata
        terraform_version = plan_data.get("terraform_version", "unknown")
        timestamp = plan_data.get("timestamp", "unknown")
        provider_version = plan_data.get("configuration", None).get("provider_config", None).get("apstra", None).get("version_constraint", None)

        # Convert timestamp to human-readable format
        try:
            execution_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            execution_datetime = timestamp

        # Extract changes summary
        summary = {"create": 0, "update": 0, "delete": 0}
        resource_changes = plan_data.get("resource_changes", [])

        # Grouped resource summaries
        resource_summary = {"create": {}, "update": {}, "delete": {}}

        for resource in resource_changes:
            actions = resource.get("change", {}).get("actions", [])
            resource_key = f"{resource.get('type', 'unknown')}.{resource.get('name', 'unknown')}"
            resource_index = resource.get("index", "unknown")

            for action in ["create", "update", "delete"]:
                if action in actions:
                    summary[action] += 1
                    resource_summary[action].setdefault(resource_key, []).append(resource_index)

        # Format the summary report


        header = (
            f"-----------------------------------\n"
            f"   🌍 Terraform Plan Summary 🌍    \n"
            f"-----------------------------------\n\n"
            f"📅 Execution Date/Time: {execution_datetime}\n"
            f"🔧 Terraform Version: {terraform_version}\n"
            f"🔌 Terraform Apstra Provider Version: {provider_version}\n\n"
        )
        
        summary = (
            f"📦 Resources to be Created: {summary['create']}\n"
            f"🔄 Resources to be Updated: {summary['update']}\n"
            f"❌ Resources to be Deleted: {summary['delete']}\n\n"
        )

        report = header

        flag_report = False
        for action in ["create", "update", "delete"]:
            if resource_summary[action]:
                flag_report = True
                report += f"** {action.capitalize()} Resources **\n"
                for resource, indices in resource_summary[action].items():
                    report += f"\n{resource}:\n"
                    for index in indices:
                        report += f"    - {index}\n"
                report += "\n"
        if flag_report:
            report += summary

        # Save the summary to a file
        with open(tfplan_summary, "w") as f:
            f.write(report)

        print("\n")
        logger.info(f"💾 Terraform Plan Summary saved to: {tfplan_summary}")

    except FileNotFoundError:
        logger.error(f"❌ Error: File {tfplan_file_json} not found.")
    except json.JSONDecodeError:
        logger.error("❌ Error parsing Terraform plan JSON output.")

def display_tfplan_summary(tfplan_file_summary):
    '''
    Displays the contents of the Terraform plan summary file created by
    the create_tfplan_summary function.

    Args:
        tfplan_file_summary (str): The file containing the Terraform plan summary.

    Returns:
        None
    '''
    try:
        with open(tfplan_file_summary, "r") as f:
            summary_content = f.read()

        # Display the summary content in the console
        print(summary_content)

    except FileNotFoundError:
        logger.error(f"❌ Error: The file {tfplan_file_summary} was not found.")
    except Exception as e:
        logger.error(f"❌ An error occurred while reading the file: {e}")

def monitor_command(command, rules):
    '''
    Runs a shell command, monitors its output for multiple patterns, and handles each according to its defined action.

    Args:
        command (str): The shell command to execute.
        rules (list of dict): List of rules, each containing:
            - 'pattern' (str): Regex pattern to match.
            - 'message' (str, optional): Message to show when pausing execution.
            - 'pattern_vs_message' (str, optional): Whether to stop 'before' or 'after' finding the pattern.
            - 'suppress_until' (str, optional): Regex pattern that resumes output display after suppression.

    Returns:
        None
    '''

    compiled_rules = [
        {
            "pattern": re.compile(rule["pattern"]),
            "message": rule.get("message"),
            "pattern_vs_message": rule.get("pattern_vs_message", "after"),  # Default to 'after'
            "suppress_until": re.compile(rule["suppress_until"]) if "suppress_until" in rule else None,
        }
        for rule in rules
    ]

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=sys.stdin, text=True)

    suppressing = None  # Tracks active suppression rule

    try:
        for line in process.stdout:
            pattern_matched = False

            # Suppression: skip printing lines if suppressing is active
            if suppressing:
                # Check if the suppression pattern is found to stop suppressing
                if suppressing.search(line):
                    suppressing = None  # Stop suppressing
                continue  # Skip printing the current line if suppression is active

            for rule in compiled_rules:
                if rule["pattern"].search(line):  # Pattern matched
                    pattern_matched = True

                    # Handle the action based on 'pattern_vs_message'
                    if rule["pattern_vs_message"] == "before":  # Display the line before message
                        print(line, end="")
                        if rule['message']:
                            logger.info(f"{rule['message']}")
                        # In interactive mode, prompt the user to press Enter to continue
                        if self.interactive:
                            input("⏭️  Press enter to continue...\n")
                    elif rule["pattern_vs_message"] == "after":  # Display the line after message
                        if rule['message']:
                            logger.info(f"{rule['message']}")
                        print(line, end="")
                        # In interactive mode, prompt the user to press Enter to continue
                        if self.interactive:
                            input("⏭️  Press enter to continue...\n")
                    # Apply suppression if 'suppress_until' is specified
                    if rule["suppress_until"]:
                        suppressing = rule["suppress_until"]
                    break  # Stop checking other rules once a match is found

            # If no pattern matched and no suppression, print the line
            if not suppressing and not pattern_matched:
                print(line, end="")

        process.wait()  # Ensure the process completes

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        process.terminate()

    # Reset terminal formatting to default
    subprocess.run('tput sgr0', shell=True)

def confirm_and_exit_on_no(question):
    '''
    Ask a yes or no question and exit the script if the answer is no.

    Args:
        question (str): The question to be asked.
    '''
    try:
        confirmation = Confirm.ask(question)
        assert confirmation, "Exiting script."
        print("\n")
    except AssertionError as e:
        logger.error(e)
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)

def prompt_for_confirmation(question):
    '''
    Ask a yes or no question and return the response.

    Args:
        question (str): The question to be asked.

    Returns:
        str: The user's response in lowercase ('yes' or 'no').
    '''
    try:
        while True:
            confirmation = input(f"{question} (yes/no or y/n): ").strip().lower()
            print("\n")

            if confirmation in {"yes", "y"}:
                return "yes"
            elif confirmation in {"no", "n"}:
                return "no"
            else:
                logger.error('❌ Invalid input. "yes", "no", "y", or "n".\n')

    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        return None

def remove_directory(directory):
    '''
    Safely removes a directory and all its contents.

    Args:
        directory (str): The path to the directory to be removed.

    Returns:
        bool: True if the directory was successfully removed, False otherwise.
    '''
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory, ignore_errors=True)
            logging.info(f"🚮 Successfully removed directory: {directory}")
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"❌ Failed to remove directory {directory}: {e}")
        return False

def remove_file(file_path):
    '''
    Safely removes a file if it exists.

    Args:
        file_path (str): The path to the file to be removed.

    Returns:
        bool: True if the file was successfully removed, False otherwise.
    '''
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            # logging.info(f"✅ Successfully removed file: {file_path}")
            return True
        else:
            # logging.warning(f"⚠️ File does not exist: {file_path}")
            return False
    except Exception as e:
        logging.error(f"❌ Failed to remove file {file_path}: {e}")
        return False

def get_direct_subdirectories(input_directory):
    '''
    Get all the directories directly contained within the input directory.

    Args:
        input_directory (str): Path to the input folder.

    Returns:
        list: A list of folder names directly contained within the input folder.

    '''
    subdirectories = [folder for folder in os.listdir(input_directory)
                  if os.path.isdir(os.path.join(input_directory, folder))]
    return subdirectories

def create_tgz_from_dir(folder_path, output_tgz_path):
    '''
    Create a .tgz file from the specified folder.
    The .tgz file is a tar archive that is compressed using gzip.

    Args:
        folder_path (str): The path to the folder to be tarred and gzipped.
        output_tgz_path (str): The path where the output .tgz file should be saved (without .tgz extension).

    Returns:
    None
    '''

    try:
        with tarfile.open(output_tgz_path, "w:gz") as tar:
            tar.add(folder_path, arcname=os.path.basename(folder_path))
    except FileNotFoundError as e:
        logger.error(f"❌ Error: The specified folder '{folder_path}' does not exist. {e}")
    except PermissionError as e:
        logger.error(f"❌ Error: Permission denied while accessing '{folder_path}' or '{output_tgz_path}'. {e}")
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred while crating a .tgz file: {e}")

def extract_tgz_to_dir(tgz_path, extract_path):
    '''
    Extract the contents of a .tgz file to the specified folder.

    Args:
        tgz_path (str): The path to the .tgz file to be extracted.
        extract_path (str): The path where the extracted files should be saved.

    Returns:
        bool: True if the .tgz file was successfully extracted, False otherwise.
    '''

    if os.path.exists(tgz_path):
        try:
            with tarfile.open(tgz_path, 'r:gz') as tar:
                tar.extractall(path=extract_path)
            return True
        except Exception as e:
            logger.error(f"❌ An error occurred while extracting {tgz_path}: {e}")
            return False
    else:
        return False

def update_yaml(yaml_file, *dicts):
    '''
    Update a YAML file by adding new dictionaries and replacing existing ones.

    Args:
        yaml_file (str): Path to the YAML file to be updated.
        *dicts (dict): Variable length argument list of dictionaries to add or update in the YAML file.

    Returns:
        None
    '''
    try:
        existing_data = {}
        if os.path.exists(yaml_file):
            with open(yaml_file, 'r') as f:
                existing_data = yaml.safe_load(f) or {}
        for d in dicts:
            existing_data.update(d)
        with open(yaml_file, 'w') as f:
            yaml.dump(existing_data, f, default_flow_style=False)
    except FileNotFoundError as e:
        logger.error(f"❌ Error: The file '{yaml_file}' was not found. {e}")
    except PermissionError as e:
        logger.error(f"❌ Error: Permission denied while accessing '{yaml_file}'. {e}")
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")

def rename_backup_files(file_path, keep_file=False, max_backups=9, tgz_backup_files=False):
    '''
    Rotate backup files with incremental indexes and optionally compress them.

    Args:
        file_path (str): Full path of the file.
        keep_file (bool, optional): If True, keeps the original file after backup. Defaults to False.
        max_backups (int, optional): Maximum number of backup files to keep. Defaults to 9.
        tgz_backup_files (bool, optional): If True, compresses backup files into a `.tgz` archive.
    '''
    try:
        if not os.path.exists(file_path):
            return  # Nothing to do if the file doesn't exist

        filename = os.path.basename(file_path)
        backup_dir = os.path.join(os.path.dirname(file_path), "_OLD")

        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)

        # Rotate existing backups (both `.bck.N` and `.bck.N.tgz`)
        for i in range(max_backups, 0, -1):
            current_backup = os.path.join(backup_dir, f"{filename}.bck.{i}")
            new_backup = os.path.join(backup_dir, f"{filename}.bck.{i + 1}")
            current_tgz = f"{current_backup}.tgz"
            new_tgz = f"{new_backup}.tgz"

            # Rotate backup files
            if os.path.exists(current_backup):
                os.rename(current_backup, new_backup)

            # Rotate compressed backups
            if os.path.exists(current_tgz):
                os.rename(current_tgz, new_tgz)

        # Move the current file as the first backup
        backup_path = os.path.join(backup_dir, f"{filename}.bck.1")
        os.rename(file_path, backup_path)

        if keep_file:
            shutil.copy(backup_path, file_path)

        # If compression is enabled, create a .tgz archive for each backup file
        if tgz_backup_files:
            tgz_path = f"{backup_path}.tgz"
            with tarfile.open(tgz_path, "w:gz") as tar:
                tar.add(backup_path, arcname=os.path.basename(backup_path))
            os.remove(backup_path)  # Remove individual backup file after compression

    except Exception as e:
        logger.error(f"❌ Error in rename_backup_files: {e}")

def create_output_file(content, file_path):
    '''
    Create an output file with the given content.

    Args:
        content (str): Content to write to the output file.
        file_path (str): Full path of the output file.

    Raises:
        IOError: If an error occurs while writing to the output file.

    '''
    try:
        # Rename backup files before creating a new output file
        rename_backup_files(file_path)

        # Write content to the output file
        with open(file_path, 'w') as output:
            output.write(content)
    except IOError as e:
        # Raise an IOError with a descriptive error message
        raise IOError(f'Error occurred while creating the output file: {e}')

def get_md5(file_path):
    '''
    Calculate the MD5 checksum of a file.

    Args:
        file_path (str): The path to the file for which the MD5 checksum is to be calculated.

    Returns:
        str: The MD5 checksum of the file as a hexadecimal string.
    '''
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def read_j2(file_path):
    '''
    Read a Jinja2 file and return its contents as a string.

    Args:
        file_path (str): The path to the Jinja2 file.

    Returns:
        str: The contents of the Jinja2 file as a string.
    '''
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"❌ An error occurred while reading {file_path}: {e}")
        return None

def read_yaml(file_path):
    '''
    Read a YAML file and return its contents.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The contents of the YAML file.
    '''

    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"❌ Error reading YAML file {file_path}: {e}")
        return None

def compare_j2(file_a, file_b):
    '''
    Compare two Jinja2 template (.j2) files using DeepDiff and return the differences.

    Args:
        file_a (str): The path to the first Jinja2 file.
        file_b (str): The path to the second Jinja2 file.

    Returns:
        dict: A dictionary containing the differences between the two Jinja2 files.
              The dictionary will have keys indicating the type of change (e.g., 'values_changed')
              and values describing the changes, or an 'error' key if any issue occurred.
    '''
    try:
        with open(file_a, 'r') as fa, open(file_b, 'r') as fb:
            template_a = fa.read()
            template_b = fb.read()
        differences = DeepDiff(template_a, template_b, ignore_order=True).to_dict()
        return differences
    except FileNotFoundError as fnf_error:
        logger.error(f"❌ File not found: {fnf_error}")
        return {"error": f"File not found: {fnf_error}"}
    except Exception as e:
        logger.error(f"❌ An error occurred while comparing {file_a} and {file_b}: {e}")
        return {"error": f"An error occurred while comparing {file_a} and {file_b}: {e}"}

def compare_yaml(file_a, file_b):
    '''
    Compare two YAML data (.yml or .yaml) files using DeepDiff and return the differences.

    Args:
        file_a (str): The path to the first YAML file.
        file_b (str): The path to the second YAML file.

    Returns:
        dict: A dictionary containing the differences between the two YAML files.
              The dictionary will have keys indicating the type of change (e.g., 'values_changed',
              'dictionary_item_added', etc.) and values describing the changes, or an 'error' key if any issue occurred.
    '''
    try:
        with open(file_a, 'r') as fa, open(file_b, 'r') as fb:
            data_a = yaml.safe_load(fa)
            data_b = yaml.safe_load(fb)
        differences = DeepDiff(data_b, data_a, ignore_order=True).to_dict()
        return differences
    except FileNotFoundError as fnf_error:
        logger.error(f"❌ File not found: {fnf_error}")
        return {"error": f"File not found: {fnf_error}"}
    except yaml.YAMLError as yaml_error:
        logger.error(f"❌ YAML error: {yaml_error}")
        return {"error": f"YAML error: {yaml_error}"}
    except Exception as e:
        logger.error(f"❌ An error occurred while comparing {file_a} and {file_b}: {e}")
        return {"error": f"An error occurred while comparing {file_a} and {file_b}: {e}"}

def get_value_at_path(data, path):
    '''
    Retrieve the value from a nested dictionary or list based on a given string path.

    Args:
        data (dict): The dictionary to search.
        path (str): The string representing the path to the desired value.

    Returns:
        The value at the specified path, or None if any part of the path is invalid.
    '''
    keys = re.findall(r"\['(.*?)'\]|\[(\d+)\]", path)

    try:
        for key in keys:
            if key[0]:  # it's a dictionary key
                data = data.get(key[0])
            else:  # it's a list index
                data = data[int(key[1])]
            if data is None:
                return None
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"❌ Error accessing path: {e}")
        return None
    return data

def extract_segments(path, num_segments):
    '''
    Extract the contents of a string path up to the end of the specified number of closing brackets.

    Args:
        path (str): The string representing the path.
        num_segments (int): The number of segments to extract, defined by the number of closing brackets ']'.

    Returns:
        str: The substring up to the end of the specified number of closing brackets, or an error message if the path is invalid.
    '''
    try:
        segments = path.split(']')
        return ']'.join(segments[:num_segments]) + ']'
    except Exception as e:
        logger.error(f"❌ Error extracting segments: {e}")
        return path

def find_nested_dict_entry(nested_dict, object_key, key, value):
    '''
    Find the second-level dictionary in a nested dictionary structure where the specified key has the given value.

    Args:
        nested_dict (dict): A dictionary where first-level keys are associated with lists of second-level dictionaries.
        object_key (str): The first-level key whose list of dictionaries to search.
        key (str): The key to look for in the second-level dictionaries.
        value (Any): The value to match for the specified key in the second-level dictionaries.

    Returns:
        dict: The second-level dictionary that matches the key-value pair,
              or None if no such dictionary is found or if the object_key does not exist.
    '''
    try:
        object_list = nested_dict.get(object_key, [])
        for entry in object_list:
            if entry.get(key) == value:
                return entry
        return None
    except Exception as e:
        logger.error(f"❌ Error processing the data: {e}")
        return None

def process_diff(diff, previous_file_path, current_file_path, configlet_name = None):

    '''
    Process the differences output from `compare_yaml` or `compare_j2` dictionary to categorize changes and return a structured dictionary.

    Args:
        diff (Dict): The dictionary containing differences output from the `compare_yaml` or `compare_j2` functions.
        previous_file_path (str): Path to the previous file.
        current_file_path (str): Path to the current file.
        configlet_name (Optional[str]): The name of the configlet, if the diff is related to a specific configlet contents.
                                        Defaults to None if not applicable.

    Returns:
        Dict: A dictionary where each key is an identifier (such as a field or section) and the value is another dictionary
              categorizing the changes into 'added', 'changed', and 'removed' keys. Each of these keys maps to the
              corresponding difference details.
    '''

    added_types = ['dictionary_item_added', 'iterable_item_added', 'attribute_added', 'set_item_added']
    changed_types = ['values_changed', 'type_changes', 'repetition_change']
    removed_types = ['dictionary_item_removed', 'iterable_item_removed', 'attribute_removed', 'set_item_removed']

    if configlet_name:
        previous_file = read_j2(previous_file_path)
        current_file = read_j2(current_file_path)
    else:
        previous_file = read_yaml(previous_file_path)
        current_file = read_yaml(current_file_path)

    try:
        results = {}
        for change_type, changes in diff.items():
            if change_type in added_types + changed_types + removed_types:
                list_objects_changed_names = []
                # This matches nearly all DeepDiff types (except for dictionary_item_added and dictionary_item_removed),
                # which are dictionaries containing the full contents of the modified fields.
                if isinstance(changes, dict):
                    for change, details in changes.items():
                        # If this is the first execution of the project, all the changes are additions
                        if change_type == 'type_changes' and change == 'root':
                            for change_first_exec, details_first_exec in details.get('new_value').items():
                                if change_first_exec not in results:
                                    results[change_first_exec] = {'added': [], 'changed': [], 'removed': []}
                                if isinstance(details_first_exec, list):
                                    results[change_first_exec]['added'].extend(details_first_exec)
                                elif isinstance(details_first_exec, dict):
                                    if 'user_defined' in details_first_exec:
                                        results[change_first_exec]['added'].extend(details_first_exec.get('user_defined'))
                        # If the diff to assess is between configlet versions
                        elif change_type == 'values_changed' and change == 'root':
                            if configlet_name:
                                apstra_object = 'configlet_contents'
                                if apstra_object not in results:
                                    results[apstra_object] = {'added': [], 'changed': [], 'removed': []}
                                change_detail = {'name': configlet_name} | details
                                results[apstra_object]['changed'].append(change_detail)
                                # results[apstra_object]['added'].append(change_detail)
                                # results[apstra_object]['removed'].append(change_detail)
                        else:
                            apstra_object = change.split("['")[1].split("']")[0]
                            if apstra_object not in results:
                                results[apstra_object] = {'added': [], 'changed': [], 'removed': []}
                            if change_type in changed_types:
                                previous_object = extract_segments(change.split('root')[1], 2)
                                changed_attribute = change.split('[')[-1].split(']')[0]
                                # If the changed attribute is the name, this is not a change but a removal + addition
                                if changed_attribute == "'name'":
                                    list_objects_changed_names.append(previous_object)
                                    previous_name = details.get('old_value', '')
                                    current_name = details.get('new_value', '')
                                    previous_entry = find_nested_dict_entry(previous_file, apstra_object, 'name', previous_name)
                                    current_entry = find_nested_dict_entry(current_file, apstra_object, 'name', current_name)
                                    if previous_entry and current_entry:
                                        results[apstra_object]['removed'].append(previous_entry)
                                        results[apstra_object]['added'].append(current_entry)
                                # If the changed attribute is NOT the name, this is a normal change, simply add the name to the details
                                else:
                                    # Ignore value changes in renamed objects
                                    if previous_object not in list_objects_changed_names:
                                        current_name = get_value_at_path(previous_file, previous_object + "['name']")
                                        change_detail = {'name': current_name} | details
                                        results[apstra_object]['changed'].append(change_detail)
                            elif change_type in added_types:
                                results[apstra_object]['added'].append(details)
                            elif change_type in removed_types:
                                results[apstra_object]['removed'].append(details)
                # This matches the two DeepDiff types (dictionary_item_added and dictionary_item_removed),
                # which are lists that do not contain the full contents of the modified fields.
                # As a result, it's necessary to access the specific entries in the diff and manually navigate through the nested items.
                else:
                    if change_type == 'dictionary_item_added' or change_type == 'dictionary_item_removed':
                        if change_type == 'dictionary_item_added':
                            with open(current_file_path, 'r') as f:
                                data_from_yaml = yaml.safe_load(f)
                        if change_type == 'dictionary_item_removed':
                            with open(previous_file_path, 'r') as f:
                                data_from_yaml = yaml.safe_load(f)
                        for change in changes:
                            apstra_object = change.split("['")[1].split("']")[0]
                            path = change.replace("root", "data_from_yaml")  # Convert DeepDiff path to Python dictionary path
                            details = eval(path)  # Safely evaluate the path to get the added value
                            if apstra_object not in results:
                                results[apstra_object] = {'added': [], 'changed': [], 'removed': []}
                            if isinstance(details, list):
                                if change_type == 'dictionary_item_added':
                                    results[apstra_object]['added'].extend(details)
                                if change_type == 'dictionary_item_removed':
                                    results[apstra_object]['removed'].extend(details)
        return results
    except Exception as e:
        logger.error(f"❌ Error processing the diff: {e}")
        return {}

def rename_file_if_exists(source_path, target_path):
    '''
    Renames the source file to the target file name if the source file exists.
    If the target file already exists, it will be removed before renaming.

    Args:
        source_path (str): The path to the file to be renamed.
        target_path (str): The new path for the renamed file.

    Returns:
        bool: True if the file was renamed successfully, False otherwise.
    '''
    try:
        if os.path.exists(source_path):
            # Remove the target file if it already exists
            if os.path.exists(target_path):
                os.remove(target_path)
                logger.info(f"🗑️  Existing file removed: {target_path}")

            # Rename the source file to the target file path
            os.rename(source_path, target_path)
            logger.info(f"📄 File renamed: {source_path} -> {target_path}")
            return True
        # else:
        #     logger.error(f"❌ File not found: {source_path}")
        #     return False
    except Exception as e:
        logger.error(f"❌ Error renaming file: {e}")
        return False

    return False  # Return False if source file does not exist

def compare_directories(dir1, dir2):
    '''
    Compare the contents of two directories, including files and subdirectories.
    This function reports the differences in files (files only in one directory,
    differing files, and identical files) and recursively compares common subdirectories.

    Args:
        dir1 (str): The path to the first directory.
        dir2 (str): The path to the second directory.

    Returns:
        tuple: A tuple containing four lists:
            - left_only (list): Files only in the first directory.
            - right_only (list): Files only in the second directory.
            - diff_files (list): Files that are in both directories but differ.
            - same_files (list): Files that are in both directories and are identical.
    '''
    # Compare the two directories
    dir_comparison = filecmp.dircmp(dir1, dir2)

    # print(f"Comparing {dir1} and {dir2}\n")

    # Report differences in files
    left_only = dir_comparison.left_only
    right_only = dir_comparison.right_only
    diff_files = dir_comparison.diff_files
    same_files = dir_comparison.same_files

    # Recursively compare common subdirectories
    for sub_dir in dir_comparison.common_dirs:
        sub_dir1 = os.path.join(dir1, sub_dir)
        sub_dir2 = os.path.join(dir2, sub_dir)
        compare_directories(sub_dir1, sub_dir2)

    return left_only, right_only, diff_files, same_files

def list_directory_contents(directory_path):
    '''
    List all files and directories in the specified directory.
    This function prints the names of all entries (files and directories) in the given directory.

    Args:
        directory_path (str): The path to the directory to list the contents of.

    Raises:
        FileNotFoundError: If the specified directory does not exist.
        PermissionError: If the program does not have permission to access the directory.
        Exception: For any other exceptions that may occur during directory access.
    '''
    try:
        # List all files and directories in the specified path
        with os.scandir(directory_path) as entries:
            for entry in entries:
                print(entry.name)
    except FileNotFoundError:
        print(f"The directory {directory_path} does not exist.")
    except PermissionError:
        print(f"Permission denied to access the directory {directory_path}.")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_templates():
    '''
    Get the Templates from the AOS API.

    Returns:
        dict: Template data if successful, otherwise an empty dictionary.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/design/templates'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to retrieve Templates - {e}")
        return {}

def get_rack_types():
    '''
    Get the Rack Type from the AOS API.

    Returns:
        dict: Rack Type data if successful, otherwise an empty dictionary.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/design/rack-types'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to retrieve Rack Type - {e}")
        return {}

def get_logical_devices():
    '''
    Get the Logical Devices from the AOS API.

    Returns:
        dict: Logical Device data if successful, otherwise an empty dictionary.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/design/logical-devices'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to retrieve Logical Devices - {e}")
        return {}

def get_interface_maps():
    '''
    Get the Interface Maps from the AOS API.

    Returns:
        dict: Interface Map data if successful, otherwise an empty dictionary.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/design/interface-maps'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to retrieve Interface Maps - {e}")
        return {}

def get_property_sets():
    '''
    Get the property-sets from the AOS API.

    Returns:
        dict: Property-set data if successful, otherwise an empty dictionary.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/property-sets'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve property-sets - {e}")
        return {}

def get_configlets():
    '''
    Get the configlets from the AOS API.

    Returns:
        dict: Configlet data if successful, otherwise an empty dictionary.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/design/configlets'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
        return response.json()

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve configlets - {e}")
        return {}

def get_ip_pools():
    '''
    Get the IP Pools from the AOS API.

    Returns:
        dict: IP Pool data if successful, otherwise an empty dictionary.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/resources/ip-pools'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Will raise HTTPError for bad responses (4xx, 5xx)
        return response.json()

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve IP Pools - {e}")
        return {}

def get_ipv6_pools():
    '''
    Get the IPv6 Pools from the AOS API.

    Returns:
        dict: IPv6 Pool data if successful, otherwise an empty dictionary.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/resources/ipv6-pools'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Will raise HTTPError for bad responses (4xx, 5xx)
        return response.json()

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve IPv6 Pools - {e}")
        return {}

def get_vni_pools():
    '''
    Get the VNI Pools from the AOS API.

    Returns:
        dict: VNI Pool data if successful, otherwise an empty dictionary.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/resources/vni-pools'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to retrieve VNI Pools - {e}")
        return {}

def get_asn_pools():
    '''
    Get the ASN Pools from the AOS API.

    Returns:
        dict: ASN Pool data if successful, otherwise an empty dictionary.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/resources/asn-pools'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code
        return response.json()

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve ASN Pools - {e}")
        return {}

def get_template_id(template_name):
    '''
    Get the Template ID from the AOS API for a given Template.

    Args:
        template_name (str): Template name.

    Returns:
        str: Template ID, or None if not found or an error occurs.
    '''
    try:
        data = get_templates()
        for item in data.get('items', []):
            if item.get('display_name') == template_name:
                return item.get('id')
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve Template ID for '{template_name}' - {e}")
        return None

def get_rack_type_id(rack_type_name):
    '''
    Get the Rack Type ID from the AOS API for a given Rack Type.

    Args:
        rack_type_name (str): Rack Type name.

    Returns:
        str: Rack Type ID, or None if not found or an error occurs.
    '''
    try:
        data = get_rack_types()
        for item in data.get('items', []):
            if item.get('display_name') == rack_type_name:
                return item.get('id')
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve Rack Type ID for '{rack_type_name}' - {e}")
        return None

def get_logical_device_id(logical_device_name):
    '''
    Get the Logical Device ID from the AOS API for a given Logical Device.

    Args:
        logical_device_name (str): Logical Device name.

    Returns:
        str: Logical Device ID, or None if not found or an error occurs.
    '''
    try:
        data = get_logical_devices()
        for item in data.get('items', []):
            if item.get('display_name') == logical_device_name:
                return item.get('id')
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve Logical Device ID for '{logical_device_name}' - {e}")
        return None

def get_interface_map_id(interface_map_name):
    '''
    Get the Interface Map ID from the AOS API for a given Interface Map.

    Args:
        interface_map_name (str): Interface Map name.

    Returns:
        str: Interface Map ID, or None if not found or an error occurs.
    '''
    try:
        data = get_interface_maps()
        for item in data.get('items', []):
            if item.get('label') == interface_map_name:
                return item.get('id')
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve Interface Map ID for '{interface_map_name}' - {e}")
        return None

def get_property_set_id(property_set_name):
    '''
    Get the Property Set ID from the AOS API for a given Property Set.

    Args:
        property_set_name (str): Property Set name.

    Returns:
        str: Property Set ID, or None if not found or an error occurs.
    '''
    try:
        data = get_property_sets()
        for item in data.get('items', []):
            if item.get('label') == property_set_name:
                return item.get('id')
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve Property Set ID for '{property_set_name}' - {e}")
        return None

def get_configlet_id(configlet_name):
    '''
    Get the Configlet ID from the AOS API for a given Configlet.

    Args:
        configlet_name (str): Configlet name.

    Returns:
        str: Configlet ID, or None if not found or an error occurs.
    '''
    try:
        data = get_configlets()
        for item in data.get('items', []):
            if item.get('display_name') == configlet_name:
                return item.get('id')
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve Configlet ID for '{configlet_name}' - {e}")
        return None

def get_ip_pool_id(ip_pool_name):
    '''
    Get the IP Pool ID from the AOS API for a given IP Pool.

    Args:
        ip_pool_name (str): IP Pool name.

    Returns:
        str: IP Pool ID, or None if not found or an error occurs.
    '''
    try:
        data = get_ip_pools()
        for item in data.get('items', []):
            if item.get('display_name') == ip_pool_name:
                return item.get('id')
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve IP Pool ID for '{ip_pool_name}' - {e}")
        return None

def get_ipv6_pool_id(ipv6_pool_name):
    '''
    Get the IPv6 Pool ID from the AOS API for a given IPv6 Pool.

    Args:
        ipv6_pool_name (str): IP Pool name.

    Returns:
        str: IP Pool ID, or None if not found or an error occurs.
    '''
    try:
        data = get_ipv6_pools()
        for item in data.get('items', []):
            if item.get('display_name') == ipv6_pool_name:
                return item.get('id')
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve IPv6 Pool ID for '{ipv6_pool_name}' - {e}")
        return None
    
def get_vni_pool_id(vni_pool_name):
    '''
    Get the VNI Pool ID from the AOS API for a given VNI Pool.

    Args:
        vni_pool_name (str): VNI Pool name.

    Returns:
        str: VNI Pool ID, or None if not found or an error occurs.
    '''
    try:
        data = get_vni_pools()
        for item in data.get('items', []):
            if item.get('display_name') == vni_pool_name:
                return item.get('id')
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve VNI Pool ID for '{vni_pool_name}' - {e}")
        return None

def get_asn_pool_id(asn_pool_name):
    '''
    Get the ASN Pool ID from the AOS API for a given ASN Pool.

    Args:
        asn_pool_name (str): ASN Pool name.

    Returns:
        str: ASN Pool ID, or None if not found or an error occurs.
    '''
    try:
        data = get_asn_pools()
        for item in data.get('items', []):
            if item.get('display_name') == asn_pool_name:
                return item.get('id')
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve ASN Pool ID for '{asn_pool_name}' - {e}")
        return None

def delete_template(template_id):
    '''
    Delete a template by its ID.

    Args:
        template_id (str): Template ID.

    Returns:
        bool: True if deleted successfully, False otherwise.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/design/templates/{template_id}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.delete(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code

        return response.status_code == 204

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to delete Template - {e}")
        return False

def delete_rack_type(rack_type_id):
    '''
    Delete a rack_type by its ID.

    Args:
        rack_type_id (str): Rack Type ID.

    Returns:
        bool: True if deleted successfully, False otherwise.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/design/rack-types/{rack_type_id}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.delete(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code

        return response.status_code == 204

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to delete Rack Type - {e}")
        return False

def delete_logical_device(logical_device_id):
    '''
    Delete a logical_device by its ID.

    Args:
        logical_device_id (str): Logical Device ID.

    Returns:
        bool: True if deleted successfully, False otherwise.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/design/logical-devices/{logical_device_id}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.delete(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code

        return response.status_code == 200

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to delete Logical Device - {e}")
        return False

def delete_interface_map(interface_map_id):
    '''
    Delete a interface_map by its ID.

    Args:
        interface_map_id (str): Interface Map ID.

    Returns:
        bool: True if deleted successfully, False otherwise.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/design/interface-maps/{interface_map_id}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.delete(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code

        return response.status_code == 200

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to delete Interface Map - {e}")
        return False

def delete_property_set(property_set_id):
    '''
    Delete a property-set by its ID.

    Args:
        property_set_id (str): Property-set ID.

    Returns:
        bool: True if the property set was deleted successfully (status code 204), False otherwise.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/property-sets/{property_set_id}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.delete(url, headers=headers, verify=False)

        if response.status_code == 204:
            return True
        else:
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)

    except Exception as e:
        logger.error(f"❌ Error: Failed to delete Property Set - {e}")
        return None

def delete_configlet(configlet_id):
    '''
    Delete a configlet by its ID.

    Args:
        configlet_id (str): Configlet ID.

    Returns:
        bool: True if the configlet is successfully deleted, False otherwise.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/design/configlets/{configlet_id}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.delete(url, headers=headers, verify=False)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx, 5xx)

        if response.status_code == 204:
            # logger.info(f"✅ Configlet with ID '{configlet_id}' successfully deleted.")
            return True
        else:
            return False

    except Exception as e:
        logger.error(f'❌ Error: Failed to delete configlet - {e}')

def delete_ip_pool(ip_pool_id):
    '''
    Delete an IP Pool by its ID.

    Args:
        ip_pool_id (str): IP Pool ID.

    Returns:
        bool: True if deleted successfully, False otherwise.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/resources/ip-pools/{ip_pool_id}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.delete(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code

        return response.status_code == 202
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to delete IP Pool - {e}")
        return False

def delete_vni_pool(vni_pool_id):
    '''
    Delete a vni_pool by its ID.

    Args:
        vni_pool_id (str): VNI Pool ID.

    Returns:
        bool: True if deleted successfully, False otherwise.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/resources/vni-pools/{vni_pool_id}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.delete(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code

        return response.status_code == 202

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to delete VNI Pool - {e}")
        return False

def delete_asn_pool(asn_pool_id):
    '''
    Delete an ASN Pool by its ID.

    Args:
        asn_pool_id (str): ASN Pool ID.

    Returns:
        bool: True if deleted successfully, False otherwise.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/resources/asn-pools/{asn_pool_id}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.delete(url, headers=headers, verify=False)
        response.raise_for_status()  # Raise error for any bad status code

        return response.status_code == 202
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error: Failed to delete ASN Pool - {e}")
        return False

def remove_non_bp_added(input_diff):
    '''
    Remove added non-blueprint items from the Apstra design and resources menus

    Args:
        input_diff (dict): The dictionary containing the differences between YAML files, structured by menu and Apstra object.

    Returns:
        None

    Raises:
        Exception: If an error occurs during the processing of blueprint changes.
    '''

    try:
        print("\n")
        logger.info("🗑️  Initiating the cleanup process for objects created in Design/Resources in this execution...")

        interface_maps_to_remove = []  # Store interface maps to ensure they are removed first

        for menu, apstra_objects in input_diff.items():
            for apstra_object, change_types in apstra_objects.items():
                added_list = change_types.get('added', [])
                changed_list = change_types.get('changed', [])

                if added_list:

                    for added in added_list:
                        added_name = added.get('name', None)
                        if added_name:
                            if menu == 'design':
                                if apstra_object == 'interface_maps':
                                    interface_maps_to_remove.append(added_name)  # Store interface maps first

        # First, remove all interface_maps before logical_devices
        for interface_map_name in interface_maps_to_remove:
            interface_map_id = get_interface_map_id(interface_map_name)
            if delete_interface_map(interface_map_id):
                logger.info(f'🚮 Removed from Apstra via API: design -> interface_maps -> {interface_map_name}')

        # Now, process the remaining objects
        for menu, apstra_objects in input_diff.items():
            for apstra_object, change_types in apstra_objects.items():
                added_list = change_types.get('added', [])
                changed_list = change_types.get('changed', [])

                if added_list:
                    for added in added_list:
                        added_name = added.get('name', None)
                        if added_name:
                            if menu == 'design':
                                if apstra_object == 'templates':
                                    template_id = get_template_id(added_name)
                                    if delete_template(template_id):
                                        logger.info(f'🚮 Removed from Apstra via API: {menu} -> {apstra_object} -> {added_name}')
                                elif apstra_object == 'racks':
                                    rack_type_id = get_rack_type_id(added_name)
                                    if delete_rack_type(rack_type_id):
                                        logger.info(f'🚮 Removed from Apstra via API: {menu} -> {apstra_object} -> {added_name}')
                                elif apstra_object == 'logical_devices':  # Safe to delete after deleting interface_maps
                                    logical_device_id = get_logical_device_id(added_name)
                                    if delete_logical_device(logical_device_id):
                                        logger.info(f'🚮 Removed from Apstra via API: {menu} -> {apstra_object} -> {added_name}')
                                elif apstra_object == 'configlets':
                                    configlet_id = get_configlet_id(added_name)
                                    if delete_configlet(configlet_id):
                                        logger.info(f'🚮 Removed from Apstra via API: {menu} -> {apstra_object} -> {added_name}')
                                elif apstra_object == 'property_sets':
                                    property_set_id = get_property_set_id(added_name)
                                    if delete_property_set(property_set_id):
                                        logger.info(f'🚮 Removed from Apstra via API: {menu} -> {apstra_object} -> {added_name}')
                            elif menu == 'resources':
                                if apstra_object == 'ipv4_pools':
                                    ip_pool_id = get_ip_pool_id(added_name)
                                    if delete_ip_pool(ip_pool_id):
                                        logger.info(f'🚮 Removed from Apstra via API: {menu} -> {apstra_object} -> {added_name}')
                                elif apstra_object == 'ipv6_pools':
                                    ipv6_pool_id = get_ipv6_pool_id(added_name)
                                    if delete_ipv6_pool(ipv6_pool_id):
                                        logger.info(f'🚮 Removed from Apstra via API: {menu} -> {apstra_object} -> {added_name}')
                                elif apstra_object == 'vni_pools':
                                    vni_pool_id = get_vni_pool_id(added_name)
                                    if delete_vni_pool(vni_pool_id):
                                        logger.info(f'🚮 Removed from Apstra via API: {menu} -> {apstra_object} -> {added_name}')
                                elif apstra_object == 'asn_pools':
                                    asn_pool_id = get_asn_pool_id(added_name)
                                    if delete_asn_pool(asn_pool_id):
                                        logger.info(f'🚮 Removed from Apstra via API: {menu} -> {apstra_object} -> {added_name}')

                elif changed_list and apstra_object == 'configlet_contents':
                    print("\n")
                    logger.info("🗑️  Removing configlets which contents have changed in Design:")
                    for configlet_name in [d["name"] for d in changed_list if "name" in d]:
                        configlet_id = get_configlet_id(configlet_name)
                        if delete_configlet(configlet_id):
                            logger.info(f'🚮 Removed from Apstra via API: {menu} -> {apstra_object} -> {configlet_name}')

    except Exception as e:
        logger.error(f"❌ Error removing Apstra objects: {e}")

def revert_apstra_config_except_blueprints(current_tgz, previous_tgz):
    '''
    Roll back the configuration of the Apstra sections other than blueprints.

    This function untars the provided current and previous tgz files,
    and for each section ('resources' and 'design'), compares their YAML files
    and performs the necessary rollback actions.

    Args:
        current_tgz (str): Path to the current tgz file.
        previous_tgz (str): Path to the previous tgz file.

    Returns:
        None
    '''

    current_dir = tempfile.mkdtemp()
    previous_dir = tempfile.mkdtemp()

    try:
        extract_tgz_to_dir(current_tgz, current_dir)

        if not extract_tgz_to_dir(previous_tgz, previous_dir):
            logger.warning(f"📝 {previous_tgz} not found. Creating temporary empty YAML files instead.")

            for menu in non_blueprint_menus:
                empty_yaml_path = os.path.join(previous_dir, "input", menu, f"{menu}.yml")
                os.makedirs(os.path.dirname(empty_yaml_path), exist_ok=True)
                with open(empty_yaml_path, "w") as f:
                    pass  # Creates an empty YAML file

        for menu in non_blueprint_menus:
            current_yaml = os.path.join(current_dir, "input", menu, f"{menu}.yml")
            previous_yaml = os.path.join(previous_dir, "input", menu, f"{menu}.yml")

            # print("*** CURRENT ***")
            # print(current_yaml)
            # with open(current_yaml, 'r') as file:
            #     contents = yaml.safe_load(file)
            #     print(yaml.dump(contents, default_flow_style=False))

            # print("*** PREVIOUS ***")
            # print(os.path.exists(current_yaml))
            # print(previous_yaml)
            # with open(previous_yaml, 'r') as file:
            #     contents = yaml.safe_load(file)
            #     print(yaml.dump(contents, default_flow_style=False))
            # print(os.path.exists(previous_yaml))

            if os.path.exists(current_yaml) and os.path.exists(previous_yaml):
                compare_yaml(current_yaml, previous_yaml)

    finally:
        # Cleanup directories safely
        for directory in [current_dir, previous_dir]:
            remove_directory(directory)

def filter_none_values(input_data):
    '''
    Filter out key-value pairs from a dictionary where the values are None,
    or filter out None values from a list.

    Args:
        input_data (dict or list): The input dictionary or list to be filtered.

    Returns:
        dict or list: A new dictionary with key-value pairs where the values are not None,
                      or a new list with elements where the values are not None.
    '''
    if isinstance(input_data, dict):
        return {key: value for key, value in input_data.items() if value is not None}
    elif isinstance(input_data, list):
        return [item for item in input_data if item is not None or []]
    else:
        raise ValueError("Input must be a dictionary or a list.")

def yamldecode(file_path):
    '''
    Decode a YAML file and return its contents as a dictionary.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict: Contents of the YAML file as a dictionary or an empty dictionary if an error occurs.
    '''
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file) or {}  # Return an empty dict if YAML is empty
    except FileNotFoundError:
        logger.error(f"❌ Error: The file '{file_path}' was not found.")
    except yaml.YAMLError as e:
        logger.error(f"❌ Error parsing YAML file '{file_path}': {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while reading '{file_path}': {e}")

    return {}  # Return an empty dictionary on error

def merge_yaml_files(*args):
    '''
    Merge YAML files or dictionaries into a single YAML string.

    Args:
        *args (dict or str): Variable number of YAML dictionaries or file paths to be merged.

    Returns:
        str: Merged YAML content as a string.
    '''
    merged_yaml = ''
    try:
        for arg in args:
            if isinstance(arg, dict):
                merged_yaml += yaml.dump(arg, Dumper=NoAliasDumper)
            elif isinstance(arg, str):
                with open(arg, 'r') as file:
                    for line in file:
                        merged_yaml += line
    except Exception as e:
        raise ValueError(f'Error occurred while merging YAML files: {e}')
    return merged_yaml

def json2yaml(file_json, file_yaml):
    '''
    Convert a JSON file to YAML format.

    Args:
        file_json (str): Path to the JSON file.
        file_yaml (str): Path to save the YAML file.

    Returns:
        bool: True if the conversion was successful. False otherwise.
    '''
    try:
        with open(file_json, 'r') as inp:
            jsonData = json.load(inp)
            # print(jsonData)
        with open(file_yaml, 'w') as outp:
            yaml.safe_dump(jsonData, outp, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f'❌ Error: Failed to convert JSON to YAML - {e}')
        return False

def yaml2json(file_yaml, file_json):
    '''
    Convert a YAML file to JSON format.

    Args:
        file_yaml (str): Path to the YAML file.
        file_json (str): Path to save the JSON file.

    Returns:
        bool: True if the conversion was successful. False otherwise.
    '''
    try:
        with open(file_yaml, 'r') as inp:
            yamlData = yaml.safe_load(inp)
            # print(yamlData)
        with open(file_json, 'w') as outp:
            json.dump(yamlData, outp, indent=4)
        return True
    except Exception as e:
        logger.error(f'❌ Error: Failed to convert YAML to JSON - {e}')
        return False

def get_ip(ip, prefixlen):
    '''
    Get the IP address object given an IP address and prefix length.

    Args:
        ip (str): The IP address.
        prefixlen (str): The prefix length. Must be between 0 or 32 (both inclusive).

    Returns:
        ip/prefixlen (str): The IP address and the prefix length if both valid, else returns None.

    '''
    if ip != None and prefixlen != None:
        try:
            if int(prefixlen) not in range(0, 33):
                raise ValueError("Prefix length must be between 0 and 32")
            return f'{ip}/{prefixlen}'
        except:
            return None
    else:
        return None

def get_peer_ip(ip, prefixlen):
    '''
    Get the peer IP address given an IP address and prefix length.

    Args:
        ip (str): The IP address.
        prefixlen (str): The prefix length. Must be 30 or 31.

    Returns:
        ip/prefixlen (str): The peer IP address and the prefix length if both valid, else returns None.

    Raises:
        ValueError: If the prefix length is not 30 or 31.

    '''
    if get_ip(ip, prefixlen) != None:
        if int(prefixlen) not in range(30, 32):
            raise ValueError("Prefix length must be 30 or 31")
        ip_object = ipaddress.ip_interface(f'{ip}/{prefixlen}')
        net_object = ipaddress.ip_network(f'{ip}/{prefixlen}', strict=False)
        hosts=list(net_object.hosts())
        if ip_object.ip == hosts[0]:
            peer_ip = f'{str(hosts[1])}/{prefixlen}'
        elif ip_object.ip == hosts[1]:
            peer_ip = f'{str(hosts[0])}/{prefixlen}'
        return peer_ip
    else:
        return None

def get_design_switch_name(blueprint_device_name, blueprint_data):
    '''
    Get the design device name associated with the given blueprint device name from blueprint data.

    Args:
        blueprint_device_name (str): The blueprint device name to search for.
        blueprint_data (dict): The blueprint data obtained from decoding the blueprint yaml file.

    Returns:
        str or None: The design device name corresponding to the provided blueprint device name, or None if not found.
    '''
    try:
        for switch in blueprint_data['switches']:
            if switch['blueprint_device_name'].upper() == blueprint_device_name.upper():
                initial_device_name = switch['initial_device_name']
        return initial_device_name
    except:
        return None

def get_blueprint_switch_name(initial_device_name, blueprint_data):
    '''
    Get the blueprint device name associated with the given design device name from blueprint data.

    Args:
        initial_device_name (str): The design device name to search for.
        blueprint_data (dict): The blueprint data obtained from decoding the blueprint yaml file.

    Returns:
        str or None: The blueprint device name corresponding to the provided design device name, or None if not found.
    '''
    try:
        for switch in blueprint_data['switches']:
            if switch['initial_device_name'].upper() == initial_device_name.upper():
                blueprint_device_name = switch['blueprint_device_name']
        return blueprint_device_name

    except:
        return None

def get_aos_variables(data, target_value):
    '''
    Extracts specific variables from a dictionary for a given target value.

    Args:
        data (dict): YAML data loaded into a dictionary.
        target_value (str): The target value to search for in the dictionary.

    Returns:
        tuple or str: A tuple containing the values associated with 'ip', 'username', and 'password' for the target.

    Raises:
        Error: If the target is not found in the list.
    '''
    for item in data.get('aos', []):  # Iterate over each item in the 'aos' list
        if item.get('target') == target_value:  # Check if the 'target' matches the input target value
            return item.get('ip'), item.get('username'), item.get('password')  # Return IP, username, and password
    logger.error(f"❌ AOS target '{target_value}' not found in the list.")  # Raise exception if target not found
    sys.exit()

def get_terraform_command(input_params):
    '''
    Determines the Terraform command and whether it is either an apply or a destroy based on user input.

    Args:
        input_params (dict): Dictionary containing input parameters.

    Returns:
        tuple: A tuple containing:
            - is_terraform_apply (bool): Whether the command is an apply command.
            - is_terraform_destroy (bool): Whether the command is a destroy command.
            - str: The Terraform command to execute.
    '''
    try:
        command = input_params.get("command")

        if not command:
            raise ValueError("At least one Terraform command must be specified when executing the script: python3 main.py command=<terraform_command>")

        terraform_command = terraform_commands.get(command)
        if terraform_command is None:
            raise ValueError("❌ Invalid Terraform command")

        is_terraform_apply = command in terraform_commands_apply
        is_terraform_destroy = command in terraform_commands_destroy

        return is_terraform_apply, is_terraform_destroy, terraform_command

    except ValueError as e:
        logger.error(str(e))
        print_choices(terraform_commands)
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ An unexpected error occurred while retrieving the Terraform command: {e}")
        sys.exit(1)

def build_table_deploy(terraform_command, uncommitted_bps, action, commit_comment, stage, non_bp_menus_w_changes=None):
    '''
    Display the deployment information in a table format

    Args:
        terraform_command (str): The Terraform command to execute (e.g., 'terraform apply' or 'terraform destroy').
        uncommitted_bps (list): A list of dictionaries with blueprint names and staged versions.
        action (str): The action to perform:
            - "revert": Revert to previous state.
            - "commit": Commit the staged version with a provided commit comment.
            - "not_commit": Do not commit changes.
        commit_comment (str): Comment for deploying the staged version of the blueprint.
        stage (str): The stage of deployment:
            - 'initial': Initial deployment phase.
            - 'final': Final deployment phase.
        non_bp_menus_w_changes (str or None, optional): Information about changes in menus other than Blueprints,
            applicable only in the 'final' stage.

    Returns:
        Table: A Rich Table object with deployment information.

    Raises:
        Exception: If any error occurs during the processing or display of the deployment information.

    '''

    # Validate stage parameter
    if stage not in ['initial', 'final']:
        raise ValueError(f" ❌ Invalid stage '{stage}'. Stage must be 'initial' or 'final'.")

    try:
        if stage == 'initial':
            title = 'CHANGES PENDING TO BE COMMITTED FROM A PREVIOUS EXECUTION'
        elif stage == 'final':
            title = 'CHANGES MADE IN THE CURRENT EXECUTION'
        table = Table(
            Column(header="Feature", justify="right", style="cyan"),
            Column(header="Value", justify="center", style="magenta"),
            title=title,
            box=box.HEAVY_EDGE,
        )
        table.show_header = False
        table.title_justify = "center"
        table.title_style = "cyan underline"

        if 'terraform apply' in terraform_command:
            if stage == 'final' and non_bp_menus_w_changes:
                table.add_row("Non-Blueprint sections with changes", str(non_bp_menus_w_changes))

            if not uncommitted_bps:
                table.add_row("Blueprints with uncommitted staging versions", "-")
            else:
                table.add_row("Blueprints with uncommitted staging versions", str(uncommitted_bps))

        table.add_row(f"Commit comment", commit_comment)

        if non_bp_menus_w_changes or uncommitted_bps or 'terraform destroy' in terraform_command:
            table.add_row(f"Action to perform", action)

        return table
    except Exception as e:
        logger.error(f"❌ Error printing blueprint deployment information: {e}")

def print_panel_deploy_handling_plan (table_deploy, panel_title):
    '''
    Display the deploy handling plan in a formatted panel

    Args:
        table_deploy (Table): The table containing the BP deployment info.

    Returns:
        None

    '''
    panel = Panel.fit(
        Columns([
            table_deploy,
        ]),
        title=f"[bold]{panel_title}",
        border_style="red",
        title_align="left",
    )

    rprint(panel)

def display_menu(options):
    '''
    Display a menu of options for the user to choose from.

    Args:
        options (list of str): A list of strings to be displayed as menu options.

    Returns:
        int: The selected option number based on the user's input.

    Raises:
        ValueError: If the user's input is not a valid number.
    '''

    for i, option in enumerate(options, start=1):
        rprint(f'{i}. {option}')

    while True:
        try:
            print("\n")
            choice = int(input('🔢 Enter the option number: '))
            if 1 <= choice <= len(options):
                return choice
            else:
                logger.error(f'❌ Invalid option. Please enter a number between 1 and {len(options)}.')
        except ValueError:
            logger.error('❌ Invalid input. Please enter a number.')

def multi_option(options):
    '''
    Display a menu of options and return the selected option.

    Args:
        options (list of str): A list of strings to be displayed as menu options.

    Returns:
        str: The selected option string based on the user's input.

    Raises:
        Exception: If an error occurs during the menu selection process.
    '''
    try:
        opt = display_menu (options)
        return(options[opt - 1])
    except Exception as e:
        logger.error(f"❌ {e}")
        raise

def multi_option_choices(options):
    '''
    Prompt the user to enter a choice from a given list of options.

    Args:
        options (list of str): A list of strings to be displayed as valid choices.

    Returns:
        str: The selected option string based on the user's input.

    Raises:
        Exception: If an error occurs during the prompt process.
    '''
    try:
        while True:
            formatted_options = ' / '.join(options)
            rprint(f'\n:pencil: Enter your choice ( {formatted_options} ):')
            option_entered = input()
            if option_entered in options:
                return option_entered
            else:
                print('\r')
                logger.error(f'❌ Invalid option ({option_entered}) not within the valid choices ({formatted_options}). Try again...')
    except Exception as e:
        logger.error(f"❌ {e}")
        raise

def print_choices(input_data):
    '''
    Display a list of choices in a formatted panel.

    Args:
        input_data (list or dict): A list of strings or a dictionary with values representing the choices to display.

    Returns:
        None

    '''
    try:
        if isinstance(input_data, dict):
            input_list = [f'{key} --> {value}' for key, value in sorted(input_data.items())]
        elif isinstance(input_data, list):
            input_list = sorted(input_data)
        else:
            raise ValueError("Input must be a list or dictionary")

        list_of_panel_columns = [Panel(f"[red]{item}", border_style="red") for item in input_list]
        print("\n")
        columns = Columns(
            list_of_panel_columns,
            equal=True,
            align="center"
        )

        panel = Panel.fit(
            columns,
            title="[bold]VALID CHOICES",
            border_style="red",
            title_align="left",
        )

        rprint(panel)

    except Exception as e:
        logger.error(f"❌ Error displaying choices: {e}")

def get_aos_token ():
    '''
    Authenticate with the AOS API and retrieve the authentication token.

    Returns:
    - str: Authentication token for AOS API.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_username = sm.get('aos_username')
        aos_password = sm.get('aos_password')
        url = f'https://{aos_ip}/api/aaa/login'
        # url = f'https://{aos_ip}/api/user/login'
        data = json.dumps({"username": aos_username, "password": aos_password})
        headers = {'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.post(url, data=data, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()['token']
    except Exception as e:
        logger.error(f'❌ Error: Authentication failed - {e}')

def get_bp_id(bp_name):
    '''
    Get the blueprint ID from the AOS API using a given blueprint name.

    Args:
        bp_name (str): Blueprint name.

    Returns:
        str: Blueprint ID.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/blueprints'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        if 'items' in data and isinstance(data['items'], list) and data['items']:
            for item in data['items']:
                if item['label'] == bp_name:
                    return item['id']
        return None
    except Exception as e:
        logger.error(f'❌ Error: Failed to retrieve blueprint ID - {e}')
        return None

def get_bp_name(bp_id):
    '''
    Get the blueprint name from the AOS API using a given blueprint ID.

    Args:
        bp_id (str): Blueprint ID.

    Returns:
        str: Blueprint ID.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/blueprints'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        for item in data['items']:
            if item['id'] == bp_id:
                return item['label']
    except Exception as e:
        logger.error(f'❌ Error: Failed to retrieve blueprint name - {e}')

def validate_commit_actions(pre_commit_action, post_commit_action):
    '''
    Validate the pre and post commit actions.

    Args:
        pre_commit_action (str): Action to execute for blueprints with uncommitted changes BEFORE the execution of the script.
        post_commit_action (str): Action to execute for blueprints with uncommitted changes AFTER the execution of the script.
    '''
    valid = True
    if pre_commit_action not in pre_commit_actions:
        print("\r")
        logger.error(f"❌ Invalid action specified for blueprints with uncommitted changes BEFORE the execution of the script ({pre_commit_action}).")
        print_choices(pre_commit_actions)
        valid = False
    if post_commit_action not in post_commit_actions:
        print("\r")
        logger.error(f"❌ Invalid action specified for blueprints with uncommitted changes AFTER the execution of the script ({post_commit_action}).")
        print_choices(post_commit_actions)
        valid = False
    if not valid:
        sys.exit()

def validate_terraform_command(terraform_command):
    '''
    Validate the Terraform command.

    Args:
        terraform_command (str): Terraform command.
    '''
    valid = True
    if terraform_commands.get(terraform_command) is None:
        print("\r")
        logger.error(f"❌ Invalid Terraform command.")
        print_choices(terraform_commands)
        valid = False
    if not valid:
        sys.exit()

def build_errors_in_uncommitted_bps(uncommitted_bps_w_errors):
    '''
    Verify if there are build errors in the list of blueprints with uncommitted changes.

    Args:
        uncommitted_bps_w_errors (list of dicts): A list of dictionaries containing blueprint names and their build error counts.

    Returns:
        there_are_build_errors (boolean): True if there are build errors on any blueprints of the input list.

    '''
    try:
        print("\n")
        if uncommitted_bps_w_errors:
            logger.error(f"🔴 Some blueprints have build errors that prevent them from being committed:\n")
            return True
        else:
            logger.info("🟢 No blueprints in the current project have build errors that prevent them from being committed.")
            return False
    except Exception as e:
        logger.error(f"❌ An error occurred while analyzing if there are uncommitted blueprints with build errors: {e}")

def rollback_bp(bp_name, revision=1):

    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = get_aos_token()
        bp_id = get_bp_id(bp_name)
        list_bp_revisions = sm.get_bp_revision_list(bp_name)
        rollback = False
        if len(list_bp_revisions) >= revision:
            bp_revision = list_bp_revisions[int(f'-{revision}')]
            rollback = True
        elif len(list_bp_revisions) == 1:
            bp_revision = list_bp_revisions[-1]
            rollback = True
        if rollback == True:
            url = f'https://{aos_ip}/api/blueprints/{bp_id}/rollback'
            data = json.dumps({'revision_id' : bp_revision['revision_id']})
            headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
            response = requests.post(url, headers=headers, data=data, verify=False)
            response.raise_for_status()
            if response.status_code == 202:
                logger.info(f'Blueprint {bp_name} rolled back to revision id {bp_revision["revision_id"]} created by {bp_revision["user"]} ({bp_revision["user_ip"]}) at {bp_revision["created_at"]} with the comment: {bp_revision["description"]}')
                return True
            else:
                return False
    except Exception as e:
        logger.error(f"❌ Error: Failed to roll back to a previous revision of blueprint '{bp_name}' - {e}")

def get_rack_id(bp_name, rack_name):
    '''
    Get the rack ID from the AOS API for a given rack from a blueprint.

    Args:
        bp_name (str): Blueprint name.
        rack_name (str): Rack name.

    Returns:
        str: Rack ID.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/racks'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Ensure status code is 2xx

        data = response.json()
        for item in data['items']:
            if item['label'] == rack_name:
                return item['rack_id']  # Return the rack ID if found

        # If rack_name not found in response
        return None

    except Exception as e:
        logger.error(f"❌ Error: Failed to retrieve rack ID - {e}")
        return None

def get_dev_model(chassis_sn):
    '''
    Get the device model information from the AOS API for a given chassis serial number.

    Args:
        chassis_sn (str): Chassis serial number.

    Returns:
        str: Device model information.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/webcons/Main/aos/v0/device/deployment/config/{chassis_sn}/field/deviceModel'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.text.split("\n", 4)[4].rsplit("\n", 4)[0]
    except Exception as e:
        logger.error(f'❌ Error: Failed to retrieve device model - {e}')

def get_cabling_map(bp_name):
    '''
    Get the cabling map information from the AOS API for a given blueprint.

    Args:
        bp_name (str): Blueprint name.

    Returns:
        str: Cabling Map information.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/experience/web/cabling-map'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f'❌ Error: Failed to retrieve cabling map - {e}')

def get_subinterfaces(bp_name):
    '''
    Get the subinterface information from the AOS API for a given blueprint.

    Args:
        bp_name (str): Blueprint name.

    Returns:
        str: Subinterface information.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/experience/web/subinterfaces'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        else:
            raise
    except Exception as e:
        logger.error(f'❌ Error: Failed to retrieve subinterfaces - {e}')

def upload_cabling_map(bp_name, cabling_map_json):
    '''
    Upload the cabling map information to the AOS API for a given blueprint.

    Args:
        bp_name (str): Blueprint name.
        cabling_map_json (dict): JSON data containing the updated cabling map information.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/cabling-map'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.patch(url, headers=headers, data=cabling_map_json, verify=False)
        return response.status_code == 204
    except Exception as e:
        logger.error(f'❌ Error: Failed to upload cabling map - {e}')
        return False

def delete_rack(bp_name, rack_name):
    '''
    Delete a rack from a blueprint by its ID.

    Args:
        bp_name (str): Blueprint name.
        rack_name (str): Rack name.

    Returns:
        bool: True if the rack was successfully deleted, False otherwise.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        rack_id = get_rack_id(bp_name, rack_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/delete-racks'

        data = json.dumps({'racks_to_delete': [rack_id]})
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.post(url, headers=headers, data=data, verify=False)

        return response.status_code == 201

    except Exception as e:
        logger.error(f"❌ Error: An unexpected error occurred while deleting rack {rack_id} from blueprint {bp_id} - {e}")
        return False

def update_subinterfaces(bp_name, ip_dict):
    '''
    Update subinterfaces on interfaces which are part of a physical link with 'to_generic' role.

    Args:
        bp_name (str): Blueprint name.
        ip_dict (dict): Dictionary with the interface IDs and the IP addresses assigned to each of them.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/subinterfaces'
        data = json.dumps({'subinterfaces' : ip_dict})
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.patch(url, headers=headers, data=data, verify=False)
        response.raise_for_status()
        return response.status_code == 204
    except Exception as e:
        logger.error(f'❌ Error: Failed to update the IP addressing of an external link - {e}')

def get_non_bp_changes_tgz(current_tgz, previous_tgz):
    '''
    Identify and list the Apstra sections other than blueprints that have changes between two specific executions.

    Args:
        current_tgz (str): Path to the current TGZ file.
        previous_tgz (str): Path to the previous TGZ file.

    Returns:
        non_bp_menus_with_changes (list): List of menu sections that have changes.
        all_non_bp_diff (dict): Dictionary where each key is a menu and its value categorizes changes into
                                'added', 'changed', and 'removed'.
    '''

    if not current_tgz:
        logger.warning("❌ Missing current TGZ file. No comparison will be performed.")
        return [], {}

    current_dir = tempfile.mkdtemp()
    previous_dir = tempfile.mkdtemp()

    try:

        extract_tgz_to_dir(current_tgz, current_dir)
        if previous_tgz:
            extract_tgz_to_dir(previous_tgz, previous_dir)

        # Call function to get non-blueprint changes
        non_bp_menus_w_changes, all_non_bp_diff = get_non_bp_changes(current_dir, previous_dir)
        return non_bp_menus_w_changes, all_non_bp_diff

    except Exception as e:
        logger.error(f"❌ Error processing TGZ files: {e}")
        return [], {}

def get_non_bp_changes(current_dir, previous_dir):
    '''
    Identify and list the Apstra sections other than blueprints that have changes between two specific executions.

    Args:
        current_dir (str): Path to the current execution directory.
        previous_dir (str): Path to the previous execution directory.

    Returns:
        non_bp_menus_with_changes (list): List of menu sections that have changes.
        all_non_bp_diff (dict): Dictionary where each key is a menu and its value categorizes changes into
                                'added', 'changed', and 'removed'.
    '''

    try:
        non_bp_menus_with_changes = []
        all_non_bp_diff = {}

        for menu in non_blueprint_menus:
            current_yaml = os.path.join(current_dir, "input", menu, f"{menu}.yml")
            previous_yaml = os.path.join(previous_dir, "input", menu, f"{menu}.yml")

            # Ensure previous YAML exists to avoid FileNotFoundError
            # Use case: when no previous executions exist in the project
            if not os.path.exists(previous_yaml):
                os.makedirs(os.path.dirname(previous_yaml), exist_ok=True)
                with open(previous_yaml, 'w'):
                    pass

            if os.path.exists(current_yaml):
                all_configlet_diff = {"configlet_contents": {}} if menu == "design" else {}
                first_iter_configlets = True

                if menu == "design":
                    dict_configlets = {
                        configlet.get("name"): configlet.get("generators", [{}])[0].get("template_file")
                        for configlet in yamldecode(current_yaml).get("configlets", [])
                    }

                    for configlet_name, configlet_filename in dict_configlets.items():
                        current_configlet = os.path.join(current_dir, "input", "design", "configlets", configlet_filename)
                        previous_configlet = os.path.join(previous_dir, "input", "design", "configlets", configlet_filename)

                        if os.path.exists(previous_configlet) and os.path.exists(current_configlet):
                            if get_md5(current_configlet) != get_md5(previous_configlet):
                                j2_comparison = compare_j2(previous_configlet, current_configlet)
                                if j2_comparison:
                                    configlet_diff = process_diff(j2_comparison, previous_configlet, current_configlet, configlet_name=configlet_name)
                                    if first_iter_configlets:
                                        all_configlet_diff = configlet_diff
                                        first_iter_configlets = False
                                    else:
                                        for key, value in configlet_diff["configlet_contents"].items():
                                            all_configlet_diff["configlet_contents"].setdefault(key, []).extend(value)

                # Detect changes in YAML files for both 'resources' and 'design' sections
                if get_md5(current_yaml) != get_md5(previous_yaml):
                    non_bp_menus_with_changes.append(menu)
                    yaml_comparison = compare_yaml(current_yaml, previous_yaml)
                    if yaml_comparison:
                        non_bp_diff = process_diff(yaml_comparison, previous_yaml, current_yaml)
                        if menu == "design" and not first_iter_configlets:
                            non_bp_diff.update(all_configlet_diff)
                    all_non_bp_diff[menu] = non_bp_diff
                elif menu == "design" and not first_iter_configlets:
                    non_bp_menus_with_changes.append(menu)
                    all_non_bp_diff[menu] = all_configlet_diff

        return non_bp_menus_with_changes, all_non_bp_diff

    except Exception as e:
        logger.error(f"❌ Error processing non-blueprint changes: {e}")
        return [], {}

    finally:
        # Cleanup directories safely
        for directory in [current_dir, previous_dir]:
            remove_directory(directory)

def display_non_bp_changes(non_bp_menus_with_changes, all_non_bp_diff):
    '''
    Display changes in non-blueprint Apstra sections.

    Args:
        non_bp_menus_with_changes (list): List of menu sections with changes.
        all_non_bp_diff (dict): Dictionary of changes categorized by 'added', 'changed', and 'removed'.
    '''

    if not non_bp_menus_with_changes or not all_non_bp_diff:
        logger.info("✅ No non-blueprint changes to display\n")
        return

    for menu in non_bp_menus_with_changes:
        try:
            non_bp_diff = all_non_bp_diff.get(menu, {})
            table_changes_count, table_changes = build_table_changes(non_bp_diff)
            print_panel_non_bp_diff(menu, table_changes_count, table_changes)
        except Exception as e:
            logger.error(f"❌ Error displaying non-blueprint changes for '{menu}': {e}")

def get_device_info(bp_names=[], bp_path=''):
    '''
    Retrieve device information from blueprints YAML files.

    Device keys are retrieved from the "switches" map in the <bp>.yml files if the "device_key" exists.
    If no key is found, the default value is set to None.

    Args:
        bp_names (list, optional): A list of blueprint names.
        bp_path (str, optional): The path to the blueprints.

    Returns:
        dict: A dictionary containing device information for each blueprint.
              The structure is {blueprint_name: {initial_device_name: {device_key, bp_device_hostname}}}.
    '''
    device_info = {}

    try:
        for bp_name in bp_names:
            bp_data = yamldecode(os.path.join(bp_path, f'{bp_name}.yml'))
            device_info[bp_name] = {}

            if 'switches' in bp_data:
                for switch in bp_data['switches']:
                    initial_device_name = switch.get('initial_device_name', None)
                    if initial_device_name:
                        device_info[bp_name][initial_device_name] = {
                            'device_key': switch.get('device_key', None),
                            'bp_device_hostname': switch.get('blueprint_device_name', None)
                        }

    except Exception as e:
        logger.error(f"❌ An error occurred while retrieving device information: {e}")

    return device_info

def get_all_devices():
    '''
    Retrieve device information from the AOS API.

    Returns:
        list: A list of dictionaries containing device details (ID, hostname, full data).
              Returns an empty list if no devices are found.
    '''

    # logger.info(f"🔍 Fetching device details.")

    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')

        # API request to fetch all system details
        url = f'https://{aos_ip}/api/systems'
        headers = {
            'AuthToken': aos_token,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()

        # Process the response and extract relevant device data
        data = response.json()
        devices = []
        for item in data.get('items', []):
            devices.append({
                'device_id': item.get('id'),  # Unique device identifier
                'hostname': item.get('status', {}).get('hostname'),  # Device hostname
                'blueprint_id': item.get('status', {}).get('blueprint_id'), # Blueprint identifier
                'blueprint_name': get_bp_name(item.get('status', {}).get('blueprint_id')), # Blueprint identifier
                'device_data': item,  # Full device details
            })
        return devices

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error: Unable to retrieve device info: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: Failed to retrieve device info: {e}")

    return []

def get_bp_devices(bp_list):
    '''
    Retrieve device data only for those associated with a list of blueprints.

    Args:
        bp_list (list): List of blueprint names.

    Returns:
        list: A list of dictionaries containing device details (ID, hostname, full data).
              Returns an empty list if no devices are found.
    '''
    try:

        if not isinstance(bp_list, list) or not bp_list:
            return []

        # Check if any blueprint has bound devices before calling get_all_devices() (time saver)
        if not any(get_bp_device_ids(bp_name) for bp_name in bp_list):
            logger.info(f"🚫 No devices found bound to the specified blueprints: {bp_list}")
            return []

        # Get all devices
        all_devices = get_all_devices()

        # Filter devices belonging to any of the specified blueprints
        filtered_devices = [device for device in all_devices if device.get('blueprint_name') in bp_list]
        if not filtered_devices:
            logger.info(f"🚫 No devices found bound to the given blueprints: {bp_list}")
            return []

        return filtered_devices

    except Exception as e:
        logger.error(f"❌ Unexpected error while retrieving devices bound to the blueprints {bp_list}: {e}")

    return []

def get_device_id(bp_name, hostname):
    '''
    Retrieve the device ID of a specific device within a given blueprint.

    Args:
        bp_name (str): Name of the blueprint.
        hostname (str): Hostname of the target device.

    Returns:
        str: The device ID if found, otherwise None.
    '''
    try:
        devices = get_all_devices()

        for device in devices:
            if device.get("hostname") == hostname and device.get("blueprint_name") == bp_name:
                return device.get("device_id")

        logger.warning(f"🚫 Device '{hostname}' not found in blueprint '{bp_name}'.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error: Unable to retrieve device ID for '{hostname}' in '{bp_name}' - {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: Failed to retrieve device ID for '{hostname}' in '{bp_name}' - {e}")

    return None

def get_bp_device_ids(bp_name):
    '''
    Retrieve the list of device ids bound to a blueprint.

    Args:
        bp_name (str): Blueprint name.

    Returns:
        list: A list of device-ids for those bound to a blueprint.
              Returns an empty list if no devices are found.
    '''
    try:

        if not bp_name:
            return []

        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)

        if not bp_id:
            return []

        url = f'https://{aos_ip}/api/blueprints/{bp_id}/systems'
        headers = {
            'AuthToken': aos_token,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()

        # Process the response and extract relevant device data
        data = response.json()
        devices = []
        for item in data.get('items', []):
            devices.append(item.get('system_id'))
        return devices

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error: Unable to retrieve device info for blueprint '{bp_name}': {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: Failed to retrieve device info for blueprint '{bp_name}': {e}")

    return []

def get_device_config_context(bp_name, device_id, hostname):
    '''
    Retrieve the config_context of a specific device.

    Args:
        bp_name (str): Blueprint name.
        device_id (str): Device ID (aka system ID).
        hostname (str): Device hostname.

    Returns:
        dict: Device configuration data if successful, otherwise an empty dictionary.
    '''
    try:
        logger.info(f"🔍🔧 Fetching context for '{hostname}' (blueprint '{bp_name}')...")

        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/systems/{device_id}/config-context'
        headers = {
            'AuthToken': aos_token,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while retrieving context for '{hostname}' (blueprint '{bp_name}'): {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while retrieving context for '{hostname}' (blueprint '{bp_name}'): {e}")

    return {}

def get_device_config_incremental(bp_name, device_id, hostname):

    '''
    Retrieve the config_incremental of a specific device.

    Args:
        bp_name (str): Blueprint name.
        device_id (str): Device ID (aka system ID).
        hostname (str): Device hostname.

    Returns:
        dict: Device configuration data if successful, otherwise an empty dictionary.
    '''
    try:
        logger.info(f"🔍📶 Fetching config_incremental for '{hostname}' (blueprint '{bp_name}')...")

        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/systems/{device_id}/config-incremental'
        headers = {
            'AuthToken': aos_token,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while retrieving config_incremental for '{hostname}' (blueprint '{bp_name}'): {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while retrieving config_incremental for '{hostname}' (blueprint '{bp_name}'): {e}")

    return {}

def get_device_config_rendering(bp_name, device_id, hostname):
    '''
    Retrieve the config_rendering of a specific device.

    Args:
        bp_name (str): Blueprint name.
        device_id (str): Device ID (aka system ID).
        hostname (str): Device hostname.

    Returns:
        dict: Device configuration data if successful, otherwise an empty dictionary.
    '''
    try:
        logger.info(f"🔍📸 Fetching config_rendering for '{hostname}' (blueprint '{bp_name}')...")

        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/systems/{device_id}/config-rendering'
        headers = {
            'AuthToken': aos_token,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while retrieving config_rendering for '{hostname}' (blueprint '{bp_name}'): {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while retrieving config_rendering for '{hostname}' (blueprint '{bp_name}'): {e}")

    return {}

def get_device_config(bp_name, device_id, hostname):
    '''
    Retrieve the configuration of a specific device from the AOS API.

    Args:
        bp_name (str): Blueprint name.
        device_id (str): Device ID (aka system ID).
        hostname (str): Device hostname.

    Returns:
        dict: Device configuration data if successful, otherwise an empty dictionary.
    '''
    try:
        logger.info(f"🔍🛠️  Fetching config for '{hostname}' (blueprint '{bp_name}')...")

        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/systems/{device_id}/configuration'
        headers = {
            'AuthToken': aos_token,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        }

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while retrieving config for '{hostname}' (blueprint '{bp_name}'): {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while retrieving config for '{hostname}' (blueprint '{bp_name}'): {e}")

    return {}

def get_device_data(bp_list):
    '''
    Retrieve the data of devices from specified blueprints from the AOS API.

    Args:
        bp_list (list): A list of blueprint names.

    Returns:
        list: A list of dictionaries containing relevant device data.
    '''
    logger.info("🔍 Retrieving device data from Apstra...\n")

    all_device_data = []  # Store all collected data

    try:
        # Get all devices from the specified blueprints
        devices = get_bp_devices(bp_list)

        for device in devices:

            hostname = device.get("hostname")
            device_id = device.get("device_id")
            blueprint_name = device.get("blueprint_name")
            blueprint_id = device.get("blueprint_id")

            device_data = {
                "hostname": hostname,
                "device_id": device_id,
                "blueprint_name": blueprint_name,
                "blueprint_id": blueprint_id,
                "device_data": device.get("device_data"),
                "config": get_device_config(blueprint_name, device_id, hostname),
                "config_context": get_device_config_context(blueprint_name, device_id, hostname),
                # "config_incremental": get_device_config_incremental(blueprint_name, device_id, hostname),
                # "config_rendering": get_device_config_rendering(blueprint_name, device_id, hostname),
            }
            all_device_data.append(device_data)

        return all_device_data  # Return collected device data

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while retrieving device data from Apstra: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while retrieving device data from Apstra: {e}")

def get_all_blueprint_data():
    '''
    Get the deploy status from the AOS API for all blueprints.

    Returns:
        list: A list of dictionaries containing relevant blueprint data.
    '''
    try:
        sm = Scope_Manager()
        aos_token = sm.get('aos_token')
        aos_ip = sm.get('aos_ip')
        url = f'https://{aos_ip}/api/blueprints'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f'❌ Error: Failed to retrieve data from all blueprints - {e}')
        return []

def get_blueprint_data(bp_list, silent_mode = False):
    '''
    Retrieve the data of specified blueprints from the AOS API.

    Args:
        bp_list (list): A list of blueprint names.
        silent_mode (bool): Whether to display logging info or not.

    Returns:
        list: A list of dictionaries containing relevant blueprint data.
    '''

    if not silent_mode:
        print("\n")
        logger.info("🔍 Retrieving blueprint data from Apstra...")

    all_bp_data = []  # Store all collected data

    try:
        # Get data from all the blueprints
        data = get_all_blueprint_data()

        for bp_name in bp_list:
            for item in data.get('items', []):
                if item.get('label') == bp_name:
                    all_bp_data.append(item)

        return all_bp_data  # Return collected bp data

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while retrieving data for blueprint '{bp_name}' from Apstra: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while retrieving data for blueprint '{bp_name}' from Apstra: {e}")

    return {}

def get_bp_diff_status(bp_name):
    '''
    Retrieve the computation status of the diff between staged and deployed/operation blueprint.

    Args:
        bp_name (str): Blueprint name.

    Returns:
        dict: A dictionary containing the diff status with the following keys:
            * deploy_error
            * deployed_version
            * cache_diff_supported
            * deploy_config_version
            * operation_version
            * deploy_status_version
            * status
            * deploy_status
            * logical_diff_supported
            * staging_version
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/diff-status'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f'❌ Error: Failed to retrieve diff status - {e}')

def get_bp_diff(bp_name, mode = 'full'):
    '''
    Retrieve diff between staged and deployed blueprint.

    Args:
        bp_name (str): Blueprint name.
        mode (str): (optional) Three different modes are supported with varying amount of details:
            * 'digest' - only counts how many nodes or links changed
            * 'lite' - (default) includes digest and logical diff, but only ids and labels of changed elements
            * 'full' - digest and full logical diff

    Returns:
        dict: A dictionary containing the diff data with the following keys:
            * aaa_server
            * cabling_map
            * catalog
            * configlet
            * digest
            * endpoint_policies
            * enforcement_points_group
            * evpn_interconnect_groups
            * external_endpoint
            * external_endpoints_group
            * fabric_policy
            * floating_ips
            * interface_policy
            * internal_endpoint
            * internal_endpoints_group
            * policy
            * property_set
            * protocol_sessions
            * redundancy_group_port_channels
            * remote_gateway
            * routing_policies
            * routing_zone_constraint
            * security_zone
            * security_zones_group
            * static_routes
            * system_info
            * validation_policy
            * virtual_infra
            * virtual_network
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/diff?mode={mode}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f'❌ Error: Failed to retrieve diff status - {e}')

def build_table_bp_diff_status(bp_diff_status):
    '''
    Build a table to display blueprint configuration versions.

    Args:
        bp_diff_status (dict): Dictionary containing blueprint diff status information.

    Returns:
        Table: A table displaying deployed and staging versions of the blueprint configuration.

    Raises:
        Exception: If an error occurs during the printing of blueprint diff status information.
    '''
    try:
        title = f'BLUEPRINT CONFIG VERSIONS'
        table = Table(
            Column(header="Feature", justify="right", style="cyan"),
            Column(header="Value", justify="center", style="magenta"),
            title=title,
            box=box.HEAVY_EDGE,
        )
        table.show_header = False
        table.title_justify = "center"
        table.title_style = "cyan underline"
        table.add_row("Deployed version", str(bp_diff_status.get('deployed_version')))
        table.add_row("Staging version", str(bp_diff_status.get('staging_version','-')))
        return table
    except Exception as e:
        logger.error(f"❌ Error printing blueprint diff status information: {e}")

def build_table_bp_summary_changes(bp_diff):
    '''
    Build a summary table to display the total counts of added, changed, and removed nodes and relationships per Apstra blueprint.

    Args:
        bp_diff (dict): The dictionary containing the blueprint differences.

    Returns:
        Table: A table summarizing the counts of added, changed, and removed items.

    Raises:
        Exception: If an error occurs during the processing of blueprint summary changes.
    '''
    try:

        node_added = bp_diff.get('digest', {}).get('node', {}).get('added', 0)
        relationship_added = bp_diff.get('digest', {}).get('relationship', {}).get('added', 0)
        total_added = node_added + relationship_added
        node_changed = bp_diff.get('digest', {}).get('node', {}).get('changed', 0)
        relationship_changed = bp_diff.get('digest', {}).get('relationship', {}).get('changed', 0)
        total_changed = node_changed + relationship_changed
        node_removed = bp_diff.get('digest', {}).get('node', {}).get('removed', 0)
        relationship_removed = bp_diff.get('digest', {}).get('relationship', {}).get('removed', 0)
        total_removed = node_removed + relationship_removed

        title = f'SUMMARY OF CHANGES'
        table = Table(
            Column(header="Feature", justify="right", style="cyan"),
            Column(header="Value", justify="center", style="magenta"),
            title=title,
            box=box.HEAVY_EDGE,
        )
        table.show_header = False
        table.title_justify = "center"
        table.title_style = "cyan underline"
        table.add_row("Added", str(total_added))
        table.add_row("Changed", str(total_changed))
        table.add_row("Removed", str(total_removed))
        return table
    except Exception as e:

        logger.error(f"❌ Error printing blueprint summary of changes information: {e}")

def build_table_changes(input_diff):
    '''
    Build tables to display the scope and description of changes per Apstra object.

    Args:
        input_diff (dict): The dictionary containing the differences.

    Returns:
        tuple: A tuple containing two tables:
        table_count: Table summarizing the count of added, changed, and removed items per Apstra object.
        table: Table providing detailed YAML descriptions of added, changed, and removed items per Apstra object.

    Raises:
        Exception: If an error occurs during the processing of blueprint changes.
    '''
    try:
        title_count = f'SCOPE OF CHANGES PER APSTRA OBJECT'
        table_count = Table(
            Column(header="Apstra Object", justify="right", style="cyan"),
            Column(header="Added", justify="center", style="magenta"),
            Column(header="Changed", justify="center", style="magenta"),
            Column(header="Removed", justify="center", style="magenta"),
            title=title_count,
            box=box.HEAVY_EDGE,
        )
        table_count.show_header = True
        table_count.title_justify = "center"
        table_count.title_style = "cyan underline"

        title = f'DESCRIPTION OF CHANGES PER APSTRA OBJECT'
        table = Table(
            Column(header="Apstra Object", justify="right", style="cyan"),
            Column(header="Added", justify="left", style="magenta"),
            Column(header="Changed", justify="left", style="magenta"),
            Column(header="Removed", justify="left", style="magenta"),
            title=title,
            box=box.HEAVY_EDGE,
        )
        table.show_header = True
        table.title_justify = "center"
        table.title_style = "cyan underline"
        table.show_lines=True

        for apstra_object in input_diff:
            if apstra_object != 'digest':

                added = input_diff[apstra_object].get('added', '-')
                changed = input_diff[apstra_object].get('changed', '-')
                removed = input_diff[apstra_object].get('removed', '-')

                added_count, added_yaml = process_diff_element(added)
                changed_count, changed_yaml = process_diff_element(changed)
                removed_count, removed_yaml = process_diff_element(removed)

                table_count.add_row(apstra_object, added_count, changed_count, removed_count)
                table.add_row(apstra_object, added_yaml, changed_yaml, removed_yaml)

        return table_count, table
    except Exception as e:
        logger.error(f"❌ Error printing blueprint changes information: {e}")

def process_diff_element(diff_element):
    '''
    Process a diff element to determine its count and YAML representation.

    Args:
        diff_element (dict or other): The element to process, typically a dictionary or a list.

    Returns:
        tuple: A tuple containing the count as a string and the YAML representation of the element.
                If the element is not a dictionary or a list or is empty, returns "-" for both count and YAML.
    '''
    if isinstance(diff_element, dict) or isinstance(diff_element, list):
        element_count = len(diff_element)
        if element_count == 0:
            element_count = "-"
            element_yaml = "-"
        else:
            element_yaml = yaml.dump(diff_element, default_flow_style=False, sort_keys=False)
    else:
        element_count = "-"
        element_yaml = "-"
    return str(element_count), element_yaml

def print_panel_bp_diff(bp_name, table_bp_diff_status, table_summary_changes, table_changes_count, table_changes):
    '''
    Display the execution plan in a formatted panel

    Args:
        table_scope (Table): The table containing scope information.
        table_terraform_command (Table): The table containing the Terraform command.

    Returns:
        None
    '''
    try:
        # Attempt to create the panel and display it
        panel = Panel.fit(
            Columns([
                table_changes,
                " "*15,
                table_bp_diff_status,
                " "*15,
                table_summary_changes,
                " "*15,
                table_changes_count,
            ]),
            title=f"[bold]CHANGE OVERVIEW IN BLUEPRINT {bp_name}",
            border_style="red",
            title_align="left",
        )
        rprint(panel)

    except Exception as e:
        # Handle any error that occurs while creating or printing the panel
        logger.error(f"❌ An error occurred while displaying the blueprint change overview for {bp_name}: {e}")

def print_panel_non_bp_diff(menu, table_changes_count, table_changes):
    '''
    Display the execution plan in a formatted panel

    Args:
        table_scope (Table): The table containing scope information.
        table_terraform_command (Table): The table containing the Terraform command.

    Returns:
        None
    '''
    try:
        # Attempt to create the panel and display it
        panel = Panel.fit(
            Columns([
                table_changes,
                " "*15,
                table_changes_count,
            ]),
            title=f"[bold]CHANGE OVERVIEW IN {menu.upper()}",
            border_style="red",
            title_align="left",
        )
        rprint(panel)

    except Exception as e:
        # Handle any error that occurs while creating or printing the panel
        logger.error(f"❌ An error occurred while displaying the change overview for {menu}: {e}")

def get_deploy_status(bp_name):
    '''
    Get deploy status of the blueprint from the AOS API using a given blueprint name.

    Args:
        bp_name (str): Blueprint name.

    Returns:
        dic: deploy_status.
    '''
    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/deploy'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        logger.error(f'❌ Error: Failed to retrieve blueprint deploy status - {e}')
        return {}
    
def revert_bp(bp_name):
    '''
    Revert the current staging version to the latest backup version from the AOS API for a given blueprint.

    Args:
        bp_name (str): The name of the blueprint to revert.

    Returns:
        int: HTTP status code from the final API response.
    '''

    logger.info(f"⏪ Reverting uncommitted changes for blueprint: '{bp_name}'")

    try:
        bp_id = get_bp_id(bp_name)
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/revert'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        max_retries = 3
        retry_delay = 5  # seconds
        max_poll_attempts = 10  # Number of times to poll for process completion
        poll_delay = 3  # seconds between poll attempts

        # Retry mechanism for initial request
        for attempt in range(1, max_retries + 1):
            response = requests.post(url, headers=headers, verify=False)

            if response.status_code == 202:
                logger.info("⏳ Initial revert request accepted. Polling for completion...")

                # Poll until the process completes
                for poll_attempt in range(1, max_poll_attempts + 1):
                    poll_response = requests.post(url, headers=headers, verify=False)

                    if poll_response.status_code == 202:
                        logger.info(f"🟢 Polling attempt {poll_attempt}/{max_poll_attempts}: Revert process completed successfully!")
                        return 202  # Return success code
                    elif poll_response.status_code == 409:
                        logger.info(f"⏳ Polling attempt {poll_attempt}/{max_poll_attempts}: Process ongoing, retrying in {poll_delay} seconds...")
                        time.sleep(poll_delay)
                    else:
                        logger.error(f"❌ Unexpected status code: {poll_response.status_code}")
                        return poll_response.status_code  # Return the unexpected status code

                logger.error("❌ Revert process did not complete within the polling limit.")
                return 408  # Request Timeout (custom return for polling exhaustion)

            elif response.status_code == 409:
                logger.info(f"⏳ Attempt {attempt}/{max_retries}: Process ongoing, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            elif poll_response.status_code == 422:
                logger.info(f"⏳ Attempt {attempt}/{max_retries}: No backup available.")
                return 422  # Return success code
            else:
                logger.error(f"❌ Failed to initiate revert: HTTP {response.status_code}")
                return response.status_code  # Return the error status code

        logger.error("❌ Max retries reached. Could not revert blueprint due to persistent conflicts.")
        return 409  # Conflict, max retries reached

    except Exception as e:
        logger.error(f'❌ Error: Failed to revert blueprint - {e}')
        return 500  # Internal Server Error (custom return for exceptions)

def delete_bp(bp_name):
    '''
    Delete a blueprint by its ID.

    Args:
        bp_name (str): Blueprint name.

    Returns:
        bool: True if the delete operation was successful, False otherwise.
    '''

    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        max_retries = 3
        retry_delay = 5  # seconds
        max_poll_attempts = 10  # Number of times to poll for process completion
        poll_delay = 3  # seconds between poll attempts

        # Retry mechanism for initial request
        for attempt in range(1, max_retries + 1):
            response = requests.delete(url, headers=headers, verify=False)

            if response.status_code == 202:
                # # Revert successful
                # return True

                logger.info("⏳ Initial delete request accepted. Polling for completion...")
                # Poll until the process completes
                for poll_attempt in range(1, max_poll_attempts + 1):
                    poll_response = requests.delete(url, headers=headers, verify=False)

                    if poll_response.status_code == 404:
                        logger.info(f"🟢 Polling attempt {poll_attempt}/{max_poll_attempts}: Removal process completed successfully!")
                        return True
                    elif poll_response.status_code == 409 or poll_response.status_code == 405:
                        logger.info(f"⏳ Polling attempt {poll_attempt}/{max_poll_attempts}: Process ongoing, retrying in {poll_delay} seconds...")
                        time.sleep(poll_delay)
                    else:
                        # Process finished successfully or unexpected status
                        poll_response.raise_for_status()

                # If polling exhausts without success
                raise Exception("❌ Removal process did not complete within the polling limit.")

            elif response.status_code == 409 or response.status_code == 405:
                logger.info(f"⏳ Attempt {attempt}/{max_retries}: Process ongoing, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                # Raise an exception for other unexpected HTTP errors
                response.raise_for_status()

        # If all retries fail, raise an exception
        raise Exception("❌ Max retries reached. Could not delete blueprint due to persistent conflicts.")

    except Exception as e:
        logger.error(f'❌ Error: Failed to delete blueprint - {e}')

def delete_bps(bp_list):
    '''
    Deletes specified blueprints from Apstra via API.

    Args:
        bp_list (list): A list of blueprint names to delete.

    '''
    try:

        if isinstance(bp_list, list):

            for bp_name in bp_list:
                logger.info(f"🗑️  Initiating blueprint '{bp_name}' deletion via Apstra API...")
                if delete_bp(bp_name):
                    logger.info(f"✅ Successfully removed blueprint '{bp_name}' from Apstra.")
                else:
                    logger.error(f"❌ Failed to remove blueprint '{bp_name}' from Apstra.")

    except Exception as e:
        logger.error(f"❌ An error occurred while deleting blueprints from Apstra: {e}")

def run_commit_check(bp_name, device_id, hostname):
    '''
    Initiate a commit check operation against a particular device in a given blueprint for which configuration can be rendered.
    This function retries every 10 seconds for up to 1 minute until a 202 status code is received.

    Args:
        bp_name (str): Blueprint name.
        device_id (str): Chassis serial number.
        hostname (str): Device hostname.

    Returns:
        bool: True if the commit check is successful (status 202), False otherwise.
    '''
    try:
        max_poll_attempts = 10  # Maximum polling attempts
        poll_delay = 3  # Seconds between poll attempts

        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/systems/{device_id}/commit-check'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        logger.info(f"🆚 Executing a commit check for '{hostname}' (blueprint '{bp_name}')...")

        # Polling loop for commit check execution completion
        for poll_attempt in range(1, max_poll_attempts + 1):
            response = requests.post(url, headers=headers, verify=False)

            if response.status_code == 202:
                logger.info(f"🟢 Polling attempt {poll_attempt}/{max_poll_attempts}: Commit check execution for '{hostname}' (blueprint '{bp_name}') completed successfully!")
                return True
            if response.status_code == 409:
                logger.info(f"⏳ Polling attempt {poll_attempt}/{max_poll_attempts}: Commit check execution for '{hostname}' (blueprint '{bp_name}') still in progress. Retrying in {poll_delay} seconds...")
                time.sleep(poll_delay)
            else:
                logger.warning(f"❌ Unexpected status code '{response.status_code}' in commit check execution response for '{hostname}' (blueprint '{bp_name}').")
                return False

        # If polling exhausts without success
        logger.error(f"❌ Commit check execution for '{hostname}' (blueprint '{bp_name}') did not complete within the polling limit.")
        return False  # Timed out or unexpected response

    except Exception as e:
        logger.error(f"❌ Error executing commit check for '{hostname}' (blueprint '{bp_name}'): {e}")
        return False

def get_commit_check_result(bp_name, device_id, hostname):
    '''
    Retrieve the result of a commit check operation for a specific device within a given blueprint.

    This function assumes that a commit-check operation has already been initiated for the device.
    It queries the AOS API to fetch details about the commit check, including its status and any
    configuration differences.

    Args:
        bp_name (str): Blueprint name.
        device_id (str): Serial number of the chassis for the specific device.
        hostname (str): Device hostname.

    Returns:
        dict: A dictionary containing the commit check results from Apstra API.
              If retrieval fails or times out, an empty dictionary is returned.

    Raises:
        SystemExit: Logs an error and exits if the API call fails or an exception occurs.
    '''
    try:
        max_poll_attempts = 10  # Maximum polling attempts
        poll_delay = 3  # Seconds between poll attempts

        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)
        url = f'https://{aos_ip}/api/blueprints/{bp_id}/systems/{device_id}/commit-check-result'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        logger.info(f"📥 Retrieving commit check results for '{hostname}' (blueprint '{bp_name}')...")

        # Polling loop for commit check retrieval completion
        for poll_attempt in range(1, max_poll_attempts + 1):
            response = requests.get(url, headers=headers, verify=False)

            if response.status_code != 200:
                logger.error(f"❌ Polling attempt {poll_attempt}/{max_poll_attempts}: API request failed with status code {response.status_code}")
                response.raise_for_status()

            data = response.json()
            state = data.get('state')

            if state == 'success':
                logger.info(f"🟢 Polling attempt {poll_attempt}/{max_poll_attempts}: Commit check retrieval for '{hostname}' (blueprint '{bp_name}') completed successfully!")
                return data  # Return full API response
            elif state == 'pending':
                logger.info(f"⏳ Polling attempt {poll_attempt}/{max_poll_attempts}: Commit check retrieval for '{hostname}' (blueprint '{bp_name}') still in progress. Retrying in {poll_delay} seconds...")
                time.sleep(poll_delay)
            else:
                logger.warning(f"❌ Unexpected state '{state}' in commit check response retrieval for '{hostname}' (blueprint '{bp_name}').")
                return data  # Return full API response
                # return {}

        # If polling exhausts without success
        logger.error(f"❌ Commit check retrieval for '{hostname}' (blueprint '{bp_name}') did not complete within the polling limit.")
        return {}

    except Exception as e:
        logger.error(f"❌ Error retrieving commit check result for '{hostname}' (blueprint '{bp_name}'): {e}")
        return {}

def get_placeholder_racks():
    '''
    Retrieves unique placeholder rack names from all blueprints in the Scope Manager.

    Returns:
        dict: A dictionary where blueprint names are keys and lists of placeholder rack names are values.
    '''
    placeholder_racks = {}

    sm = Scope_Manager()
    bp_list = sm.blueprints  # Get the list of blueprints

    if isinstance(bp_list, list):
        try:
            for bp_name in bp_list:
                # Load blueprint data from its corresponding YAML file
                bp_data = yamldecode(os.path.join(sm.blueprints_path, f"{bp_name}.yml"))

                # Ensure bp_data is valid before accessing it
                if bp_data and isinstance(bp_data, dict):
                    bp_placeholder_racks = []
                    # Extract placeholder rack names if present
                    placeholder_rack_list = bp_data.get("placeholder_racks", [])

                    if isinstance(placeholder_rack_list, list):
                        placeholder_racks[bp_name] = list(set(placeholder_rack_list))

        except Exception as e:
            logging.error(f"❌ Error retrieving placeholder racks: {e}")

    return placeholder_racks

def generate_execution_history(all_customers=False, customer=None, domain=None, project=None):
    '''
    Collects execution history data from the directory structure and stores it in a structured list.

    Args:
        all_customers (bool): If True, processes all customers. Overrides customer-specific parameters.
        customer (str, optional): Specific customer name to process.
        domain (str, optional): Specific domain name to process (requires customer).
        project (str, optional): Specific project name to process (requires customer and domain).

    Returns:
        list: A sorted list of execution history dictionaries.
    '''

    execution_history = []
    customers_path = os.path.join(data_path, 'customers')

    if not os.path.exists(customers_path):
        logger.error(f"❌ Customers directory '{customers_path}' not found.")
        return []

    # Determine which customers to process
    customers = os.listdir(customers_path) if all_customers else [customer] if customer else []

    for cust in customers:
        customer_path = os.path.join(customers_path, cust)
        if not os.path.isdir(customer_path):
            continue

        if domain:
            domains = [domain]
        else:
            domains_path = os.path.join(customer_path, 'domains')
            if not os.path.exists(domains_path):
                continue
            domains = os.listdir(domains_path)

        for dom in domains:
            domain_path = os.path.join(customer_path, 'domains', dom)
            if not os.path.isdir(domain_path):
                continue

            if project:
                projects = [project]
            else:
                projects_path = os.path.join(domain_path, 'projects')
                if not os.path.exists(projects_path):
                    continue
                projects = os.listdir(projects_path)

            for proj in projects:
                project_path = os.path.join(domain_path, 'projects', proj)
                if not os.path.isdir(project_path):
                    continue

                executions_path = os.path.join(project_path, 'output', 'executions')
                if not os.path.exists(executions_path):
                    continue

                for execution in os.listdir(executions_path):
                    execution_path = os.path.join(executions_path, execution)
                    if not os.path.isdir(execution_path):
                        continue

                    execution_data_file = os.path.join(execution_path, execution_data_filename)
                    if not os.path.exists(execution_data_file):
                        continue

                    try:
                        with open(execution_data_file, 'r') as f:
                            execution_data = yaml.safe_load(f) or {}

                        # Ensure 'execution_id' exists for sorting; otherwise, skip
                        if 'execution_id' not in execution_data:
                            # logger.warning(f"❌ Skipping file '{execution_data_file}' due to missing 'execution_id'.")
                            continue

                        execution_history.append(execution_data)

                    except Exception as e:
                        logger.error(f"❌ Error reading execution data file '{execution_data_file}': {e}")

    # Sort the list by execution_id in descending order (latest execution first)
    execution_history.sort(key=lambda x: x.get("execution_id", ""), reverse=True)

    return execution_history

def write_execution_history(execution_data, all_customers=False, customer=None, domain=None, project=None):
    '''
    Writes the collected execution history data to both YAML and CSV files.

    Args:
        execution_data (list): The collected execution history data as a list of dictionaries.
        all_customers (bool): If True, stores the data at a global level, otherwise at customer/domain/project level.
        customer (str, optional): Specific customer name to store the files in their directory.
        domain (str, optional): Specific domain name to store the files within a customer's domain directory.
        project (str, optional): Specific project name to store the files in that project’s directory.
    '''

    try:
        # Determine the output directory
        if all_customers:
            execution_history_path = os.path.join(data_path, 'execution_history')
        elif customer and domain and project:
            execution_history_path = os.path.join(data_path, 'customers', customer, 'domains', domain, 'projects', project, 'execution_history')
        elif customer and domain:
            execution_history_path = os.path.join(data_path, 'customers', customer, 'domains', domain, 'execution_history')
        elif customer:
            execution_history_path = os.path.join(data_path, 'customers', customer, 'execution_history')
        else:
            logger.error("❌ Invalid parameters: Specify 'all_customers=True' or at least 'customer'.")
            return

        old_execution_history_path = os.path.join(execution_history_path, '_OLD')
        os.makedirs(execution_history_path, exist_ok=True)
        os.makedirs(old_execution_history_path, exist_ok=True)

        # Move existing files to _OLD
        for filename in os.listdir(execution_history_path):
            file_path = os.path.join(execution_history_path, filename)
            if os.path.isfile(file_path):
                shutil.move(file_path, os.path.join(old_execution_history_path, filename))
            elif os.path.isdir(file_path) and filename != '_OLD':
                shutil.move(file_path, os.path.join(old_execution_history_path, filename))

        # Generate timestamped filenames
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        yaml_filename = f'{now}_execution_history.yml'
        csv_filename = f'{now}_execution_history.csv'
        yaml_filepath = os.path.join(execution_history_path, yaml_filename)
        csv_filepath = os.path.join(execution_history_path, csv_filename)

        # Write execution data to YAML
        with open(yaml_filepath, 'w') as yamlfile:
            yaml.safe_dump(execution_data, yamlfile, default_flow_style=False, sort_keys=False)

        logger.info(f"📝 YAML file successfully created at '{yaml_filepath}'")

        # Collect all unique keys from execution data to define CSV columns
        all_keys = set()
        for record in execution_data:
            all_keys.update(record.keys())

        # Sort keys for consistency
        all_keys = sorted(all_keys)

        # Write execution data to CSV
        with open(csv_filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(all_keys)  # Write header row

            for record in execution_data:
                row = [record.get(key, '-') for key in all_keys]  # Fill missing fields with '-'
                writer.writerow(row)

        logger.info(f"📝 CSV file successfully created at '{csv_filepath}'")

    except Exception as e:
        logger.error(f"❌ Error writing execution history: {e}")

def generate_and_write_execution_history(all_customers=False, customer=None, domain=None, project=None):
    '''
    Wrapper function that generates execution history and writes it to a CSV file.

    Args:
        all_customers (bool, optional): If True, processes all customers. Overrides specific customer filtering.
        customer (str, optional): Specific customer to process.
        domain (str, optional): Specific domain within a customer.
        project (str, optional): Specific project within a domain.
    '''
    try:
        execution_data = generate_execution_history(
            all_customers=all_customers, customer=customer, domain=domain, project=project
        )

        if not execution_data:
            logger.warning("❌ No execution data found. Skipping file writing.")
            return

        write_execution_history(
            execution_data, all_customers=all_customers, customer=customer, domain=domain, project=project
        )

    except Exception as e:
        logger.error(f"❌ Error in generate_and_write_execution_history: {e}")

def monitor_config_push_status(blueprints):
    '''
    Waits for the completion of the on-commit process, ensuring that all configuration changes have been pushed to the devices.
    It polls the deployment status until the process completes or the polling limit is reached.

    Args:
        blueprints (list): A list of blueprint names in the project scope.

    Returns:
        bool: Returns True if all deployments complete within the polling limit, False otherwise.
    '''
    try:
        max_poll_attempts = 10  # Maximum number of polling attempts
        poll_delay = 3  # Delay in seconds between each poll attempt
        all_successful = True  # Flag to track if all deployments are successful

        if isinstance(blueprints, list):
            for bp_name in blueprints:
                logger.info(f"👀 Starting deployment status check for blueprint '{bp_name}'...")

                # Polling for process completion
                success = False  # Flag for current blueprint status
                for poll_attempt in range(1, max_poll_attempts + 1):
                    # Update blueprint data
                    raw_blueprint_data = get_blueprint_data(blueprints, silent_mode=True)
                    bp_data = next((bp for bp in raw_blueprint_data if bp.get('label', None) == bp_name), None)

                    # Check if all deployment modes have no pending tasks
                    if bp_data:
                        if bp_data.get('deployment_status', None) and all(data.get('num_pending', 0) == 0 for data in bp_data['deployment_status'].values()):
                            logger.info(f"🟢 Polling attempt {poll_attempt}/{max_poll_attempts}: Configuration push to devices for blueprint '{bp_name}' completed successfully!\n")
                            success = True  # Mark success for this blueprint
                            break  # Exit polling loop if success
                        else:
                            logger.info(f"⏳ Polling attempt {poll_attempt}/{max_poll_attempts}: Configuration push to devices for blueprint '{bp_name}' still in progress. Retrying in {poll_delay} seconds...")
                            time.sleep(poll_delay)
                    else:
                        logger.info(f"🚫 Skipping status check for blueprint '{bp_name}' (removed or unavailable).\n")
                        success = True  # Mark success for this blueprint
                        break
                    
                # If polling exhausts without success, flag all_successful as False
                if not success:
                    logger.error(f"❌ Configuration push to devices for blueprint '{bp_name}' did not complete within the polling limit.\n")
                    all_successful = False

            return all_successful  # Return True if all blueprints succeeded, False otherwise

    except TypeError as e:
        logger.error(f"❌ Input Error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ An error occurred while monitoring deployment status: {e}")
        return False
    
def get_bp_build_errors(bp_name):
    '''
    Retrieve build errors for a given blueprint.

    Args:
        bp_name (str): Name of the blueprint.

    Returns:
        dict: A dictionary of build errors if any exist, otherwise an empty dictionary.
    '''

    try:
        sm = Scope_Manager()
        aos_ip = sm.get('aos_ip')
        aos_token = sm.get('aos_token')
        bp_id = get_bp_id(bp_name)

        url = f'https://{aos_ip}/api/blueprints/{bp_id}/errors'
        headers = {'AuthToken': aos_token, 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        else:
            return {}

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while retrieving build errors in blueprint '{bp_name}': {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while retrieving build errors in blueprint '{bp_name}': {e}")

    return []  # Ensure a consistent return type even in case of errors

def get_build_errors(bps_w_errors):
    '''
    Retrieve a list of blueprints with build errors.

    Args:
        bps_w_errors (list of dicts): A list of dictionaries containing blueprint names and their build error counts.

    Returns:
        build_errors (list of dicts): Each dictionary contains the blueprint name and the build errors if errors exist.
    '''
    try:
        if not isinstance(bps_w_errors, list):
            logger.warning("❌ Expected a list of blueprints but received a different type. Skipping error retrieval.")
            return []

        build_errors = []

        for bp in bps_w_errors:

            bp_name = bp.get('blueprint')
            build_errors_count = bp.get('build_errors_count')

            logger.info(f"📡 Fetching {build_errors_count} build errors for blueprint '{bp_name}'...\n")

            bp_build_errors = get_bp_build_errors(bp_name)

            if bp_build_errors:
                build_errors.append({
                    'blueprint': bp_name,
                    'build_errors_count': build_errors_count,
                    'build_errors': bp_build_errors
                })

        return build_errors

    except Exception as e:
        logger.error(f"❌ An error occurred while retrieving blueprint build errors: {e}")
        return []  # Ensuring a valid return type even if an error occurs

def print_build_errors(bps_w_errors):
    '''
    Fetch and print build errors for a list of blueprints.

    Args:
        bps_w_errors (list of dicts): A list of dictionaries containing blueprint names and their build error counts.

    '''

    try:

        build_errors = get_build_errors(bps_w_errors)

        if build_errors:
            # pprint(build_errors)

            for bp in build_errors:
                bp_name = bp.get('blueprint')
                # build_errors_count = bp.get('build_errors_count')
                build_errors = bp.get('build_errors')

                # Display selected configuration differences
                title="[bold]DESCRIPTION OF BUILD ERRORS IN BLUEPRINT"
                table = Table(
                    Column(header="Build Error Type", justify="center", style="cyan"),
                    Column(header="Error ID", justify="center", style="cyan"),
                    Column(header="Severity", justify="left", style="cyan"),
                    Column(header="Category", justify="center", style="cyan"),
                    Column(header="Entity Type", justify="center", style="cyan"),
                    Column(header="Error Type", justify="center", style="cyan"),
                    Column(header="Message", justify="left", style="magenta"),
                    Column(header="Resolutions", justify="left", style="magenta"),
                    title=title,
                    box=box.HEAVY_EDGE,
                )
                table.show_header = True
                table.title_justify = "center"
                table.title_style = "cyan underline"
                table.show_lines=True
                for build_error_type, build_errors_type in build_errors.items():
                    if build_error_type == 'nodes':
                        for build_error_id, build_error_args in build_errors_type.items():
                            table.add_row(
                                build_error_type,
                                build_error_id,
                                build_error_args[0].get('severity','-'),
                                build_error_args[0].get('display_category','-'),
                                build_error_args[0].get('entity_type','-'),
                                build_error_args[0].get('error_type','-'),
                                build_error_args[0].get('message','-'),
                                yaml.dump(build_error_args[0].get('resolutions','-'), default_flow_style=False, sort_keys=False),
                            )
                    # else:
                    #     logger.info(f'Build Error Type {build_error_type} pending to be considered for display.\n')

                panel = Panel.fit(
                    Columns([
                        table,
                    ]),
                    title=f"[bold]BUILD ERRORS OVERVIEW IN BLUEPRINT {bp_name}",
                    border_style="red",
                    title_align="left",
                )

                print("\n")
                rprint(panel)

        else:
            logger.info("✅ No build errors found.")

    except Exception as e:
        logger.error(f"❌ Error in print_build_errors: {e}")
        return 0  # Return 0 in case of an error

def run_apaf_terraform(input_params):

    '''
    Main framework function that orchestrates the different steps
    required to complete the full execution process using Terraform.

    Args:
        input_params (dict): A dictionary containing input parameters
                             for the execution.
    '''

    # -- Retrieve the terraform command from the input parameters
    is_terraform_apply, is_terraform_destroy, terraform_command = get_terraform_command(input_params)

    # -- Instantiate the Scope Manager
    sm = Scope_Manager(terraform_command, input_params)

    # -- Create a directory to store logs for the entire session, which will be relocated to the appropriate project afterward
    os.makedirs(tmp_exec_log_path, exist_ok=True)  # Creates the directory and any missing parent directories if not already present

    # -- Using `with` ensures proper closure fo the log file
    with Tee(tmp_exec_log_file) as tee:

        try:
            # -- Redirect stdout and stderr to both file and console
            sys.stdout = tee
            sys.stderr = sys.stdout

            # -- Above all, manners. Say hello...
            display_welcome_banner()

            # -- Check if the execuions are blocked
            if sm.blocked_executions():
                sm.exit_manager("BLOCKED_EXECUTIONS")

            if sm.post_rollback:
                logger.info("🔄 Launching a fresh execution of the framework post-rollback to realign the Apstra deployment... Hold tight! 🚀\n")
                sm.terraform_command = "terraform apply"
                sm.post_commit_action = "commit"
                sm.post_commit_comment = "Post-rollback execution for alignment purposes"
            else:
                logger.info("🚀 Launching a fresh execution of the framework... Hold tight! 🚀\n")

            if sm.interactive:
                logger.info("👤 Running in interactive mode - user input required at several points across the execution. 🛠️\n")
            else:
                logger.info("🤖 Running in non-interactive mode - no user input required. Sit back and relax! 🛠️\n")

            while True:
                print("\r")
                sm.print_panel_execution_plan()
                rprint('\n:pushpin:')

                options = [
                    '🚀 Proceed with the plan and execute Terraform',
                    '🎯 Change "AOS Target"',
                    '🏢 Change "Customer"',
                    '🌍 Change "Domain"',
                    '📁 Change "Project"',
                    '🔧 Change "Terraform command"',
                    '📜 Generate execution history report',
                    '📥 Fetch Apstra snapshot',
                    '🚪 Exit'
                ]

                # -- In not interactive mode, unconditionally choose to proceed with the plan (option 1)
                if sm.interactive:
                    opt = display_menu (options)
                else:
                    opt = 1 # Simulate the automatic choice to proceed with the plan

                if opt == 1:
                    if 'terraform destroy' in sm.terraform_command:
                        print("\n")
                        if sm.prompt_destroy():
                            break
                    else:
                        break
                elif opt == 2:
                    rprint(f'\n:pushpin: {options[opt - 1]}')
                    sm.update_vars({'aos_target' : multi_option(sorted(sm.aos_targets_list))})
                elif opt == 3:
                    rprint(f'\n:pushpin: {options[opt - 1]}')
                    sm.update_vars({'customer' : multi_option(sorted(customers_list))})
                elif opt == 4:
                    rprint(f'\n:pushpin: {options[opt - 1]}')
                    sm.update_vars({'domain' : multi_option(sorted(sm.domains_list))})
                elif opt == 5:
                    rprint(f'\n:pushpin: {options[opt - 1]}')
                    sm.update_vars({'project' : multi_option(sorted(sm.projects_list))})
                elif opt == 6:
                    rprint(f'\n:pushpin: {options[opt - 1]}')
                    sm.terraform_command = multi_option(sorted(list(terraform_commands.values())))
                    sm.update_vars({})
                elif opt == 7:
                    rprint(f'\n:pushpin: {options[opt - 1]}')
                    exec_hist_opt = multi_option(execution_history_options)
                    sm.generate_customer_history_report(exec_hist_opt)
                elif opt == 8:
                    sm.execution_stage  = '00_apstra_snapshot'
                    sm.save_device_data()
                    sm.save_blueprint_data()
                    sm.save_apstra_snapshot()
                    sm.exit_manager("USER_SILENT_EXIT")
                elif opt == 9:
                    sm.exit_manager("USER_SILENT_EXIT")
                else:
                    logger.error(f'❌ Invalid option ({opt}) not within the valid choices. Try again...')

            # -- Recreate the "wip" directory and copy the "executions" folder in it with all its contents
            replace_directory_contents(
                sm.get('wip_path'),
                sm.get('executions_dir'),
            )

            # -- Ensure the creation and management of "execution" folders in the "wip" staging area
            sm.manage_execution_dirs("initial_stage")

            if is_terraform_apply or is_terraform_destroy:

                # ---------------------------------------------------------------------------- #
                #                              Pre-execution plan                              #
                # ---------------------------------------------------------------------------- #

                # -- Get blueprint data, display warning messages and prompt the user for confirmation to continue
                sm.scan_blueprints(warning = True)

                # -- Check for uncommitted blueprints and prompt the user to revert them before proceeding with execution
                if sm.uncommitted_bps:
                    print("\n")
                    logger.warning(f"🚨 Uncommitted changes detected in the following blueprints of the current project:\n{sm.uncommitted_bps}\n")
                    sm.prompt_revert()

                # -- No uncommitted blueprints - ready to go!
                logger.info("ℹ️  No blueprints in the current project have uncommitted changes.\n")

                # -- Save blueprint data and prompt for saving device data
                sm.execution_stage  = '00_before_starting'
                sm.save_blueprint_data()
                sm.prompt_save_blueprint_data()

                # ---------------------------------------------------------------------------- #
                #                                Execution plan                                #
                # ---------------------------------------------------------------------------- #

                print("\n")
                logger.info(f"🚀 Proceeding with the execution plan...\n")

                # -- Update the Terraform backend configuration path using the most recent tfstate file corresponding to the current project
                backend_config_path = sm.update_terraform_backend_config_path()

                # -- Identify and list the Apstra sections other than blueprints that have changes compared to the last successful execution
                list_non_bp_menus_w_changes_last_exec, non_bp_diff_last_exec = get_non_bp_changes_tgz(sm.get('wip_execution_0_input_tgz_file'), sm.get('wip_execution_0_input_tgz_rollback_file'))
                for menu in list_non_bp_menus_w_changes_last_exec:
                    sm.handle_execution_data_file('update', {f'changes_in_{menu}': 'Yes'})

                # -- Run Terraform (includes the pre-creation of the Plan if necessary)
                sm.run_terraform()

                display = False
                if 'terraform apply' in sm.terraform_command and not sm.post_rollback:
                    display = True
                    print("\n")
                    logger.info("📊 Summary of the staged changes performed on Apstra as a result of applying the Terraform Plan:\n")

                # -- Display changes in Non-blueprint menus compared to the last successful execution
                if display:
                    display_non_bp_changes(list_non_bp_menus_w_changes_last_exec, non_bp_diff_last_exec)

                # -- Check for uncommitted blueprints
                sm.scan_blueprints()
                if sm.uncommitted_bps:
                    list_finally_uncommitted_bps = [item['blueprint'] for item in sm.uncommitted_bps]
                    sm.handle_execution_data_file('update', {f'changes_in_blueprints': list_finally_uncommitted_bps})

                    # -- Display changes in Blueprints
                    if display:
                        sm.print_changes_in_bps(list_finally_uncommitted_bps)

                    # -- Build Errors after the Terraform execution
                    if sm.get('post_commit_action') == 'commit' and build_errors_in_uncommitted_bps(sm.uncommitted_bps_w_errors):
                            if sm.interactive:
                                input("⏭️  Press enter to display the build errors...\n")
                            print_build_errors(sm.uncommitted_bps_w_errors)
                            print("\n")
                            if sm.post_rollback:
                                sm.exit_manager("BLOCKED_EXECUTIONS")
                            elif "terraform destroy" in sm.terraform_command:
                                sm.exit_manager("TF_EXEC_W_ERRORS_DESTROY")
                            else:
                                # -- In interactive mode, prompt the user to press Enter to initiate the rollback process
                                if sm.interactive:
                                    input("⏭️  Press enter to initiate the rollback process...\n")
                                sm.revert_execution(revert_to_last_exec = True)
                                sm.exit_manager("TF_EXEC_W_ERRORS_REVERT")

                # ---------------------------------------------------------------------------- #
                #                              Post-execution plan                             #
                # ---------------------------------------------------------------------------- #

                # -- Execute this section only if:
                #    - Either it is a 'terraform destroy'
                #    - Or it is a 'terraform apply' and there are changes either in the Non-blueprint menus or in the Blueprint menu
                if 'terraform destroy' in sm.terraform_command or ('terraform apply' in sm.terraform_command and (list_non_bp_menus_w_changes_last_exec or sm.uncommitted_bps)):

                    # -- Get commit check status only if there are uncomitted blueprints
                    if sm.uncommitted_bps:
                        sm.commit_check(display)

                    while True:
                        if 'terraform destroy' in sm.terraform_command:
                            table_final_deploy = build_table_deploy(sm.terraform_command, sm.uncommitted_bps, 'commit', sm.get('post_commit_comment'), 'final', list_non_bp_menus_w_changes_last_exec)
                            print('\r')
                            print_panel_deploy_handling_plan(table_final_deploy, "POST-EVENTS")
                            print("\n")
                            logger.info("Since 'terraform destroy' is an IRREVERSIBLE action, 'commit' is the only allowed option at this stage.")
                            rprint('\n:pushpin:')
                            options = [
                                '🚀 Proceed with the plan',
                                '💬 Change "Commit comment"',
                            ]
                        else:
                            table_final_deploy = build_table_deploy(sm.terraform_command, sm.uncommitted_bps, sm.get('post_commit_action'), sm.get('post_commit_comment'), 'final', list_non_bp_menus_w_changes_last_exec)
                            print('\r')
                            print_panel_deploy_handling_plan(table_final_deploy, "POST-EVENTS")
                            rprint('\n:pushpin:')
                            options = [
                                '🚀 Proceed with the plan',
                                '💬 Change "Commit comment"',
                                '🏷️  Change "Action to perform"',
                            ]
                        # -- In not interactive mode, unconditionally choose to proceed with the plan (option 1)
                        if sm.interactive:
                            opt = display_menu (options)
                        else:
                            opt = 1 # Simulate the automatic choice to proceed with the plan

                        if opt == 1:
                            loop_again = False
                            if 'terraform destroy' not in sm.terraform_command and sm.get('post_commit_action') == 'revert':
                                loop_again = sm.prompt_reconfirm_revert()
                            if not loop_again:
                                break
                        elif opt == 2:
                            rprint(f'\n:pencil: Enter the commit comment:')
                            sm.update_vars({'post_commit_comment' : input()}, update_execution_data_file = True)
                        elif opt == 3:
                            rprint(f'\n:pushpin: {options[opt - 1]}')
                            sm.update_vars({'post_commit_action' : multi_option(post_commit_actions)}, update_execution_data_file = True)

                    if sm.uncommitted_bps:
                        # Commit the staged blueprints
                        for bp in sm.uncommitted_bps:
                            sm.deploy_bp(
                                bp['blueprint'],
                                bp['staged_version'],
                                sm.get('post_commit_comment')
                            )

                    # Wait until all configurations have been successfully pushed to the devices (no pending configurations) to grab device info
                    if monitor_config_push_status(sm.get('blueprints',[])):
                        # Get device status
                        sm.execution_stage  = '02_after_committing'
                        sm.save_device_data()
                        sm.save_blueprint_data()

                # Archive the executions if it is a Terraform destroy action
                if 'terraform destroy' in sm.terraform_command:
                    sm.exit_manager("USER_TF_EXEC_DESTROY")
                else:
                    sm.exit_manager("USER_TF_EXEC_COMMIT")


            else: # Terraform action is neither 'apply' nor 'destroy'

                # Update the Terraform backend configuration path using the most recent tfstate file corresponding to the current project
                backend_config_path = sm.update_terraform_backend_config_path()

                # Run Terraform
                sm.run_terraform()

        finally:
            # Once the `with` block ends, `tee.close()` is automatically called
            sys.stdout = sys.stdout.original_stdout # Restore original stdout
            sys.stderr = sys.stdout

# ---------------------------------------------------------------------------- #
#                               Global variables                               #
# ---------------------------------------------------------------------------- #

# Maximum number of permanently saved revisions allowed in the Time Voyager for a given blueprint.
# Limit imposed by Apstra.
max_permanent_revisions = 25

execution_history_options = [
    'all-customers',
    'customer-wide',
    'domain-wide',
    'project-wide',
]

terraform_commands = {
    'v': 'terraform version',
    'i': 'terraform init',
    'pr': 'terraform providers',
    'sh': 'terraform show',
    'st': 'terraform state list',
    'p': 'terraform plan',
    'a': 'terraform apply',
    'aa': 'terraform apply -auto-approve',  # Handle this with care!
    'd': 'terraform destroy',
    'da': 'terraform destroy -auto-approve',  # Handle this with care!
}

terraform_commands_apply = {
    'a': 'terraform apply',
    'aa': 'terraform apply -auto-approve',  # Handle with care!
}

terraform_commands_destroy = {
    'd': 'terraform destroy',
    'da': 'terraform destroy -auto-approve',  # Handle with care!
}

list_successful_exit_codes = [
    "USER_TF_EXEC_COMMIT",
    "USER_TF_EXEC_DESTROY",
]

list_execution_history_relevant_fields = [
    # "aos_target",
    # "customer",
    # "domain",
    "execution_id",
    "rollback_execution_id",
    "exit_code",
    "local_creation_date",
    "local_creation_time",
    "post_commit_action",
    "post_commit_comment",
    "changes_in_design",
    "changes_in_resources",
    "changes_in_blueprints",
    # "pre_commit_action",
    # "pre_commit_comment",
    # "project",
    # "terraform_command",
    # "utc_creation_date",
    # "utc_creation_time",
]
valid_commands = ", ".join([f"'{key}' ({value})" for key, value in terraform_commands.items()])

pre_commit_actions = ['commit', 'exit']

post_commit_actions = ['commit', 'revert']

python_path = "../python"
terraform_path = "../terraform"

tools_path = "../../tools"
python_path = os.path.join(tools_path, "python")

data_path = "../../data"
scope_path = os.path.join(data_path, "scope")
customers_path = os.path.join(data_path, "customers")
customers_list = get_direct_subdirectories(customers_path)

tmp_exec_log_path = os.path.join(customers_path, "__tmp__")
tmp_exec_log_file = os.path.join(tmp_exec_log_path, "full_execution.log")

execution_data_filename = "execution_data.yml"

scope_filename = "scope.yml"
scope_file_path = os.path.join(scope_path, scope_filename)

non_blueprint_menus = ['resources', 'design']

