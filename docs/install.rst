Installation Instructions
=========================

These instructions will walk you through installing Quest either from the released package or from the source code.

Install Released Conda Package
------------------------------

1. Install `Miniconda <http://conda.io/miniconda.html>`_ [or `Anaconda <http://continuum.io/downloads>`_ although Miniconda is preferred] for your OS

2. Install Quest from the ERDC Environmental Simulator conda channel using one of the following methods:

    a. Install Quest into new environment::

        conda create -n quest -c conda-forge quest

    b. Install Quest into existing environment::

        conda install -c conda-forge quest

    .. note::

        Because of incompatibilities with the dependencies between conda-forge and the defaults channel, the environment must have been created with conda-forge.

3.  Refer to :doc:`quickstart` for more help getting started with Quest.

Install from Source
-------------------

1. Clone the repository::

    git clone https://github.com/erdc/quest.git

2. Install the dependencies using conda:

    a. Install `Miniconda <http://conda.io/miniconda.html>`_ [or `Anaconda <http://continuum.io/downloads>`_ although Miniconda is preferred] for your OS.

    b. Create new environment with dependenciest::

            conda env create -n quest --file conda_environment.yml
            conda activate quest

    c. Install Quest in develop mode::

            python setup.py develop

Optional
........

    d. Run tests::

        pytest
