# Table of Contents
- [Day-1 Operations: Deploy Your First Apstra Blueprints](#day-1-operations-deploy-your-first-apstra-blueprints)
- [Day-2 Operations: Modify Your Initial Deployments](#day-2-operations-modify-your-initial-deployments)

## Day-1 Operations: Deploy Your First Apstra Blueprints

If you want to experience the framework firsthand, this repository includes two demo setups for testing purposes, located in the [``/data/customers/DEMO``](./data/customers/DEMO) directory.

Both domains can be deployed on the same Apstra infrastructure, as they create distinct objects with unique names to prevent conflicts and ensure their independence.

### [**Single Terraform Project to deploy two Datacenters**](./data/customers/DEMO/domains/SINGLE_PROJECT)
  
  The **SINGLE_PROJECT** domain, as its name suggests, consists of just one project named **ALL-IN-ONE** that deploys two complete Datacenters (known as Blueprints in Apstra) named **SINGLE-DC1** and **SINGLE-DC2**.
  
  It includes all the required Apstra artifacts, both global (objects under the Design and Resources Apstra menus) and blueprint-specific (such as devices, routing policies, VRFs, virtual networks, and connectivity templates).
  
  By deploying this project with the default parameters in the input YAML files, you’ll get a hands-on experience of the framework's power. What would normally be a time-consuming task through Apstra's GUI, can be achieved with just one simple execution of the framework.

### [**Multilevel Hierarchical Terraform Projects to deploy two Datacenters**](./data/customers/DEMO/domains/MULTI_PROJECT)
    
  The **MULTI_PROJECT** domain, as its name suggests, consists of several projects that deploys two complete Datacenters, **MULTI-DC1** and **MULTI-DC2**, very similar to those deployed in the **SINGLE_PROJECT** domain.
    
  The reason of being of this domain is to showcase the power of micro-segmenting the entire Apstra Deployment into smaller, interconnected projects organized in a logical hierarchy. 
    
  While it might seem more tedious at first —deploying five projects instead of one for a very similar outcome —this approach offers several advantages, including risk isolation, improved execution times, and scalability. Additionally, the modular nature of this setup enhances maintainability and flexibility in large-scale environments.

  The logical order for deploying (and, conversely, destroying) the projects in this domain is:
  
  1. Deploy the [**`L1_GLOBAL`**](./data/customers/DEMO/domains/MULTI_PROJECT/projects/L1_GLOBAL) project.
  2. Deploy the [**`L2_INFRA_DC1`**](./data/customers/DEMO/domains/MULTI_PROJECT/projects/L2_INFRA_DC1) and [**`L2_INFRA_DC2`**](./data/customers/DEMO/domains/MULTI_PROJECT/projects/L2_INFRA_DC2) projects.
  3. Deploy the [**`L3_TENANT_DC1`**](./data/customers/DEMO/domains/MULTI_PROJECT/projects/L3_TENANT_DC1) and [**`L3_TENANT_DC2`**](./data/customers/DEMO/domains/MULTI_PROJECT/projects/L3_TENANT_DC2) projects.

## Day-2 Operations: Modify Your Initial Deployments

After deploying one or both of the proposed domains, you can proceed with modifying the input YAML files to create, update, or remove resources within Apstra — common tasks typically performed during daily operations in real-world deployments.

Below is a collection of quick exercises you can work through using any of the demo domains:

| **Exercise** | **Steps** |
| --------------- | --------- |
| **Exercise #1** | - Create the Server **Serv04** dual-homed to both leaves in Rack **RACK02**. |
| **Exercise #2** | - Change the VLAN ID of Virtual Network **VN01** from **211** to **261**. |
| **Exercise #3** | - Add Virtual Network **VN03**. <br> - Replace Virtual Network **VN02** with Virtual Network **VN03** in Connectivity Template **CT-MASTER-BOND0**. <br> - Add Virtual Network **VN03** to Connectivity Template **CT-MASTER-BOND1**. |
| **Exercise #4** | - Remove Virtual Network **VN02** from Connectivity Template **CT-MASTER-BOND1**. |
| **Exercise #5** | - Delete Virtual Network **VN02**. |
| **Exercise #6** | - Modify external link IPs in Connectivity Template **IxC-EXT-RTR-SERV02**. |
