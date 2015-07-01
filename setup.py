import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

from config import services, filters, io


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)
# this sets __version__
info = {}
execfile(os.path.join('dsl', 'version.py'), info)


with open('README.rst') as f:
    # use README for long description but don't include the link to travis-ci;
    # it seems a bit out of place on pypi since it applies to the development
    # version
    long_description = ''.join([
        line for line in f.readlines()
        if 'travis-ci' not in line])


# create plugin entrypoint strings
services = [' = '.join([k,v]) for k,v in services.iteritems()]
filters = [' = '.join([k,v]) for k,v in filters.iteritems()]
io = [' = '.join([k,v]) for k,v in io.iteritems()]

setup(
    name='dsl',
    version=info['__version__'],
    license='',
    author='Dharhas Pothina',
    author_email='dharhas.pothina@erdc.dren.mil',
    description='Environmental Simulator, Data Services, Interpolation, Web Services',
    long_description=long_description,
    url='',
    keywords='',
    packages=find_packages(),
    package_data={'dsl.smtk': ['*.sbt']},
    platforms='any',
    install_requires=[
        'numpy',
        'fiona>=1.5.1',
        'rasterio>=0.23.0',
        'geojson',
        'jsonschema',
        'stevedore',
        'ulmo>=0.7.6',
        'pyyaml',
        'pyoos',
        'click',
        'matplotlib>=1.4.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: :: ',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],

    include_package_data=True,

    entry_points={
        'console_scripts': ['dsl-get-elevations=dsl.scripts.get_elevations:cli'],
        'dsl.services': services,
        'dsl.filters': filters,
        'dsl.io': io,
    },

    zip_safe=False,

    tests_require=[
        'pytest>=2.3.2',
    ],
    cmdclass={'test': PyTest},
)
