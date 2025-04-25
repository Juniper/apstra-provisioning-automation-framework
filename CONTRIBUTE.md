# Table of Contents
- [Why Contribute?](#why-contribute)
- [Stage 1: Setting Up Your GitHub Account](#stage-1-setting-up-your-github-account)
- [Stage 2: Forking, Cloning and Branching](#stage-2-forking-cloning-and-branching)
- [Stage 3: Adding, Committing and Pushing](#stage-3-adding-committing-and-pushing)
- [Stage 4: Submitting Your Contribution](#stage-4-submitting-your-contribution)

# Why Contribute?

It seems that solving the same problems in many different ways is a common practice. While most solutions are valid and some are even brilliant, this often results in a lot of duplicated effort. Instead of starting from scratch, why not build on existing solutions and enhance them with new features? It’s a more efficient and smarter way to drive progress.

This framework was designed from its foundation with a global perspective and with the aim to be useful across various environments and projects, benefiting the wider community. However, it is still a work in progress and there’s plenty of room for enhancement, optimization and new functionalities. Hopefully together, we can polish it and take it to the next level.

If you believe you can improve the framework by developing a new feature/functionality, or even if it is a simple code optimization, please contribute it back to the community. This generous act of altruism will allow the next generation of users to benefit from your work, just like you benefitted from the work done by your forebears. 

This document explains the general process that you should follow when contributing your work.

# Stage 1: Setting Up Your GitHub Account

This first stage needs only to be done once, and should only take several minutes. Once you have followed the steps in this stage, you can move onto the second stage and skip this first stage altogether in the future.

## Create a GitHub.com Account

This sounds obvious, but if you want to contribute code to GitHub.com you will need to create an account first. What might not be so obvious is that if you only want to clone a repo from GitHub.com then you don't need an account. 😊

You can use your personal email address as your primary email address when you register and GitHub.com will use this to send you account-related notifications. But you may also benefit from adding a business email address too. Quite often, a project hosted on GitHub.com by an organization such as Juniper will allow contributions from two sources, employees and non-employees. 

## Verify your Email Address

In order to strenghten your account's security and to gain access to all GitHub.com features, it is strongly recommended to verify your email address following [the instructions here](https://docs.github.com/en/get-started/signing-up-for-github/verifying-your-email-address).

# Stage 2: Forking, Cloning and Branching

## Fork from Upstream

OK, now the fun stuff 🎉! Go to the repository on GitHub.com you want to contribute to and click the "Fork" button. Most of the time you will only want to copy the ```master``` (aka ```main```) branch, so check that this option is set and then press the "Create Fork" button. This will create a copy of the upstream repository in your personal GitHub.com account.

## Clone Repo to a Development Environment

Most likely you are developing on a separate remote system, so you will need to get the code that you just forked sent from your GitHub.com account to the Git server on your development system. You do this by running the ```git clone``` command on your development system - see [the link here](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) for more details. 

## Create a Branch

On your development system you should create a branch (a separate copy of the repository) where you can add your code. A good practice is to simply call this branch "development". You can do this with the Git command ```git checkout -b development```

# Stage 3: Adding, Committing and Pushing

## Add Your Work

Now make your desired changes on the files into the development branch in order to add new features or any improvement to the original source code. Remember that you will need to run ```git add``` to add any new file that did not exist in the original repo.

## Commit Locally

Once you have added your changes, it is time to commit them (save them) to the local Git server on your development platform by using the ```git commit -m 'Message'``` command. Make sure you add a meaningful message describing your changes.

Repeat the add and commit steps until you are done, and have enough content that you want to push back up to your GitHub.com account.

## Push to Origin

The act of pushing will transfer the work that you have committed on your local development Git server to the central servers at GitHub.com. To achieve this, following our previous example, use the ```git push origin development``` command. The name ```origin``` is a reserved name that simply means the remote parent where the repository was cloned from (if you are working with Git on a remote development system, ```origin``` will typically be the parent repository under your GitHub.com account). 

# Stage 4: Submitting Your Contribution

## Create a Pull Request

When you are finally ready to contribute your work back into the upstream source, you will need to create a Pull Request from the repository branch on your GitHub.com account. This will notify the owners of the upstream repository of your changes. For more details about pull requests please read [this link ](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) and then follow the [steps here](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) to create the request.

## Thank you! 

The administrators of the upstream repository will review your pull request, and if your additions or changes are approved, they will merge your branch with the original upstream repository. Note that unsigned commits and pushes will take longer to be reviewed and might be rejected. Well done, and thank you for your contribution! 👏


