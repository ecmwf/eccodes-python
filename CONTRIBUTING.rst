
.. highlight: console

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Please note, that we have hooked a CLA assistant to this GitHub Repo. Please accept the contributors license agreement to allow us to keep a legal track of contributions and keep this package open source for the future.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/ecmwf/eccodes-python/issues

If you are reporting a bug, please include:

* Your operating system name and version.
* Installation method and version of all dependencies.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug, including a sample file.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whoever wants to implement a fix for it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Get Started!
------------

Ready to contribute? Here's how to set up `eccodes-python` for local development. Please note this documentation assumes
you already have `virtualenv` and `Git` installed and ready to go.

1. Fork the `eccodes-python` repo on GitHub.
2. Clone your fork locally::

    $ cd path_for_the_repo
    $ git clone https://github.com/YOUR_NAME/eccodes-python.git
    $ cd eccodes-python

3. Assuming you have virtualenv installed (If you have Python3.5 this should already be there), you can create a new environment for your local development by typing::

    $ virtualenv ../eccodes-python-env
    $ source ../eccodes-python-env/bin/activate

    This should change the shell to look something like
    (eccodes-python-env) $

4. Install system dependencies as described in the README.rst file then install a known-good set of python dependencies and the your local copy with::

    $ pip install -r ci/requirements-tests.txt
    $ pip install -e .

5. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

6. The next step would be to run the test cases. `eccodes-python` uses py.test, you can run PyTest. Before you run pytest you should ensure all dependencies are installed::

    $ pip install -r ci/requirements-dev.txt
    $ pytest -v --flakes

7. Before raising a pull request you should also run tox. This will run the tests across different versions of Python::

    $ tox

8. If your contribution is a bug fix or new feature, you should add a test to the existing test suite.

9. Format your Python code with the Black auto-formatter, to ensure the code is uses the library's style. We use the default Black configuration (88 lines per character and `"` instead of `'` for string encapsulation)::

    $ black .

10. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

11. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.

2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.

3. The pull request should work for Python 3.8, 3.9, 3.10, 3.11 and for PyPy2 and PyPy3.
   Check the tox results and make sure that the tests pass for all supported Python versions.


Testing CDS data
----------------

You can test the CF-GRIB driver on a set of products downloaded from the Climate Data Store
of the `Copernicus Climate Change Service <https://climate.copernicus.eu>`_.
If you are not register to the CDS portal register at:

    https://cds.climate.copernicus.eu/user/register

In order to automatically download and test the GRIB files install and configure the `cdsapi` package::

    $ pip install cdsapi
    $ pip install netcdf4

The log into the CDS portal and setup the CDS API key as described in:

    https://cds.climate.copernicus.eu/api-how-to

Then you can run::

    $ pytest -vv tests/cds_test_*.py


.. eccodes-python: https://github.com/ecmwf/eccodes-python
.. virtualenv: https://virtualenv.pypa.io/en/stable/installation
.. git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
