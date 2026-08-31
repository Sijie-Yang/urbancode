uc --version
============

Question
--------

Which UrbanCode version is installed?

Expected output
---------------

.. figure:: /_static/recipes/cli/version.png
   :alt: Terminal-style preview of uc --version
   :width: 100%

   ``uc --version`` prints ``urbancode <version>`` and exits.

Installation
------------

``pip install urbancode`` (core wheel).

Minimal command
---------------

::

   uc --version

::

   urbancode 0.3.0

The command prints the installed package version and exits without
loading GIS or model backends.

Related pages
-------------

* CLI: :doc:`/reference/cli`
* Script: ``examples/recipes/cli/version.py``
