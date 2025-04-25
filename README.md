# Table of Contents
- [Overview](#overview)
- [Version Compatibility](#version-compatibility)
- [Getting Started](#getting-started)
- [Example Projects](#example-projects)
- [Contributing](#contributing)


# Overview

The **Apstra Provisioning Automation Framework** simplifies the **automated provisioning** of your datacenter infrastructure managed by [Juniper Apstra](https://www.juniper.net/us/en/products/network-automation/apstra.html) by separating code and data into independent blocks allowing the interaction with Apstra by editing **data-only, code-agnostic**, and **human-friendly YAML files**. 

This enables the users to perform both **Day-0 initial deployments and Day-1 business-as-usual operations** on Apstra without needing in-depth knowledge of the underlying code, making the framework accessible to a wider audience. Additionally, decoupling data from code also facilitates the integration with a centralized **Single Source of Truth (SSoT)** hub, ensuring consistency across the entire deployment, extending beyond Apstra and network devices.

The current implementation relies on Apstra's [Terraform](https://www.terraform.io) [provider](https://github.com/Juniper/terraform-provider-apstra) and other Python-based features to simplify and enhance user operations. As the data and code are segregated, the framework’s underlying code can easily be expanded to other automation tools without impacting the data.

In summary, its **data and code separation** approach, combined with a **modular architecture**, improves the **maintainability, scalability, and flexibility** of your datacenter deployment. Meanwhile, its **simple, intuitive, and robust** interface streamlines user operations, ensuring **consistent and seamless** provisioning.

# Version Compatibility

This framework has been developed to be compatible with the following versions of its key components. 

This doesn't mean it will not work with other other releases, but it has been tested to work reliably with these versions:

| Component                  | Version        |
|----------------------------|----------------|
| [**Apstra**](https://supportportal.juniper.net/s/article/Apstra-Supported-Releases-of-Juniper-Apstra?language=en_US)                 | 4.2.1.1, 4.2.2, 5.0.0, 5.1.0      |
| [**Terraform**](https://github.com/hashicorp/terraform/releases)            | 1.9.8          |
| [**Terraform Apstra Provider**](https://github.com/Juniper/terraform-provider-apstra/releases/) | 0.85.1         |


# Getting Started

- [Step-by-Step Process](step-by-step-process)
- [Process Summary](#process-summary)
  
## Step-by-Step Process

Following steps will allow you to fully install and test the framework.

- [🌐 Step 0 - Apstra Reachability](-step-0-apstra-reachability)
- [📂 Step 1 - Clone the Repository](-step-1-clone-the-repository)
- [⚙️ Step 2 - Install Dependencies](-step-2-install-dependencies)
- [🔧 Step 3 - Initialize Terraform](-step-3-initialize-terraform)
- [📝 Step 4 - Edit Your Input Data Files](-step-4-edit-your-input-data-files)

### 🌐 Step 0 - Apstra Reachability
### Step 0 - Apstra Reachability

As obvious as it may seem, the first requirement is that the Juniper Apstra web interface (REST API) is **reachable** from the machine where you plan to install this framework.
 
For testing purposes, you don’t need a real physical data center infrastructure underneath, since Apstra allows you to create all provisioning objects "logically" without the need to assign them to actual devices.

> If you wish to assign actual devices to your blueprints, **ensure they are acknowledged** in the Apstra GUI by placing them in the "Out of Service Ready" state. This will indicate your intent for Apstra to manage the devices. Follow the steps outlined [here](https://www.juniper.net/documentation/us/en/software/apstra5.0/apstra-user-guide/topics/task/device-acknowledge.html) to complete this process.

### 📂 Step 1 - Clone the Repository

**Clone this repository**, which contains all the necessary files to run the framework, into a suitable location on your system.

### ⚙️ Step 2 - Install Dependencies

The server where you install the framework can be **any machine**: a physical server, a laptop, a VM, an OpenShift pod, or even a Docker container. Regardless of where it's running, it must have the **necessary tools installed**:
 
1 - **Terraform Installation**: You need Terraform installed on your system. You can find installation instructions for popular operating systems [here](https://developer.hashicorp.com/terraform/tutorials/docker-get-started/install-cli).
 
> Please make sure to install a Terraform version specified in the [Version Compatibility section](#version-compatibility).

2 - **Python Installation**: You also need Python 3 installed, along with the required dependencies listed below. The framework has been successfully tested with **Python 3.12.9** and the following package versions:

| Python3 Package    | Tested Version |
|--------------------|----------------|
| apstra-api-python  | 0.2.1 |
| certifi            | 2025.1.31 |
| charset-normalizer | 3.4.1 |
| deepdiff           | 8.2.0 |
| idna               | 3.10 |
| Jinja2             | 3.1.5 |
| markdown-it-py     | 3.0.0 |
| MarkupSafe         | 3.0.2 |
| mdurl              | 0.1.2 |
| orderly-set        | 5.3.0 |
| Pygments           | 2.19.1 |
| PyYAML             | 6.0.2 |
| requests           | 2.32.3 |
| rich               | 13.9.4 |
| urllib3            | 2.3.0 |

💡 If you decide to run the Framework within **a dedicated 🐳 Docker container 🐳** — isolating it from the characteristics of your host machine — [this guide](./setup/docker_setup/DOCKER_SETUP.md) will help streamline the process.
A set of prepared files and scripts are available to simplify the setup, automating the required steps and ensuring a reliable environment with minimal manual effort.

### 🔧 Step 3 - Initialize Terraform

**Initialize the Terraform backend**, which will automatically install the Apstra Terraform Provider too. The Apstra Terraform provider version to be installed is specified in the [``provider.tf``](./tools/terraform/provider.tf) file.

To initialize Terraform, execute the command ``terraform init`` from the [``/tools/terraform``](./tools/terraform) directory in your cloned repo:

```
$ pwd
/tools/terraform
$ terraform init
Initializing the backend...

Successfully configured the backend "local"! Terraform will automatically
use this backend unless the backend configuration changes.
Initializing modules...
- blueprints in modules/blueprints
- blueprints.design in modules/design
- blueprints.resources in modules/resources
Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform
- Finding juniper/apstra versions matching "0.85.1"...
- Installing juniper/apstra v0.85.1...
...

Terraform has been successfully initialized!
```

To complete this step successfully, an Internet connection is required to download the necessary provider plugins and modules for the specified version from the [Terraform Registry](https://registry.terraform.io/providers/Juniper/apstra/latest/docs). However, in scenarios where you need to run Terraform in an offline or restricted environment, you can pre-download the required dependencies and configure a local repository. For detailed instructions on how to set this up, refer to the guide [here](https://support.hashicorp.com/hc/en-us/articles/23562100651923-How-to-use-Terraform-CLI-with-Local-Mirror-for-Provider-Plugins-for-system-without-internet-access).

### 📝 Step 4 - Edit Your Input Data Files

Once all the environment is ready, you can proceed to **edit the YAML data files** that define the Apstra objects for your particular data center infrastructure.

Refer to this repository’s documentation (Wiki section) for details on the different data files, objects, and variables.

For demo pourposes, [two sample domains](#example-projects) have been created under the [``/data/customers/DEMO``](./data/customers/DEMO) customer directory. To quickly test the first one [``SINGLE_PROJECT``](./data/customers/DEMO/domains/SINGLE_PROJECT) domain on your Apstra infrastructure, edit the [``credentials.yml``](./data/customers/DEMO/domains/SINGLE_PROJECT/private/credentials.yml) file with your Apstra server details and login credentials. 

For now, you can leave the other data files in [that directory](./data/customers/DEMO/domains/SINGLE_PROJECT) unchanged, since the predefined objects (under design, resources and blueprints [``input``](./data/customers/DEMO/domains/SINGLE_PROJECT/projects/ALL_IN_ONE/input/) subdirectories) describe a couple of sample data centers and will be deployed automatically.

Once you've tested the [``SINGLE_PROJECT``](./data/customers/DEMO/domains/SINGLE_PROJECT) domain, you can follow a similar process with the [``MULTI_PROJECT``](./data/customers/DEMO/domains/MULTI_PROJECT) domain and explore the results in the Apstra GUI.

### 🚀 Step 5 - Run the Framework

To **run the framework** on your machine, navigate to the [``/tools/python``](./tools/python) directory and execute the command ``python3 main.py command=a`` in your terminal:

```
$ pwd
/tools/python
$ python3 main.py command=a
                                                                👋😊


                                                   W E L C O M E   T O   T H E
                              A P S T R A    P R O V I S I O N I N G    A U T O M A T I O N    F R A M E W O R K


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

2025-04-02 - 15:52:27 INFO     🚀 Launching a fresh execution of the framework... Hold tight! 🚀                                                                                                                                                                   utils.py:6927

                      INFO     👤 Running in interactive mode - user input required at several points across the execution. 🛠️                                                                                                                                      utils.py:6930


╭─ EXECUTION PLAN ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                      SCOPE                                        TERRAFORM COMMAND                                                                                                                                                                                          │
│ ┏━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓                 ┏━━━━━━━━━━━━━━━━━━━┓                                                                                                                                                                                        │
│ ┃ AOS Target │        apstra_server_lab       ┃                 ┃  terraform apply  ┃                                                                                                                                                                                        │
│ ┃   Customer │              DEMO              ┃                 ┗━━━━━━━━━━━━━━━━━━━┛                                                                                                                                                                                        │
│ ┃     Domain │         SINGLE_PROJECT         ┃                                                                                                                                                                                                                              │
│ ┃    Project │           ALL_IN_ONE           ┃                                                                                                                                                                                                                              │
│ ┗━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛                                                                                                                                                                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

📌
1. 🚀 Proceed with the plan and execute Terraform
2. 🎯 Change "AOS Target"
3. 🏢 Change "Customer"
4. 🌍 Change "Domain"
5. 📁 Change "Project"
6. 🔧 Change "Terraform command"
7. 📜 Generate execution history report
8. 📥 Fetch Apstra snapshot
9. 🚪 Exit


🔢 Enter the option number:

```

At this point, you can either accept the current settings and proceed with execution or modify any configuration by selecting an option from 2 to 6.

Each time a change is made, the EXECUTION PLAN is updated and displayed again, reflecting the newly selected options. This iterative approach allows users to fine-tune their configuration before proceeding with the plan by selecting option 1.

For a comprehensive guide on all available options and interactive menus throughout the entire lifecycle of a framework execution, please refer to the Wiki section of this repository.

## Process Summary

While **Steps 0, 1, 2, and 3** are typically required **only once per machine** to set up the entire ecosystem and get the framework functional (or when something breaks and needs to be restarted), it's important to note that, after that, the usual workflow for running the Framework is a continuous cycle of just **Steps 4 and 5**: 📝 edit input data files (Step 4) → 🚀 run the Framework (Step 5) → 📝 edit the input data files (Step 4) → 🚀 run the Framework (Step 5)… and so on.

Nothing really complex — just a smooth and repetitive flow 🔄.

# Example Projects

If you want to experience the framework firsthand, this repository includes two demo setups for testing purposes, located in the [``/data/customers/DEMO``](./data/customers/DEMO) directory.

You can explore the details of each example and follow the lab guide in the [``DEMO_EXAMPLES``](DEMO_EXAMPLES.md) document to see how the framework efficiently handles both Day-0 and Day-1 tasks, covering the full lifecycle of an Apstra-based datacenter.

# Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**. 🙏

If you spot something wrong, please open a GitHub issue and, if you’d like to contribute, feel free to submit a pull request with your changes. For detailed instructions on how to contribute, please refer to the [``CONTRIBUTE``](CONTRIBUTE.md) document.  

Last but not least, we hope that you enjoy using this framework, and if you do, please consider giving the project a star on GitHub ⭐ to show your support.

Thanks again!
