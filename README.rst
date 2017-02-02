Environmental Simulator Quest
-----------------------------

.. image:: https://public.git.erdc.dren.mil/ci/projects/7/status.png?ref=master
   :target: https://public.git.erdc.dren.mil/ci/projects/7?ref=master
   :alt: Build status of the master branch on gitlab-ci

Python API for Quest

See *.rst files in the docs folder for documentation

Development Workflow
--------------------

setup dev environment
+++++++++++++++++++++

- Install miniconda
- Install conda-env

    conda install conda-env

- Clone master branch
- Create a new conda environment for development

    conda env create -n quest -f py3-conda-requirements.yml

    (you can also create a python 2 env but 3 is preferred)

- Install quest in develop mode

    python setup.py develop

development workflow
++++++++++++++++++++

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

**Never work on the same branch as someone else, if you need to continue work**
**on a branch started by someone else, checkout that branch and make a new branch. i.e.:**

    git fetch

    git checkout bobs-branch

    git checkout -b my-bobs-branch

    etc

**naming branches** use descriptive names following the pattern 'type of branch/name'**

- add-dataset/noaa
- bugfix/user-services
- feature/caching-api

