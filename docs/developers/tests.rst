Testing
=======

Quest has an expanding test suite the testing framework from `pytest <http://doc.pytest.org/en/latest/contents.html>`_.

Running Tests
-------------

To run the tests you will need to install the pytest Python package after activating your environment::

    (quest) $ conda install pytest

Once pytest is installed in your environment you can execute the tests from the command line with the following command (assuming your working directory is the quest source code directory)::

    (quest) $ pytest test

The first time the tests are run quest will build a complete cache of all of the feature metadata for each service. This can take 5 or 6 minutes. This is only done the first time the tests are run (or when a flag is passed to update the cache). The tests will run much faster after the first time.

The tests are configured to run through both a Python interpreter and through an RPC server. This lengthens the time it takes to run the tests, but provides more coverage. If you are interested in only running one set of test or the other, this can be achived by passing in `Custom Test Options`_.

Custom Test Options
-------------------

Several custom options have been configured to allow several subsets of the tests to be run.

    * `--skip-slow`: Any tests that have been marked as slow (e.g. the `get_features` tests) will not be run.
    * `--update-cache`: Triggers the feature metadata for each service to be re-downloaded (this process takes 5 or 6 minutes).

For example, to run most of the tests very quickly you can run::

    (quest) $ pytest test --skip-slow

This will will give you the most bang for you buck, running the majority of the tests in just several seconds.

To get the most coverage you should run::

    (quest) $ pytest test --update-cache

This will test all of the services by regenerating the cache and will run the complete set of tests. This process can take around 10 minutes.


Adding Tests
------------

The Quest testing framework makes extensive use of `pytest fixtures <http://doc.pytest.org/en/latest/proposals/parametrize_with_fixtures.html?highlight=fixtures>`_. Fixtures provide a very flexible and powerful way to provide the correct baseline configuration for each test, and for running the same test with multiple configurations. The heart of the testing configuration is determined by the fixtures defined in `conftest.py`.

.. todo::

    Add more explanation of how the testing framework is set up and how/where tests should be added.