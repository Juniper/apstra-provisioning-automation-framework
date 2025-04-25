This guide walks you through spinning up a **ready-to-use Docker container** in seconds — complete with all required libraries and dependencies — for running the **Apstra Provisioning Automation Framework** in a clean, isolated environment.

# Table of Contents
- [Why Use a Docker Container](#why-use-a-docker-container)
- [Setting Up the Framework in a Docker Container](#setting-up-the-framework-in-a-docker-container)

# Why Use a Docker Container?  

Running the Framework inside a **Docker container** offers several advantages:

- ✅ **Cross-platform compatibility** – Run it on any OS without installing or configuring dependencies on your host.
- 🔐 **Environment isolation** – Prevent conflicts with other tools or libraries.
- 🧼 **Clean and reproducible setup** – Always start from a fresh and controlled state while using full system resources. 

We've made deployment simple using a **Python Docker container (available [here](https://hub.docker.com/_/python)) running on top of a lightweight Alpine Linux distribution**  and a set of setup scripts. Just follow the steps below for a smooth installation!

# Setting Up the Framework in a Docker Container

## 🐳 Step 1 - Install Docker

First, verify whether **Docker** is installed on your machine. On Unix-based systems, you can check this by running the following command:  

```bash
docker --version
```

If Docker is not installed, proceed to install the **Docker Engine** by following the installation steps for your specific operating system as outlined [here](https://www.docker.com/products/docker-desktop/).

> ☝️ **Note**: Some versions of Docker may not include **Docker Compose** by default. Be sure to install it separately if needed.

## 🌍 Step 2 - Customize the Docker Compose file

Edit the [`docker_compose_apaf.yaml`](docker_compose_apaf.yaml) file to set your timezone in the `TZ` variable.

Example for setting it to `Europe/Madrid`:

```yaml
services:
  apaf:
    [...]
    environment:
        TZ: "Europe/Madrid" # 📝 Set to the correct timezone for your environment (adjust as needed)
    [...]
```

## 🚀 Step 3 - Run the Container

A [`dockerfile`](dockerfile), a [`docker_compose_apaf.yaml`](docker_compose_apaf.yaml), and a set of helper scripts have been prepared to simplify the process of getting the Docker Container up and running with minimal effort.

These assets automatically handle the entire setup process behind the scenes, performing the following actions:

- 🐧 Deploy a **Python Alpine-based Docker** container.
- 🔁 **Mount volumes** for code access and persistence.
- 🕓 **Configure the timezone** and other **environment variables**.
- 🌐 Create and activate a **Python virtual environment**.
- 📦 Install all required Python and Terraform **dependencies**.
- 🧱 Keep the container **running continuously** and ready for use.

### Option A - Unix-Based Operating Systems (or Unix-Compatible Subsystems)

On Unix-based systems or environments with Unix compatibility, you can take advantage of the automation artifacts provided in this repository to streamline the deployment process.

First, jump to the [`/setup/docker_setup/`](/setup/docker_setup/) subidrectory within your local clone of this repository:

```bash
$ cd <YOUR_LOCAL_REPO_FOLDER>/setup/docker_setup/
```

Once there, you can bring up the container by simply executing the [`docker_apaf.sh`](docker_apaf.sh) shell script passing the [`docker_compose_apaf.yaml`](docker_compose_apaf.yaml) file as an input argument:

```bash
$ bash docker_apaf.sh docker_compose_apaf.yaml

2025-04-16 14:43:12 No running container found. Starting with a fresh build...
Compose can now delegate builds to bake for better performance.
 To do so, set COMPOSE_BAKE=true.
[+] Building 15.6s (14/14) FINISHED                                                                                                                                                                                                                        docker:desktop-linux
 => [apaf internal] load build definition from dockerfile                                                                                                                                                                                                                  0.0s
 => => transferring dockerfile: 2.81kB                                                                                                                                                                                                                                     0.0s
 => [apaf internal] load metadata for docker.io/library/python:3.12.9-alpine3.21                                                                                                                                                                                           2.1s
 => [apaf auth] library/python:pull token for registry-1.docker.io                                                                                                                                                                                                         0.0s
 => [apaf internal] load .dockerignore                                                                                                                                                                                                                                     0.0s
 => => transferring context: 2B                                                                                                                                                                                                                                            0.0s
 => [apaf 1/7] FROM docker.io/library/python:3.12.9-alpine3.21@sha256:28b8a72c4e0704dd2048b79830e692e94ac2d43d30c914d54def6abf74448a4e                                                                                                                                     0.9s
 => => resolve docker.io/library/python:3.12.9-alpine3.21@sha256:28b8a72c4e0704dd2048b79830e692e94ac2d43d30c914d54def6abf74448a4e                                                                                                                                          0.0s
 => => sha256:89322d3ac64bf8a79585df322d2034d9f6dff9108bf3134f1430ae711700f749 247B / 247B                                                                                                                                                                                 0.1s
 => => sha256:bd9f743c4b2d27fb5cf8ff2cbd18a1e506e86a4b444e1a28e42b5fb63964c87f 13.70MB / 13.70MB                                                                                                                                                                           0.6s
 => => sha256:b60a29b5b2911d5b8ee9dcdb5f3a38f98e46d2b43ff40db6f826f5497a01cab4 460.73kB / 460.73kB                                                                                                                                                                         0.6s
 => => sha256:6e771e15690e2fabf2332d3a3b744495411d6e0b00b2aea64419b58b0066cf81 3.99MB / 3.99MB                                                                                                                                                                             0.7s
 => => extracting sha256:6e771e15690e2fabf2332d3a3b744495411d6e0b00b2aea64419b58b0066cf81                                                                                                                                                                                  0.0s
 => => extracting sha256:b60a29b5b2911d5b8ee9dcdb5f3a38f98e46d2b43ff40db6f826f5497a01cab4                                                                                                                                                                                  0.0s
 => => extracting sha256:bd9f743c4b2d27fb5cf8ff2cbd18a1e506e86a4b444e1a28e42b5fb63964c87f                                                                                                                                                                                  0.1s
 => => extracting sha256:89322d3ac64bf8a79585df322d2034d9f6dff9108bf3134f1430ae711700f749                                                                                                                                                                                  0.0s
 => [apaf internal] load build context                                                                                                                                                                                                                                     0.0s
 => => transferring context: 9.31kB                                                                                                                                                                                                                                        0.0s
 => [apaf 2/7] RUN apk add --no-cache curl=8.12.1-r1                                                                                                                                                                                                                       0.8s
 => [apaf 3/7] WORKDIR /apaf                                                                                                                                                                                                                                               0.0s
 => [apaf 4/7] RUN echo "Copying necessary files into the container"                                                                                                                                                                                                       0.1s
 => [apaf 5/7] COPY requirements.yaml docker_install_requirements.j2 docker_install_requirements.py docker_install_terraform.py .                                                                                                                                          0.0s
 => [apaf 6/7] RUN echo "Installing Python packages with pip"     && pip install --upgrade pip==25.0.1         pyyaml==6.0.2         jinja2==3.1.5      && python3 /apaf/docker_install_requirements.py                                                                    8.0s
 => [apaf 7/7] RUN echo "Installing Terraform using the dedicated Python script"     && python3 /apaf/docker_install_terraform.py                                                                                                                                          1.4s
 => [apaf] exporting to image                                                                                                                                                                                                                                              2.1s
 => => exporting layers                                                                                                                                                                                                                                                    1.7s
 => => exporting manifest sha256:645dbf054e2cc7d6863791049ca9bc3a762db22597d5e323b4fbe3416d493bfe                                                                                                                                                                          0.0s
 => => exporting config sha256:83a8e67eecc48f17a7772c9465a45727999e429fe36b088914b3c4d63c9e0766                                                                                                                                                                            0.0s
 => => exporting attestation manifest sha256:a8d822ce972133c950cd6304c1c5e92871e3a9fc5407de51f6e05b528bb7ecca                                                                                                                                                              0.0s
 => => exporting manifest list sha256:a56f3f27c2ab3a019f154734055312bead7269519a8b6ab43d41f0c92837309b                                                                                                                                                                     0.0s
 => => naming to docker.io/library/docker_apaf:latest                                                                                                                                                                                                                      0.0s
 => => unpacking to docker.io/library/docker_apaf:latest                                                                                                                                                                                                                   0.4s
 => [apaf] resolving provenance for metadata file                                                                                                                                                                                                                          0.0s
[+] Running 3/3
 ✔ apaf                          Built                                                                                                                                                                                                                                     0.0s
 ✔ Network docker_setup_default  Created                                                                                                                                                                                                                                   0.0s
 ✔ Container docker_apaf         Started                                                                                                                                                                                                                                   0.2s


2025-04-16 14:43:29 Containers running:
CONTAINER ID   IMAGE         COMMAND               CREATED        STATUS                  PORTS     NAMES
c5f4f9248acb   docker_apaf   "tail -f /dev/null"   1 second ago   Up Less than a second             docker_apaf
```

### Option B - Non-Unix-Based Operating Systems

If your machine runs a non-Unix-based operating system (e.g., Windows), start up the container by deploying the [`docker_compose_apaf.yaml`](docker_compose_apaf.yaml) file following the [official Docker Compose instructions](https://docs.docker.com/compose/gettingstarted/) for your platform.

## 🧪 Step 4 - Container verifications

Perform the next verifications to guarantee that the Docker container is ready to run the Framework with all the necesessary requiremenets.

### Verify Interactive Shell Access
Confirm that you can access the container and interact with it using an interactive shell. This ensures you can manage and troubleshoot the container directly.

```bash
$ docker exec -it docker_apaf sh
```

If the container is set up correctly, you should enter an interactive shell session, and you'll see the command prompt change to something like:

```bash
/apaf/tools/python #
```

This confirms that the shell is working as expected, and you can begin interacting with the container.

### Check Mounted Directories
Ensure that the necessary volumes are mounted correctly, particularly the Git cloned code and data directories:

```bash
$ docker inspect docker_apaf | grep Mounts -A 9
        "Mounts": [
            {
                "Type": "bind",
                "Source": "<YOUR_LOCAL_REPO_FOLDER>/apstra-provisioning-automation-framework",
                "Destination": "/apaf",
                "Mode": "rw",
                "RW": true,
                "Propagation": "rprivate"
            }
        ],
```
Verify that you can see them mounted when accessing the container:

```bash
$ docker exec -it docker_apaf pwd
/apaf/tools/python

$ docker exec -it docker_apaf ls -altr
total 360
-rw-r--r--    1 root     root          1840 Apr  1 11:35 main.py
-rw-r--r--    1 root     root          7950 Apr  1 11:35 apstra_update_external_links.py
-rwxr-xr-x    1 root     root          3239 Apr  1 11:35 apstra_pull_device_models.py
-rw-r--r--    1 root     root          2715 Apr  1 11:35 apstra_pull_cabling_maps.py
-rw-r--r--    1 root     root          3056 Apr  1 11:35 apstra_delete_placeholder_racks.py
-rw-r--r--    1 root     root          3641 Apr  1 11:35 apstra_create_ct_with_bindings.py
-rw-r--r--    1 root     root         13303 Apr  2 17:10 apstra_update_cabling_maps.py
-rw-r--r--    1 root     root          3687 Apr  2 17:20 apstra_push_cabling_maps.py
drwxr-xr-x    4 root     root           128 Apr  2 17:20 ..
drwxr-xr-x   12 root     root           384 Apr  7 16:24 .
-rw-r--r--    1 root     root        319265 Apr  7 18:34 utils.py
drwxr-xr-x    4 root     root           128 Apr  8 09:18 __pycache__
```

### Verify Installed Python libraries
Check that the required Python libraries (``pyyaml``, ``jinja2``, and the ones set in [`requirements.yaml`](requirements.yaml) and other dependencies are installed within the container.

```bash
$ docker exec -it docker_apaf pip list
Package            Version
------------------ ---------
apstra-api-python  0.2.1
certifi            2025.1.31
charset-normalizer 3.4.1
deepdiff           8.2.0
idna               3.10
Jinja2             3.1.5
markdown-it-py     3.0.0
MarkupSafe         3.0.2
mdurl              0.1.2
orderly-set        5.3.0
pip                25.0.1
Pygments           2.19.1
PyYAML             6.0.2
requests           2.32.3
rich               13.9.4
urllib3            2.3.0
```
### Verify Terraform Version

Check that the expected Terraform version has been installed: 

```bash
$ docker exec -it docker_apaf terraform version
Terraform v1.9.8
```

### Verify Internet Connectivity to the Apstra Registry

Check the Internet reachability from the container to the [Apstra Terraform Registry](https://registry.terraform.io/providers/Juniper/apstra/latest/docs), as this will be necessary to download the required provider plugins and modules for the specified version. 

```bash
$ docker exec -it docker_apaf curl -s -f -I https://registry.terraform.io/providers/Juniper/apstra/latest
HTTP/2 200
...
```

### Check if the Framework is Executable

Ensure that you can run the framework on the container by executing: 

```bash
docker exec -it docker_apaf python3 main.py command=a
```

The main menu should appar, prompting the user to select a numeric option:

```
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

Press 9 to abort the execution.

# Final Notes

In summary:

- ✅ **Steps 1 and 2** are only needed **once per machine**.
- 🔄 **Steps 3 and 4** are only needed **after a reboot or if the container is stopped**.

With this setup, running the Docker container becomes as simple as typing a single command. Enjoy the speed, isolation, and reproducibility of Docker! 🐳✨