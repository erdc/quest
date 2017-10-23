Installation Instructions
=========================

These instructions will walk you through installing Quest either from the released package or from the source code.

Install Released Conda Package
------------------------------

1. Install Miniconda (http://conda.io/) [or Anaconda (http://continuum.io/downloads) although Miniconda is preferred] for your OS

2. Create a new environment and install Quest from the ERDC Environmental Simulator conda channel::

    conda config --set ssl_verify false
    conda create -n quest -c conda-forge -c https://quest.erdc.dren.mil/Software/es-conda-channel/ terrapin quest
    conda config --set ssl_verify true

.. note::

    Because of the DoD certificates on the es-conda-channel server conda's SSL verification must be turned off to install packages from this channel.

3.  Refer to :doc:`quickstart` for more help getting started with Quest.

Install from Source
-------------------

1. Clone the repository::

    git clone git@public.git.erdc.dren.mil:computational-analysis-and-mechanics/quest.git

Conda Install
~~~~~~~~~~~~~

*This is the recommended install method*

Install Anaconda (http://continuum.io/downloads) or Miniconda (http://conda.io/) for your OS

::

    conda env create -n quest --file py3_conda_environment.yml
    # (use py2_conda_environment.yml if you want a Python 2 based install)
    source activate quest  # (use 'activate quest' on windows)
    python setup.py develop

Optional
........
Some filters (e.g. watershed delineation) require the package `terrapin` that is available (Python 3 only) through the es-conda-channel::

    conda config --set ssl_verify false
    conda install -y -c https://quest.erdc.dren.mil/Software/es-conda-channel/ terrapin
    conda config --set ssl_verify true

Run tests::

    python setup.py test


Pip Installation
~~~~~~~~~~~~~~~~~~~~

.. warning::

    Some of the Python dependencies (e.g. gdal) have system dependencies that must be installed before they can be installed from pip.

from the base directory type::

    pip install -r requirements.txt
    python setup.py develop

This will download to correct feature/raster branch of ulmo and install all quest 
dependencies into your python path.

Note: `python setup.py install` and `python setup.py develop` have issues installing 
numpy correctly on osx.