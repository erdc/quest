Installation Instructions
=========================

These instructions will walk you through installing Quest either from the released package or from the source code.

Install Released Conda Package
------------------------------

1. Install `Miniconda <http://conda.io/miniconda.html>`_ [or `Anaconda <http://continuum.io/downloads>`_ although Miniconda is preferred] for your OS

2. Install Quest from the ERDC Environmental Simulator conda channel using one of the following methods:

    a. Install Quest into new environment::

        conda create -n quest -c conda-forge -c erdc quest

    b. Install Quest into existing environment::

        conda install -c erdc -c conda-forge quest

    .. note::

        Becuase of incompatibilities with the dependencies between conda-forge and the defaults channel, the environment must have been created with conda-forge.

3.  Refer to :doc:`quickstart` for more help getting started with Quest.

Install from Source
-------------------

1. Clone the repository::

    git clone https://github.com/erdc/quest.git

2. Install the dependencies using conda or pip (conda is recommended):

Conda Install
~~~~~~~~~~~~~

    a. Install `Miniconda <http://conda.io/miniconda.html>`_ [or `Anaconda <http://continuum.io/downloads>`_ although Miniconda is preferred] for your OS.

    b. Create new environment with dependenciest::

            conda env create -n quest --file py3_conda_environment.yml
            source activate quest  # (use 'activate quest' on windows)

    c. Install Quest in develop mode::

            python setup.py develop

    Optional
    ........

    d. Run tests::

        python setup.py test


Pip Installation
~~~~~~~~~~~~~~~~~~~~

    .. warning::

        Some of the Python dependencies (e.g. gdal and numpy) have system dependencies that must be installed before they can be installed from pip.

    a. Install pip requirements. From the base directory type::

        pip install -r pip_requirements.txt

    b. Install Quest in develop mode::

        python setup.py develop

    .. note::

        `python setup.py install` and `python setup.py develop` have issues installing numpy correctly on osx.