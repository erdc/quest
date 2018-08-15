# Environmental Simulator Quest

| Gitter | Linux/Mac | Windows | Test Coverage |
| --------- | --------- | --------- | ------------- |
| [![Join the chat at https://gitter.im/Quest-Development/Quest](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Quest-Development/Quest) | [![Build Status](https://travis-ci.org/erdc/quest.svg?branch=master)](https://travis-ci.org/erdc/quest) | [![Build Status](https://ci.appveyor.com/api/projects/status/e20arxcfrcmb2ylm/branch/master?svg=true)](https://ci.appveyor.com/project/dharhas/quest) | [![Coverage Status](https://coveralls.io/repos/github/erdc/quest/badge.svg)](https://coveralls.io/github/erdc/quest) |

### Project Description
Quest is a python library that provides an API the ability to search, publish and download data (both geographical and non-geographical) across multiple data sources including both local repositories and web based services. The library also allows provides tools in order to manipulate and manage the data that the user is working with. 

### Project Links
- Here is a live link for the Quest Documentation: https://quest.readthedocs.io/en/latest/

## Setup Dev Environment

- Install miniconda
- Install conda-env

    conda install conda-env

- Clone master branch
- Create a new conda environment for development

    conda env create -n quest -f py3_conda_requirements.yml

    (you can also create a python 2 env but 3 is preferred)

- Install quest in develop mode

    python setup.py develop

## Development Workflow

- change to master branch

    git checkout master

- get the latest version of master

    git pull master

- create a new branch locally

    git checkout -b mybranch

- Develop the new features on your local machine, add tests for any new features
- push the local branch to gitlab and set up tracking, later `git push` is all that is required.

    git push -u origin mybranch

- run tests on python 2 and python 3 using py.test
- Once you have finished developing your branch, check if master has changed

    git checkout master

    git pull

- If `git pull` pulls in new changes from master then you need to rebase

    git checkout mybranch

    git rebase master

    (follow the prompts, you may have to fix conflicts)

- after a rebase you may have to force push to gitlab on your branch

    git push -f

- Run tests again.
- If everything looks good, use Gitlab to do a merge request from your branch to master
- Once the merge has been accepted, do not continuing working in that branch. make a new branch starting at step 1


