Installation Instructions
=========================

These instructions will walk you through installing Quest either from the released package or from the source code.

Install Released Conda Package
------------------------------

1. Install `Miniconda <http://conda.io/miniconda.html>`_ [or `Anaconda <http://continuum.io/downloads>`_ although Miniconda is preferred] for your OS

2. Install Quest from the ERDC Environmental Simulator conda channel using one of the following methods:

    a. Install Quest into new environment::

        conda config --set ssl_verify false
        conda create -n quest -c conda-forge -c https://quest.erdc.dren.mil/Software/es-conda-channel/ terrapin quest
        conda config --set ssl_verify true

    .. note::

        Because of the DoD certificates on the es-conda-channel server conda's SSL verification must be turned off to install packages from this channel.


    b. Install Quest into existing environment::

        conda config --set ssl_verify false
        conda install -c conda-forge -c https://quest.erdc.dren.mil/Software/es-conda-channel/ terrapin quest
        conda config --set ssl_verify true

    .. note::

        Becuase of incompatibilities with the dependencies between conda-forge and the defaults channel, the environment must have been created with conda-forge.

3.  Refer to :doc:`quickstart` for more help getting started with Quest.

Install from Source
-------------------

1. Clone the repository::

    git clone git@public.git.erdc.dren.mil:computational-analysis-and-mechanics/quest.git

2. Install the dependencies using conda or pip (conda is recommended):

Conda Install
~~~~~~~~~~~~~

    a. Install `Miniconda <http://conda.io/miniconda.html>`_ [or `Anaconda <http://continuum.io/downloads>`_ although Miniconda is preferred] for your OS.

    b. Create new environment with dependenciest::

            conda env create -n quest --file py3_conda_environment.yml
            # (use py2_conda_environment.yml if you want a Python 2 based install)
            source activate quest  # (use 'activate quest' on windows)

    c. Install Quest in develop mode::

            python setup.py develop

    Optional
    ........
    d. Some filters (e.g. watershed delineation) require the package `terrapin` that is available through the es-conda-channel::

        conda config --set ssl_verify false
        conda install -y -c https://quest.erdc.dren.mil/Software/es-conda-channel/ terrapin
        conda config --set ssl_verify true

    e. Run tests::

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