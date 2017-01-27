Installation Instructions
-------------------------

Conda Install
~~~~~~~~~~~~~

*This is the recommended install method*

Install Anaconda (http://continuum.io/downloads) or Miniconda (http://conda.io/) for your OS


conda env create -n quest --file py2_conda_environment.yml (use py3_conda_environment.yml if you want a Python 3 based install)
source activate myenv (use 'activate myenv' on windows)
python setup.py develop

optionally run tests:
    python setup.py test


Regular Installation
~~~~~~~~~~~~~~~~~~~~

from the base directory type:

`pip install -r requirements.txt`

This will download to correct feature/raster branch of ulmo and install all quest 
dependencies into your python path.

Note: `python setup.py install` and `python setup.py develop` have issues installing 
numpy correctly on osx.